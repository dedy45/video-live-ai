"""GPT-4o-mini LLM adapter.

Used for emotion detection and as backup for chat replies.
Requirements: 1.1, 1.4
"""

from __future__ import annotations

import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import get_env, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.gpt4o")


class GPT4oAdapter(BaseLLMAdapter):
    """OpenAI GPT-4o-mini adapter — emotion detection + backup."""

    # Pricing: GPT-4o-mini — $0.15/1M input, $0.60/1M output
    INPUT_COST_PER_TOKEN = 0.15 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 0.60 / 1_000_000

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_tokens: int = 200,
        timeout_ms: int = 1000,
    ) -> None:
        super().__init__("gpt4o", model, max_tokens, timeout_ms)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            api_key = get_env().openai_api_key
            if not api_key:
                raise RuntimeError("OPENAI_API_KEY not set")
            self._client = openai.AsyncOpenAI(api_key=api_key)
        return self._client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.EMOTION_DETECT,
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
        try:
            client = self._get_client()
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
            text = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

            result = LLMResponse(
                text=text, provider=self.provider_name, model=self.model,
                task_type=task_type, input_tokens=input_tokens,
                output_tokens=output_tokens, latency_ms=latency,
                cost_usd=self.estimate_cost(input_tokens, output_tokens),
                trace_id=trace_id,
            )
            self.record_usage(result)
            logger.info("gpt4o_generate", latency_ms=latency, tokens=result.total_tokens, trace_id=trace_id)
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error("gpt4o_error", error=str(e), trace_id=trace_id)
            result = LLMResponse(
                text="", provider=self.provider_name, model=self.model,
                task_type=task_type, latency_ms=latency,
                success=False, error=str(e), trace_id=trace_id,
            )
            self.record_usage(result)
            return result

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return (input_tokens * self.INPUT_COST_PER_TOKEN) + (output_tokens * self.OUTPUT_COST_PER_TOKEN)

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-GPT4o] Emotion: cheerful | Confidence: 0.85"
        result = LLMResponse(
            text=mock_text, provider=self.provider_name, model=self.model,
            task_type=task_type, input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()), latency_ms=25.0, trace_id=trace_id,
        )
        self.record_usage(result)
        return result
