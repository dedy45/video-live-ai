"""LiteLLM Universal Adapter — satu adapter untuk SEMUA provider LLM.

LiteLLM (https://github.com/BerriAI/litellm) adalah library proven yang
sudah support 100+ LLM provider dengan interface yang konsisten.

Provider yang didukung via LiteLLM:
  - gemini/gemini-2.0-flash          → Google Gemini
  - anthropic/claude-sonnet-4-5      → Anthropic Claude
  - openai/gpt-4o-mini               → OpenAI GPT
  - groq/llama-3.3-70b-versatile     → Groq (ultra-fast)
  - openai/MiniMaxAI/MiniMax-M2.5    → Chutes.ai (via custom base_url)
  - openai/gemini-3-flash            → Local Gemini proxy (localhost:8091)
  - openai/qwen2.5:7b                → Local Ollama (localhost:11434)

Format model string LiteLLM:
  "<provider>/<model_name>"
  Untuk OpenAI-compatible endpoint: provider="openai", set OPENAI_API_BASE

Env vars yang dibutuhkan (lihat .env.example):
  GEMINI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, GROQ_API_KEY,
  CHUTES_API_TOKEN, LOCAL_GEMINI_URL, LOCAL_GEMINI_API_KEY, LOCAL_LLM_URL
"""

from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import litellm
from litellm import acompletion
from litellm.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
    ServiceUnavailableError,
    Timeout,
)

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.litellm")

# Suppress LiteLLM verbose logging — kita pakai structlog sendiri
litellm.suppress_debug_info = True
litellm.set_verbose = False

# Retry config
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 0.5   # seconds
_RETRY_MAX_DELAY = 8.0    # seconds


def _classify_exc(exc: Exception) -> str:
    """Klasifikasi exception LiteLLM ke kategori sederhana."""
    if isinstance(exc, RateLimitError):
        return "rate_limit"
    if isinstance(exc, AuthenticationError):
        return "auth_error"
    if isinstance(exc, (ServiceUnavailableError,)):
        return "server_error"
    if isinstance(exc, Timeout):
        return "timeout"
    if isinstance(exc, BadRequestError):
        return "bad_request"
    if isinstance(exc, asyncio.TimeoutError):
        return "timeout"
    msg = str(exc).lower()
    if "429" in msg or "rate limit" in msg:
        return "rate_limit"
    if "401" in msg or "403" in msg or "auth" in msg:
        return "auth_error"
    if any(c in msg for c in ["500","502","503","504","unavailable"]):
        return "server_error"
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "connection" in msg or "refused" in msg or "eof" in msg:
        return "connection_error"
    return "unknown_error"


def _is_retryable(err_cat: str) -> bool:
    return err_cat in ("rate_limit", "server_error", "timeout", "connection_error", "unknown_error")


