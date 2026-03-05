"""Layer 1: Intelligence — LLM Adapters package.

Backend: LiteLLM (https://github.com/BerriAI/litellm)
Semua provider menggunakan LiteLLMAdapter — universal, proven, reliable.

Legacy adapter files (chutes.py, groq.py, gemini.py, etc.) masih ada
untuk backward compatibility tapi tidak lagi digunakan oleh router.
"""

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, LLMUsageStats, TaskType
from src.brain.adapters.litellm_adapter import LiteLLMAdapter

__all__ = [
    "BaseLLMAdapter",
    "LiteLLMAdapter",
    "LLMResponse",
    "LLMUsageStats",
    "TaskType",
]

