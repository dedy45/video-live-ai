"""Claude Sonnet LLM adapter.

Primary provider for high-quality script generation.
Requirements: 1.1, 1.3
"""

from __future__ import annotations

import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import get_env, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.claude")


class ClaudeAdapter(BaseLLMAdapter):
    """Anthropic Claude Sonnet adapter — optimized for quality."""

    # Pricing: Claude Sonnet — $3/1M input, $15/1M output
    INPUT_COST_PER_TOKEN = 3.0 / 1_000_000
    OUTPUT_COST_PER_TOKEN = 15.0 / 1_000_000

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 2000,
        timeout_ms: int = 5000,
    ) -> None:
        super().__init__("claude", model, max_tokens, timeout_ms)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import anthropic

            api_key = get_env().anthropic_api_key
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not set")
            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        return self._client

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.SELLING_SCRIPT,
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
            response = await client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            latency = (time.time() - start) * 1000
            text = response.content[0].text if response.content else ""
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens

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
            )
            self.record_usage(result)
            logger.info("claude_generate", latency_ms=latency, tokens=result.total_tokens, trace_id=trace_id)
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error("claude_error", error=str(e), trace_id=trace_id)
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
        mock_text = f"[MOCK-Claude] High-quality script for: {prompt[:50]}..."
        result = LLMResponse(
            text=mock_text, provider=self.provider_name, model=self.model,
            task_type=task_type, input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()), latency_ms=50.0, trace_id=trace_id,
        )
        self.record_usage(result)
        return result