class LiteLLMAdapter(BaseLLMAdapter):
    """Universal LLM adapter menggunakan LiteLLM.

    Satu class ini menggantikan semua adapter custom (gemini, claude,
    gpt4o, groq, chutes, local, gemini_local). LiteLLM handles:
      - Authentication per provider
      - Retry logic
      - Token counting
      - Cost estimation
      - Streaming / non-streaming
      - OpenAI-compatible custom endpoints

    Args:
        provider_name: Nama pendek untuk logging (contoh: "groq", "chutes")
        litellm_model: Model string format LiteLLM (contoh: "groq/llama-3.3-70b-versatile")
        max_tokens: Max output tokens
        timeout_ms: Timeout dalam ms
        api_key: API key (opsional, fallback ke env var)
        api_base: Custom base URL untuk OpenAI-compatible endpoints
        extra_headers: Header tambahan (contoh: Bearer token untuk Chutes)
        cost_per_input_token: Override harga input token (USD)
        cost_per_output_token: Override harga output token (USD)
        max_retries: Jumlah retry maksimum
    """

    def __init__(
        self,
        provider_name: str,
        litellm_model: str,
        max_tokens: int = 500,
        timeout_ms: int = 10000,
        api_key: str = "",
        api_base: str = "",
        extra_headers: dict[str, str] | None = None,
        cost_per_input_token: float = 0.0,
        cost_per_output_token: float = 0.0,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        super().__init__(provider_name, litellm_model, max_tokens, timeout_ms)
        self._litellm_model = litellm_model
        self._api_key = api_key
        self._api_base = api_base
        self._extra_headers = extra_headers or {}
        self._cost_per_input = cost_per_input_token
        self._cost_per_output = cost_per_output_token
        self._max_retries = max_retries

        logger.info(
            "litellm_adapter_init",
            provider=provider_name,
            model=litellm_model,
            api_base=api_base or "default",
            timeout_ms=timeout_ms,
        )

    def _build_kwargs(self) -> dict[str, Any]:
        """Build kwargs untuk litellm.acompletion()."""
        kwargs: dict[str, Any] = {
            "model": self._litellm_model,
            "max_tokens": self.max_tokens,
            "temperature": 0.7,
            "timeout": self.timeout_ms / 1000.0,
            "num_retries": 0,  # kita handle retry sendiri
        }
        if self._api_key:
            kwargs["api_key"] = self._api_key
        if self._api_base:
            kwargs["api_base"] = self._api_base
        if self._extra_headers:
            kwargs["extra_headers"] = self._extra_headers
        return kwargs

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
                text="", provider=self.provider_name, model=self._litellm_model,
                task_type=task_type, success=False,
                error="Empty prompt", trace_id=trace_id,
            )

        messages = []
        if system_prompt.strip():
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})

        call_kwargs = self._build_kwargs()
        call_kwargs["messages"] = messages

        start = time.time()
        last_error: Exception = RuntimeError("No attempts made")

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await acompletion(**call_kwargs)
                latency = (time.time() - start) * 1000

                # Ekstrak text
                text = response.choices[0].message.content or ""
                if not text.strip():
                    raise ValueError("Empty response from LiteLLM")

                # Token usage — LiteLLM selalu mengisi ini
                usage = response.usage
                input_tokens = getattr(usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(usage, "completion_tokens", 0) or 0

                # Cost — gunakan LiteLLM cost calculation jika tersedia
                cost_usd = self.estimate_cost(input_tokens, output_tokens)
                try:
                    # LiteLLM bisa hitung cost otomatis
                    lm_cost = litellm.completion_cost(completion_response=response)
                    if lm_cost and lm_cost > 0:
                        cost_usd = lm_cost
                except Exception:
                    pass  # fallback ke manual estimate

                result = LLMResponse(
                    text=text,
                    provider=self.provider_name,
                    model=self._litellm_model,
                    task_type=task_type,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency,
                    cost_usd=cost_usd,
                    trace_id=trace_id,
                    metadata={
                        "attempt": attempt,
                        "litellm_model": self._litellm_model,
                        "finish_reason": response.choices[0].finish_reason,
                    },
                )
                self.record_usage(result)
                logger.info(
                    "litellm_generate_ok",
                    provider=self.provider_name,
                    model=self._litellm_model,
                    latency_ms=round(latency, 1),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=round(cost_usd, 6),
                    attempt=attempt,
                    trace_id=trace_id,
                )
                return result

            except (RateLimitError, AuthenticationError, ServiceUnavailableError,
                    Timeout, BadRequestError, asyncio.TimeoutError) as e:
                last_error = e
                err_cat = _classify_exc(e)
                if err_cat == "auth_error" or err_cat == "bad_request":
                    logger.error(
                        "litellm_fatal_error",
                        provider=self.provider_name,
                        error_category=err_cat,
                        error=str(e)[:200],
                        trace_id=trace_id,
                    )
                    break  # tidak perlu retry
                logger.warning(
                    "litellm_retryable_error",
                    provider=self.provider_name,
                    attempt=attempt,
                    max_retries=self._max_retries,
                    error_category=err_cat,
                    error=str(e)[:200],
                    trace_id=trace_id,
                )

            except Exception as e:
                last_error = e
                err_cat = _classify_exc(e)
                if err_cat == "auth_error":
                    logger.error(
                        "litellm_auth_error",
                        provider=self.provider_name,
                        error=str(e)[:200],
                        trace_id=trace_id,
                    )
                    break
                logger.warning(
                    "litellm_error",
                    provider=self.provider_name,
                    attempt=attempt,
                    max_retries=self._max_retries,
                    error_category=err_cat,
                    error=str(e)[:200],
                    trace_id=trace_id,
                )

            # Exponential backoff sebelum retry
            if attempt < self._max_retries:
                delay = min(_RETRY_BASE_DELAY * (2 ** (attempt - 1)), _RETRY_MAX_DELAY)
                logger.info(
                    "litellm_retry_wait",
                    provider=self.provider_name,
                    attempt=attempt,
                    wait_sec=round(delay, 2),
                    trace_id=trace_id,
                )
                await asyncio.sleep(delay)

        # Semua attempt gagal
        latency = (time.time() - start) * 1000
        err_cat = _classify_exc(last_error)
        logger.error(
            "litellm_all_failed",
            provider=self.provider_name,
            model=self._litellm_model,
            attempts=self._max_retries,
            error_category=err_cat,
            error=str(last_error)[:300],
            trace_id=trace_id,
        )
        result = LLMResponse(
            text="",
            provider=self.provider_name,
            model=self._litellm_model,
            task_type=task_type,
            latency_ms=latency,
            success=False,
            error=f"[{err_cat}] {str(last_error)[:200]}",
            trace_id=trace_id,
            metadata={"attempts": self._max_retries},
        )
        self.record_usage(result)
        return result

    async def health_check(self) -> bool:
        """Health check dengan request minimal ke provider."""
        if is_mock_mode():
            return True
        try:
            call_kwargs = self._build_kwargs()
            call_kwargs["messages"] = [{"role": "user", "content": "hi"}]
            call_kwargs["max_tokens"] = 5
            call_kwargs["timeout"] = 5.0
            call_kwargs["num_retries"] = 0
            response = await asyncio.wait_for(
                acompletion(**call_kwargs),
                timeout=8.0,
            )
            ok = bool(response.choices and response.choices[0].message.content)
            if ok:
                self.is_available = True
                logger.info("litellm_health_ok", provider=self.provider_name)
            else:
                self.is_available = False
                logger.warning("litellm_health_empty", provider=self.provider_name)
            return ok
        except AuthenticationError as e:
            self.is_available = False
            logger.error("litellm_health_auth_error", provider=self.provider_name, error=str(e)[:100])
            return False
        except asyncio.TimeoutError:
            self.is_available = False
            logger.warning("litellm_health_timeout", provider=self.provider_name)
            return False
        except Exception as e:
            self.is_available = False
            err_cat = _classify_exc(e)
            logger.warning(
                "litellm_health_failed",
                provider=self.provider_name,
                error_category=err_cat,
                error=str(e)[:100],
            )
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self._cost_per_input) + (output_tokens * self._cost_per_output)

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-{self.provider_name}/{self._litellm_model.split('/')[-1]}] {prompt[:60]}..."
        result = LLMResponse(
            text=mock_text,
            provider=self.provider_name,
            model=self._litellm_model,
            task_type=task_type,
            input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()),
            latency_ms=15.0,
            cost_usd=0.0,
            trace_id=trace_id,
            metadata={"mock": True},
        )
        self.record_usage(result)
        return result
