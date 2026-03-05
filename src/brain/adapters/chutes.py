"""Chutes.ai LLM adapter — aiohttp streaming via Bearer token auth.

Uses the official Chutes.ai format:
    POST https://llm.chutes.ai/v1/chat/completions
    Authorization: Bearer <CHUTES_API_TOKEN>
    Content-Type: application/json
    stream: True  (SSE streaming, parsed line-by-line)

Model: MiniMaxAI/MiniMax-M2.5-TEE (default)

Features:
    - aiohttp (not openai client) — matches Chutes official SDK format
    - SSE streaming with line-by-line parsing ("data: {...}" / "data: [DONE]")
    - Retry with exponential backoff (max 3 attempts)
    - HTTP status-based error classification (429, 401, 5xx)
    - Token estimation from streamed text (word count * 1.3)
    - Mock mode support
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.chutes")

CHUTES_API_URL = "https://llm.chutes.ai/v1/chat/completions"

# Retry config
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0   # seconds
_RETRY_MAX_DELAY = 8.0    # seconds


def _classify_http_error(status: int, body: str = "") -> str:
    """Classify HTTP error by status code."""
    if status == 429:
        return "rate_limit"
    if status in (401, 403):
        return "auth_error"
    if status in (500, 502, 503, 504):
        return "server_error"
    return "unknown_error"


def _classify_error(exc: Exception) -> str:
    """Classify exception into error category."""
    msg = str(exc).lower()
    if "429" in msg or "rate limit" in msg or "ratelimit" in msg:
        return "rate_limit"
    if any(c in msg for c in ["401", "403", "authentication", "api key", "unauthorized"]):
        return "auth_error"
    if any(c in msg for c in ["500", "502", "503", "504", "server error", "overloaded"]):
        return "server_error"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "connection" in msg or "eof" in msg or "reset" in msg or "refused" in msg:
        return "connection_error"
    return "unknown_error"


class ChutesAdapter(BaseLLMAdapter):
    """Chutes.ai adapter using aiohttp + SSE streaming.

    Endpoint : https://llm.chutes.ai/v1/chat/completions
    Auth     : Authorization: Bearer <CHUTES_API_TOKEN>
    Streaming: Server-Sent Events — "data: {...}\\n" lines, ends with "data: [DONE]"

    Default model: MiniMaxAI/MiniMax-M2.5-TEE
    Great for: selling scripts, product QA, creative content.
    """

    # Pricing: Chutes.ai — pay-per-use
    INPUT_COST_PER_TOKEN = 0.5 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 1.5 / 1_000_000

    def __init__(
        self,
        model: str = "MiniMaxAI/MiniMax-M2.5-TEE",
        max_tokens: int = 1024,
        timeout_ms: int = 30000,
        api_key: str = "",
        api_url: str = "",
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        super().__init__("chutes", model, max_tokens, timeout_ms)
        self._api_key = api_key
        self._api_url = api_url or CHUTES_API_URL
        self._max_retries = max_retries

    def _get_api_key(self) -> str:
        key = self._api_key or os.getenv("CHUTES_API_TOKEN", "") or os.getenv("CHUTES_API_KEY", "")
        if not key:
            raise RuntimeError(
                "CHUTES_API_TOKEN not set. Add it to .env: CHUTES_API_TOKEN=your_token"
            )
        return key

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._get_api_key()}",
            "Content-Type": "application/json",
        }

    def _build_body(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "max_tokens": self.max_tokens,
            "temperature": 0.7,
        }

    async def _stream_request(
        self,
        system_prompt: str,
        user_prompt: str,
        trace_id: str,
    ) -> tuple[str, int, int]:
        """Send streaming request and collect full response text.

        Returns:
            (full_text, input_tokens_estimate, output_tokens_estimate)

        Raises:
            aiohttp.ClientResponseError: on HTTP 4xx/5xx
            asyncio.TimeoutError: on timeout
            RuntimeError: on missing API key
        """
        import aiohttp

        headers = self._build_headers()
        body = self._build_body(system_prompt, user_prompt)
        timeout = aiohttp.ClientTimeout(total=self.timeout_ms / 1000.0)

        collected_chunks: list[str] = []

        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                self._api_url,
                headers=headers,
                json=body,
            ) as response:
                # Raise immediately on HTTP error (4xx / 5xx)
                if response.status >= 400:
                    body_text = await response.text()
                    err_cat = _classify_http_error(response.status, body_text)
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=f"[{err_cat}] HTTP {response.status}: {body_text[:200]}",
                    )

                # Parse SSE stream line-by-line
                async for raw_line in response.content:
                    line = raw_line.decode("utf-8").strip()

                    if not line.startswith("data: "):
                        continue

                    data = line[6:]  # strip "data: " prefix

                    if data == "[DONE]":
                        break

                    try:
                        chunk_json = json.loads(data)
                        delta = (
                            chunk_json
                            .get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if delta:
                            collected_chunks.append(delta)
                    except (json.JSONDecodeError, IndexError, KeyError) as parse_err:
                        # Skip malformed chunks — streaming may have partial lines
                        logger.debug(
                            "chutes_chunk_parse_skip",
                            error=str(parse_err),
                            raw=data[:80],
                            trace_id=trace_id,
                        )

        full_text = "".join(collected_chunks)

        # Estimate tokens (Chutes streaming doesn't always return usage)
        combined_prompt = f"{system_prompt} {user_prompt}"
        input_tokens = int(len(combined_prompt.split()) * 1.3)
        output_tokens = int(len(full_text.split()) * 1.3)

        return full_text, input_tokens, output_tokens

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.CHAT_REPLY,
        trace_id: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        if is_mock_mode():
            return self._mock_response(user_prompt, task_type, trace_id)

        if not user_prompt.strip():
            return LLMResponse(
                text="", provider=self.provider_name, model=self.model,
                task_type=task_type, success=False,
                error="Empty prompt", trace_id=trace_id,
            )

        start = time.time()
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(1, self._max_retries + 1):
            try:
                text, input_tokens, output_tokens = await self._stream_request(
                    system_prompt, user_prompt, trace_id
                )
                latency = (time.time() - start) * 1000

                if not text.strip():
                    raise ValueError("Empty streamed response from Chutes API")

                result = LLMResponse(
                    text=text,
                    provider=self.provider_name,
                    model=self.model,
                    task_type=task_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency,
                    cost_usd=self.estimate_cost(input_tokens, output_tokens),
                    trace_id=trace_id,
                    metadata={"attempt": attempt, "streaming": True},
                )
                self.record_usage(result)
                logger.info(
                    "chutes_generate",
                    latency_ms=round(latency, 1),
                    tokens=result.total_tokens,
                    model=self.model,
                    attempt=attempt,
                    trace_id=trace_id,
                )
                return result

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    "chutes_timeout",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    timeout_sec=self.timeout_ms / 1000.0,
                    trace_id=trace_id,
                )

            except Exception as e:
                last_error = e
                err_cat = _classify_error(e)

                # Auth errors → no point retrying
                if err_cat == "auth_error":
                    logger.error(
                        "chutes_auth_error",
                        error=str(e),
                        trace_id=trace_id,
                    )
                    break

                logger.warning(
                    "chutes_error",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    error_category=err_cat,
                    error=str(e),
                    trace_id=trace_id,
                )

            # Exponential backoff before next attempt
            if attempt < self._max_retries:
                delay = min(_RETRY_BASE_DELAY * (2 ** (attempt - 1)), _RETRY_MAX_DELAY)
                logger.info(
                    "chutes_retry_wait",
                    attempt=attempt,
                    next_attempt=attempt + 1,
                    wait_sec=round(delay, 2),
                    trace_id=trace_id,
                )
                await asyncio.sleep(delay)

        # All attempts failed
        latency = (time.time() - start) * 1000
        err_cat = _classify_error(last_error)
        logger.error(
            "chutes_all_attempts_failed",
            attempts=self._max_retries,
            error_category=err_cat,
            error=str(last_error),
            trace_id=trace_id,
        )
        result = LLMResponse(
            text="",
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            latency_ms=latency,
            success=False,
            error=f"[{err_cat}] {last_error}",
            trace_id=trace_id,
            metadata={"attempts": self._max_retries},
        )
        self.record_usage(result)
        return result

    async def health_check(self) -> bool:
        """Health check — verify API token is present and endpoint is reachable."""
        if is_mock_mode():
            return True
        try:
            import aiohttp

            # Verify token exists
            self._get_api_key()

            # Quick HEAD/GET to base domain to check connectivity
            timeout = aiohttp.ClientTimeout(total=5.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Send a minimal streaming request with 1 max_token as ping
                headers = self._build_headers()
                body = {
                    "model": self.model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream": True,
                    "max_tokens": 1,
                    "temperature": 0.0,
                }
                async with session.post(
                    self._api_url,
                    headers=headers,
                    json=body,
                ) as response:
                    # 200 or 401 both mean server is reachable
                    if response.status in (200, 401, 403):
                        ok = response.status == 200
                        if not ok:
                            logger.warning(
                                "chutes_health_auth_failed",
                                status=response.status,
                            )
                        return ok
                    logger.warning(
                        "chutes_health_unexpected_status",
                        status=response.status,
                    )
                    return False

        except asyncio.TimeoutError:
            logger.warning("chutes_health_timeout")
            return False
        except RuntimeError as e:
            # Missing API key
            logger.error("chutes_health_no_token", error=str(e))
            return False
        except Exception as e:
            err_cat = _classify_error(e)
            logger.warning("chutes_health_failed", error_category=err_cat, error=str(e))
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (
            (input_tokens * self.INPUT_COST_PER_TOKEN)
            + (output_tokens * self.OUTPUT_COST_PER_TOKEN)
        )

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-Chutes/{self.model}] Response to: {prompt[:50]}..."
        result = LLMResponse(
            text=mock_text,
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()),
            latency_ms=50.0,
            trace_id=trace_id,
            metadata={"streaming": True, "mock": True},
        )
        self.record_usage(result)
        return result
