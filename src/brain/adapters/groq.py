"""Groq LLM adapter — ultra-fast inference via OpenAI-compatible API.

Groq provides the fastest LLM inference (sub-100ms latency).
Uses OpenAI client with custom base_url: https://api.groq.com/openai/v1
Ideal for: chat replies, filler, quick emotion detection.

Fixes:
- Timeout raised from 500ms → 5000ms (realistic for first call / cold start)
- Retry with exponential backoff (max 3 attempts)
- Rate limit (429) → rotate to next API key before retrying
- Specific error classification (rate_limit / auth / server / timeout)
- Key rotation bug fixed: index is per-request, not global counter drift
- health_check now does actual API ping, not just client instantiation
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import get_env, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.groq")

GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Available Groq models (as of 2026)
GROQ_MODELS = {
    "llama-3.3-70b-versatile": "Fast, versatile general-purpose",
    "llama-3.1-8b-instant": "Ultra-fast, lightweight",
    "mixtral-8x7b-32768": "Large context window",
    "gemma2-9b-it": "Google Gemma 2, efficient",
}

# Retry config for Groq
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 0.5   # seconds — Groq is fast, retry quickly
_RETRY_MAX_DELAY = 5.0    # seconds


def _classify_error(exc: Exception) -> str:
    """Return a short, human-readable error category."""
    msg = str(exc).lower()
    if "429" in msg or "rate limit" in msg or "ratelimit" in msg:
        return "rate_limit"
    if any(c in msg for c in ["401", "403", "authentication", "api key", "unauthorized"]):
        return "auth_error"
    if any(c in msg for c in ["500", "502", "503", "504", "server error", "overloaded"]):
        return "server_error"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "connection" in msg or "eof" in msg or "reset" in msg:
        return "connection_error"
    return "unknown_error"


class GroqAdapter(BaseLLMAdapter):
    """Groq adapter — OpenAI-compatible, ultra-fast inference.

    Uses the OpenAI Python client with Groq's base_url.
    Supports all Groq-hosted models (Llama 3.3, Mixtral, Gemma).
    Supports multiple API keys for rotation (spread rate limits).
    """

    # Pricing: Groq — varies by model, generally very cheap
    # Llama 3.3 70B: $0.59/1M input, $0.79/1M output
    INPUT_COST_PER_TOKEN = 0.59 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 0.79 / 1_000_000

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        max_tokens: int = 200,
        timeout_ms: int = 5000,   # Raised from 500ms — too aggressive for real API
        api_key: str = "",
        api_keys: list[str] | None = None,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        super().__init__("groq", model, max_tokens, timeout_ms)
        self._api_keys: list[str] = []
        self._key_index = 0          # Current key index (rotates on rate limit)
        self._clients: dict[str, Any] = {}
        self._max_retries = max_retries

        # Support multiple keys
        if api_keys:
            self._api_keys = [k.strip() for k in api_keys if k.strip()]
        elif api_key:
            self._api_keys = [api_key]
        # Load from env if not provided
        if not self._api_keys:
            # Try comma-separated GROQ_API_KEYS first
            multi = os.getenv("GROQ_API_KEYS", "")
            if multi:
                self._api_keys = [k.strip() for k in multi.split(",") if k.strip()]
            else:
                # Fall back to single GROQ_API_KEY
                single = ""
                try:
                    single = get_env().groq_api_key
                except Exception:
                    pass
                if not single:
                    single = os.getenv("GROQ_API_KEY", "")
                if single:
                    self._api_keys = [single]

        if self._api_keys:
            logger.info("groq_keys_loaded", count=len(self._api_keys))

    def _get_client(self, key_offset: int = 0) -> tuple[Any, str]:
        """Get OpenAI client for a specific key index offset.

        Returns (client, api_key) tuple.
        key_offset allows rotating to next key on rate limit.
        """
        if not self._api_keys:
            raise RuntimeError(
                "GROQ_API_KEY not set. Add it to .env or pass via constructor."
            )

        idx = (self._key_index + key_offset) % len(self._api_keys)
        key = self._api_keys[idx]

        if key not in self._clients:
            import openai
            self._clients[key] = openai.AsyncOpenAI(
                api_key=key,
                base_url=GROQ_BASE_URL,
                timeout=self.timeout_ms / 1000.0,
                max_retries=0,  # We handle retries ourselves
            )
        return self._clients[key], key

    def _advance_key(self) -> None:
        """Rotate to the next API key (called on rate limit)."""
        if len(self._api_keys) > 1:
            self._key_index = (self._key_index + 1) % len(self._api_keys)
            logger.info("groq_key_rotated", new_index=self._key_index)

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
                # On rate limit, try the next key in the pool
                key_offset = attempt - 1
                client, active_key = self._get_client(key_offset=key_offset)

                response = await client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                )
                latency = (time.time() - start) * 1000

                # Validate response structure
                if not response.choices or response.choices[0].message is None:
                    raise ValueError("Empty response from Groq API")

                text = response.choices[0].message.content or ""
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else 0
                output_tokens = usage.completion_tokens if usage else 0

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
                    metadata={"attempt": attempt},
                )
                self.record_usage(result)
                logger.info(
                    "groq_generate",
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
                    "groq_timeout",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    timeout_sec=self.timeout_ms / 1000.0,
                    trace_id=trace_id,
                )

            except Exception as e:
                last_error = e
                err_cat = _classify_error(e)

                if err_cat == "auth_error":
                    # Auth errors → no point retrying any key
                    logger.error("groq_auth_error", error=str(e), trace_id=trace_id)
                    break

                if err_cat == "rate_limit":
                    # Rate limit → rotate to next key immediately
                    logger.warning(
                        "groq_rate_limit",
                        attempt=attempt,
                        trace_id=trace_id,
                    )
                    self._advance_key()
                else:
                    logger.warning(
                        "groq_error",
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
                    "groq_retry_wait",
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
            "groq_all_attempts_failed",
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
        if is_mock_mode():
            return True
        try:
            client, _ = self._get_client()
            # Real connectivity check — list models
            await asyncio.wait_for(
                client.models.list(),
                timeout=5.0,
            )
            return True
        except asyncio.TimeoutError:
            logger.warning("groq_health_timeout")
            return False
        except Exception as e:
            err_cat = _classify_error(e)
            if err_cat == "auth_error":
                logger.error("groq_health_auth_error", error=str(e))
            else:
                logger.warning("groq_health_failed", error=str(e))
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.INPUT_COST_PER_TOKEN) + (output_tokens * self.OUTPUT_COST_PER_TOKEN)

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-Groq/{self.model}] Fast response to: {prompt[:50]}..."
        result = LLMResponse(
            text=mock_text,
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()),
            latency_ms=10.0,  # Groq is ultra-fast
            trace_id=trace_id,
        )
        self.record_usage(result)
        return result
