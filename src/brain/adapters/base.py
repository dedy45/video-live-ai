"""Base LLM adapter interface.

All LLM providers implement this abstract base class for consistent
routing, fallback, and cost tracking across the Multi-LLM Brain.
Requirements: 1.1, 1.6, 1.7, 1.8
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TaskType(str, Enum):
    """Types of tasks routed to LLMs."""

    CHAT_REPLY = "chat_reply"
    SELLING_SCRIPT = "selling_script"
    HUMOR = "humor"
    PRODUCT_QA = "product_qa"
    EMOTION_DETECT = "emotion_detect"
    FILLER = "filler"
    SAFETY_CHECK = "safety_check"


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider.

    Format is identical across all providers for round-trip property (Req 1.10).
    """

    text: str
    provider: str
    model: str
    task_type: TaskType
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    trace_id: str = ""
    success: bool = True
    error: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class LLMUsageStats:
    """Cumulative usage stats for a provider."""

    total_calls: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    error_count: int = 0

    @property
    def avg_latency_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.error_count / self.total_calls


class BaseLLMAdapter(ABC):
    """Abstract base class for all LLM provider adapters.

    Each adapter must implement:
    - generate(): async text generation
    - estimate_cost(): cost estimation per request
    - health_check(): connection verification
    """

    def __init__(self, provider_name: str, model: str, max_tokens: int, timeout_ms: int) -> None:
        self.provider_name = provider_name
        self.model = model
        self.max_tokens = max_tokens
        self.timeout_ms = timeout_ms
        self.stats = LLMUsageStats()
        self._is_available = True

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.CHAT_REPLY,
        trace_id: str = "",
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate text from the LLM provider.

        Args:
            system_prompt: System instruction.
            user_prompt: User query.
            task_type: Classification of the task.
            trace_id: Unique trace ID for request correlation (Req 34).

        Returns:
            Standardized LLMResponse.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Verify provider connectivity."""
        ...

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD. Override per provider."""
        return 0.0

    def record_usage(self, response: LLMResponse) -> None:
        """Record usage statistics."""
        self.stats.total_calls += 1
        self.stats.total_tokens += response.total_tokens
        self.stats.total_cost_usd += response.cost_usd
        self.stats.total_latency_ms += response.latency_ms
        if not response.success:
            self.stats.error_count += 1

    @property
    def is_available(self) -> bool:
        return self._is_available

    @is_available.setter
    def is_available(self, value: bool) -> None:
        self._is_available = value

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model} available={self._is_available}>"
