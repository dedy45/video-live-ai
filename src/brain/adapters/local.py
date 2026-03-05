"""Local/Qwen LLM adapter — cost-free filler generation.

Uses a local model server (e.g., Ollama, vLLM) via OpenAI-compatible API.
Zero cost, used for filler generation and budget-mode operation.
Requirements: 1.1, 1.5, 1.9
"""

from __future__ import annotations

import os
import time
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("brain.local")

# Default: Ollama local server
DEFAULT_LOCAL_URL = "http://localhost:11434/v1"


class LocalAdapter(BaseLLMAdapter):
    """Local model adapter — zero-cost, OpenAI-compatible local inference.

    Supports Ollama, vLLM, LM Studio, and any OpenAI-compatible local server.
    """

    def __init__(
        self,
        model: str = "qwen2.5:7b",
        max_tokens: int = 100,
        timeout_ms: int = 2000,
        base_url: str = "",
    ) -> None:
        super().__init__("local", model, max_tokens, timeout_ms)
        self._base_url = base_url or os.getenv("LOCAL_LLM_URL", DEFAULT_LOCAL_URL)
        self._client: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            import openai

            self._client = openai.AsyncOpenAI(
                api_key="local",  # Local servers don't need real keys
                base_url=self._base_url,
            )
        return self._client

    async def _is_server_available(self) -> bool:
        """Quick TCP-level check to see if local server port is open."""
        import asyncio
        try:
            host = self._base_url.split("//")[-1].split("/")[0].split(":")[0]
            port_str = self._base_url.split(":")[-1].split("/")[0]
            port = int(port_str) if port_str.isdigit() else 11434
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
        task_type: TaskType = TaskType.FILLER,
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

        # Quick availability check before wasting timeout budget
        if not await self._is_server_available():
            logger.warning(
                "local_server_unavailable",
                url=self._base_url,
                trace_id=trace_id,
            )
            self.is_available = False
            result = LLMResponse(
                text="", provider=self.provider_name, model=self.model,
                task_type=task_type, latency_ms=0.0,
                success=False, error="local_server_not_running",
                trace_id=trace_id,
            )
            self.record_usage(result)
            return result

        self.is_available = True
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

            if not response.choices or response.choices[0].message is None:
                raise ValueError("Empty response from local server")

            text = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0

            result = LLMResponse(
                text=text, provider=self.provider_name, model=self.model,
                task_type=task_type, input_tokens=input_tokens,
                output_tokens=output_tokens, latency_ms=latency,
                cost_usd=0.0,  # Local = free
                trace_id=trace_id,
            )
            self.record_usage(result)
            logger.info(
                "local_generate",
                latency_ms=round(latency, 1),
                model=self.model,
                trace_id=trace_id,
            )
            return result

        except Exception as e:
            latency = (time.time() - start) * 1000
            logger.error("local_error", error=str(e), trace_id=trace_id)
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
        # First: fast TCP check
        if not await self._is_server_available():
            logger.warning("local_health_server_down", url=self._base_url)
            self.is_available = False
            return False
        try:
            import asyncio
            client = self._get_client()
            await asyncio.wait_for(client.models.list(), timeout=3.0)
            self.is_available = True
            return True
        except Exception as e:
            logger.warning("local_health_failed", error=str(e))
            self.is_available = False
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return 0.0  # Local models are free

    def _mock_response(self, prompt: str, task_type: TaskType, trace_id: str) -> LLMResponse:
        mock_text = f"[MOCK-Local] Filler: Wah, seru banget ya kak!"
        result = LLMResponse(
            text=mock_text, provider=self.provider_name, model=self.model,
            task_type=task_type, input_tokens=len(prompt.split()),
            output_tokens=len(mock_text.split()), latency_ms=30.0, trace_id=trace_id,
        )
        self.record_usage(result)
        return result
