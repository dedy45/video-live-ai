"""Gemini Flash LLM adapter.

Primary provider for fast chat replies (<200ms target).
Requirements: 1.1, 1.2
"""

from __future__ import annotations

import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import get_env, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.gemini")


class GeminiAdapter(BaseLLMAdapter):
    """Google Gemini Flash adapter — optimized for speed."""

    # Pricing: Gemini Flash — $0.075/1M input, $0.30/1M output (approx)
    INPUT_COST_PER_TOKEN = 0.075 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 0.30 / 1_000_000

    def __init__(
        self,
        model: str = "gemini-2.0-flash",
        max_tokens: int = 150,
        timeout_ms: int = 5000,   # Raised from 500ms — was far too aggressive
        max_retries: int = 2,
    ) -> None:
        super().__init__("gemini", model, max_tokens, timeout_ms)
        self._client: Any = None
        self._max_retries = max_retries

    def _get_client(self) -> Any:
        if self._client is None:
            import google.generativeai as genai

            api_key = get_env().gemini_api_key
            if not api_key:
                raise RuntimeError("GEMINI_API_KEY not set")
            genai.configure(api_key=api_key)
            self._client = genai.GenerativeModel(self.model)
        return self._client

    def _classify_error(self, exc: Exception) -> str:
        msg = str(exc).lower()
        if "429" in msg or "quota" in msg or "rate" in msg:
            return "rate_limit"
        if any(c in msg for c in ["401", "403", "api key", "invalid"]):
            return "auth_error"
        if any(c in msg for c in ["500", "503", "unavailable"]):
            return "server_error"
        if "timeout" in msg or "deadline" in msg:
            return "timeout"
        return "unknown_error"

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
                client = self._get_client()
                full_prompt = f"{system_prompt}\n\nUser: {user_prompt}"
                response = await client.generate_content_async(
                    full_prompt,
                    generation_config={
                        "max_output_tokens": self.max_tokens,
                        "temperature": 0.7,
                    },
                )
                latency = (time.time() - start) * 1000
                text = response.text or ""
                # Estimate tokens (Gemini SDK doesn't always expose usage)
                input_tokens = int(len(full_prompt.split()) * 1.3)
                output_tokens = int(len(text.split()) * 1.3)

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
                    "gemini_generate",
                    latency_ms=round(latency, 1),
                    tokens=result.total_tokens,
                    attempt=attempt,
                    trace_id=trace_id,
                )
                return result

            except Exception as e:
                last_error = e
                err_cat = self._classify_error(e)
                if err_cat == "auth_error":
                    logger.error("gemini_auth_error", error=str(e), trace_id=trace_id)
                    break
                logger.warning(
                    "gemini_error",
                    attempt=attempt,
                    max_retries=self._max_retries,
                    error_category=err_cat,
                    error=str(e),
                    trace_id=trace_id,
                )
                if attempt < self._max_retries:
                    import asyncio
                    await asyncio.sleep(1.0 * attempt)

        latency = (time.time() - start) * 1000
        err_cat = self._classify_error(last_error)
        result = LLMResponse(
            text="",
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            latency_ms=latency,
            success=False,
            error=f"[{err_cat}] {last_error}",
            trace_id=trace_id,
        )
        self.record_usage(result)
        return result

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        try:
            self._get_client()
            return True
        except Exception as e:
            logger.warning("gemini_health_failed", error=str(e))
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.INPUT_COST_PER_TOKEN) + (output_tokens * self.OUTPUT_COST_PER_TOKEN)

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        """Return mock response for testing."""
        mock_text = f"[MOCK-Gemini] Response to: {prompt[:50]}..."
        result = LLMResponse(
            text=mock_text,
            provider=self.provider_name,
            model=self.model,
            task_type=task_type,
            input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()),
            latency_ms=15.0,
            trace_id=trace_id,
        )
        self.record_usage(result)
        return result
