"""GeminiLocal adapter — OpenAI-compatible local proxy for Gemini models.

Connects to a local/self-hosted proxy server (e.g., localhost:8091)
that exposes Gemini models via OpenAI-compatible /v1/chat/completions.

Supported models:
    - gemini-3.1-pro-high  (high-quality, slower)
    - gemini-3-flash        (fast, lightweight)

Usage:
    Set LOCAL_GEMINI_URL and LOCAL_GEMINI_API_KEY in .env, or pass via constructor.

    Example endpoint config:
        base_url = "http://127.0.0.1:8091/v1"
        api_key  = "sk-231d5e6912b44d929ac0b93ba2d2e033"

Fixes & features:
    - TCP-level availability check before wasting timeout budget
    - Retry with exponential backoff (max 3 attempts)
    - Error classification (rate_limit / auth / server / timeout)
    - is_available flag updated dynamically so router can skip if server is down
    - Zero cost (local proxy → no billing)
    - Mock mode support
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.gemini_local")

# Defaults — override via env or constructor
DEFAULT_LOCAL_GEMINI_URL = "http://127.0.0.1:8091/v1"
DEFAULT_LOCAL_GEMINI_KEY = "sk-231d5e6912b44d929ac0b93ba2d2e033"

# Available models on this local proxy
GEMINI_LOCAL_MODELS = {
    "gemini-3.1-pro-high": "High-quality Gemini 3.1 Pro — best for selling scripts & complex tasks",
    "gemini-3-flash": "Fast Gemini 3 Flash — best for chat replies & filler",
}

# Retry config
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 0.5   # seconds
_RETRY_MAX_DELAY = 5.0    # seconds


def _classify_error(exc: Exception) -> str:
    """Return a short error category string."""
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


class GeminiLocalAdapter(BaseLLMAdapter):
    """Adapter for a local OpenAI-compatible Gemini proxy (localhost:8091).

    Supports two models:
        - "gemini-3.1-pro-high" → high quality, use for SELLING_SCRIPT / PRODUCT_QA
        - "gemini-3-flash"      → fast, use for CHAT_REPLY / FILLER / HUMOR

    The adapter performs a quick TCP check before every generate() call
    so the router skips it immediately if the local server is not running,
    without waiting for the full HTTP timeout.
    """

    # Local proxy → no billing
    INPUT_COST_PER_TOKEN = 0.0
    OUTPUT_COST_PER_TOKEN = 0.0

    def __init__(
        self,
        model: str = "gemini-3-flash",
        max_tokens: int = 500,
        timeout_ms: int = 10000,
        base_url: str = "",
        api_key: str = "",
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        super().__init__("gemini_local", model, max_tokens, timeout_ms)
        self._base_url = (
            base_url
            or os.getenv("LOCAL_GEMINI_URL", DEFAULT_LOCAL_GEMINI_URL)
        ).rstrip("/")
        self._api_key = (
            api_key
            or os.getenv("LOCAL_GEMINI_API_KEY", DEFAULT_LOCAL_GEMINI_KEY)
        )
        self._max_retries = max_retries
        self._client: Any = None

        logger.info(
            "gemini_local_init",
            base_url=self._base_url,
            model=self.model,
            max_retries=self._max_retries,
        )

    def _get_client(self, force_recreate: bool = False) -> Any:
        if self._client is None or force_recreate:
            import openai

            self._client = openai.AsyncOpenAI(
                base_url=f"{self._base_url}",
                api_key=self._api_key,
                timeout=self.timeout_ms / 1000.0,
                max_retries=0,  # We handle retries ourselves
            )
        return self._client

    async def _is_server_available(self) -> bool:
        """Quick TCP-level port check — completes in ≤1s."""
        try:
            # Parse host:port from base_url
            netloc = self._base_url.split("//")[-1].split("/")[0]
            if ":" in netloc:
                host, port_str = netloc.rsplit(":", 1)
                port = int(port_str)
            else:
                host = netloc
                port = 80

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=1.0,
            )
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            return True
        except Exception:
            return False

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

        # Fast TCP check — skip long HTTP timeout if server is not running
        if not await self._is_server_available():
            logger.warning(
                "gemini_local_server_unavailable",
                url=self._base_url,
                trace_id=trace_id,
            )
            self.is_available = False
            result = LLMResponse(
                text="", provider=self.provider_name, model=self.model,
                task_type=task_type, latency_ms=0.0,
                success=False, error="gemini_local_server_not_running",
                trace_id=trace_id,
            )
            self.record_usage(result)
            return result

        self.is_available = True
        start = time.time()
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(1, self._max_retries + 1):
            try:
                client = self._get_client(force_recreate=(attempt > 1))
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

                if not response.choices or response.choices[0].message is None:
                    raise ValueError("Empty response from gemini_local proxy")

                text = response.choices[0].message.content or ""
                usage = response.usage
                input_tokens = usage.prompt_tokens if usage else int(len(user_prompt.split()) * 1.3)
                output_tokens = usage.completion_tokens if usage else int(len(text.split()) * 1.3)

                result = LLMResponse(
                    text=text,
                    provider=self.provider_name,
                    model=self.model,
                    task_type=task_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency,
                    cost_usd=0.0,  # Local proxy = free
                    trace_id=trace_id,
                    metadata={"attempt": attempt, "base_url": self._base_url},
                )
                self.record_usage(result)
                logger.info(
                    "gemini_local_generate",
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
                    "gemini_local_timeout",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    timeout_sec=self.timeout_ms / 1000.0,
                    trace_id=trace_id,
                )

            except Exception as e:
                last_error = e
                err_cat = _classify_error(e)

                if err_cat == "auth_error":
                    logger.error(
                        "gemini_local_auth_error",
                        error=str(e),
                        trace_id=trace_id,
                    )
                    break

                logger.warning(
                    "gemini_local_error",
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
                    "gemini_local_retry_wait",
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
            "gemini_local_all_attempts_failed",
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

        # 1. Fast TCP check
        if not await self._is_server_available():
            logger.warning("gemini_local_health_server_down", url=self._base_url)
            self.is_available = False
            return False

        # 2. API ping — list models
        try:
            client = self._get_client()
            await asyncio.wait_for(client.models.list(), timeout=3.0)
            self.is_available = True
            return True
        except asyncio.TimeoutError:
            logger.warning("gemini_local_health_timeout")
            self.is_available = False
            return False
        except Exception as e:
            err_cat = _classify_error(e)
            logger.warning(
                "gemini_local_health_failed",
                error_category=err_cat,
                error=str(e),
            )
            self.is_available = False
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0  # Local proxy = free

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-GeminiLocal/{self.model}] Response to: {prompt[:50]}..."
        result = LLMResponse(
            text=mock_text,
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()),
            latency_ms=20.0,
            trace_id=trace_id,
        )
        self.record_usage(result)
        return result
