"""LLM Router — Intelligent task routing with fallback chain.

Menggunakan LiteLLM (https://github.com/BerriAI/litellm) sebagai
backend universal untuk semua provider LLM. LiteLLM sudah proven
mendukung 100+ provider dengan interface yang konsisten.

Provider yang dikonfigurasi:
  - gemini          → Google Gemini 2.0 Flash
  - claude          → Anthropic Claude Sonnet
  - gpt4o           → OpenAI GPT-4o Mini
  - groq            → Groq Llama 3.3 70B (ultra-fast)

Requirements: 1.1, 1.6, 1.7, 1.8, 1.9, 1.10
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.brain.adapters.litellm_adapter import LiteLLMAdapter
from src.config import get_config
from src.utils.logging import generate_trace_id, get_logger

logger = get_logger("brain.router")

# Default task→provider mapping
# PRIORITAS: Groq (tercepat) → Gemini → Claude → GPT-4o
DEFAULT_ROUTING: dict[TaskType, list[str]] = {
    TaskType.CHAT_REPLY:     ["groq", "gemini", "claude", "gpt4o"],
    TaskType.SELLING_SCRIPT: ["claude", "gpt4o", "groq", "gemini"],
    TaskType.HUMOR:          ["groq", "gemini", "gpt4o", "claude"],
    TaskType.PRODUCT_QA:     ["claude", "gpt4o", "gemini", "groq"],
    TaskType.EMOTION_DETECT: ["groq", "gemini", "claude", "gpt4o"],
    TaskType.FILLER:         ["groq", "gemini", "gpt4o", "claude"],
    TaskType.SAFETY_CHECK:   ["claude", "gpt4o", "groq", "gemini"],
}


def _load_env() -> None:
    """Load .env file jika belum di-load (untuk non-uvicorn context)."""
    try:
        from pathlib import Path
        env_file = Path(".env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # Jangan overwrite yang sudah ada di environment
                if key and val and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass  # Bukan fatal — env mungkin sudah di-set dari luar


def _build_adapters(llm_cfg: Any) -> dict[str, BaseLLMAdapter]:
    """Bangun semua LiteLLM adapter dari config + env vars.

    Hanya load adapter yang punya API key valid di .env.
    Adapter tanpa API key akan di-skip untuk performa lebih baik.
    """
    # Pastikan .env sudah ter-load
    _load_env()

    # ── Env vars ──────────────────────────────────────────
    gemini_key    = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key    = os.getenv("OPENAI_API_KEY", "")
    groq_key      = os.getenv("GROQ_API_KEY", "")

    adapters: dict[str, BaseLLMAdapter] = {}
    
    # Helper function to check if key is valid (not placeholder)
    def _is_valid_key(key: str) -> bool:
        if not key:
            return False
        # Check for common placeholder patterns
        placeholders = ["your_", "changeme", "placeholder", "xxx", "yyy"]
        key_lower = key.lower()
        return not any(p in key_lower for p in placeholders)

    # ── Google Gemini ──────────────────────────────────────
    if _is_valid_key(gemini_key):
        adapters["gemini"] = LiteLLMAdapter(
            provider_name="gemini",
            litellm_model=f"gemini/{llm_cfg.gemini.model}",
            max_tokens=llm_cfg.gemini.max_tokens,
            timeout_ms=llm_cfg.gemini.timeout_ms,
            api_key=gemini_key,
            cost_per_input_token=0.075 / 1_000_000,
            cost_per_output_token=0.30 / 1_000_000,
        )
        logger.info("adapter_loaded", provider="gemini", model=llm_cfg.gemini.model)
    else:
        logger.info("adapter_skipped", provider="gemini", reason="no_valid_api_key")

    # ── Anthropic Claude ───────────────────────────────────
    if _is_valid_key(anthropic_key):
        adapters["claude"] = LiteLLMAdapter(
            provider_name="claude",
            litellm_model=f"anthropic/{llm_cfg.claude.model}",
            max_tokens=llm_cfg.claude.max_tokens,
            timeout_ms=llm_cfg.claude.timeout_ms,
            api_key=anthropic_key,
            cost_per_input_token=3.0 / 1_000_000,
            cost_per_output_token=15.0 / 1_000_000,
        )
        logger.info("adapter_loaded", provider="claude", model=llm_cfg.claude.model)
    else:
        logger.info("adapter_skipped", provider="claude", reason="no_valid_api_key")

    # ── OpenAI GPT-4o ──────────────────────────────────────
    if _is_valid_key(openai_key):
        adapters["gpt4o"] = LiteLLMAdapter(
            provider_name="gpt4o",
            litellm_model=f"openai/{llm_cfg.gpt4o.model}",
            max_tokens=llm_cfg.gpt4o.max_tokens,
            timeout_ms=llm_cfg.gpt4o.timeout_ms,
            api_key=openai_key,
            cost_per_input_token=0.15 / 1_000_000,
            cost_per_output_token=0.60 / 1_000_000,
        )
        logger.info("adapter_loaded", provider="gpt4o", model=llm_cfg.gpt4o.model)
    else:
        logger.info("adapter_skipped", provider="gpt4o", reason="no_valid_api_key")

    # ── Groq (ultra-fast Llama 3.3) ────────────────────────
    if _is_valid_key(groq_key):
        adapters["groq"] = LiteLLMAdapter(
            provider_name="groq",
            litellm_model="groq/llama-3.3-70b-versatile",
            max_tokens=300,
            timeout_ms=8000,
            api_key=groq_key,
            cost_per_input_token=0.59 / 1_000_000,
            cost_per_output_token=0.79 / 1_000_000,
        )
        logger.info("adapter_loaded", provider="groq", model="llama-3.3-70b-versatile")
    else:
        logger.info("adapter_skipped", provider="groq", reason="no_valid_api_key")

    # Log summary
    logger.info(
        "adapters_build_complete",
        total_loaded=len(adapters),
        providers=list(adapters.keys()),
    )

    return adapters


class LLMRouter:
    """Intelligent LLM Router dengan LiteLLM backend.

    Semua provider menggunakan LiteLLMAdapter yang proven.
    Router handles: routing table, fallback chain, budget tracking.
    """

    def __init__(self) -> None:
        config = get_config()
        llm_cfg = config.llm_providers

        self.adapters: dict[str, BaseLLMAdapter] = _build_adapters(llm_cfg)
        self.daily_budget_usd = llm_cfg.daily_budget_usd
        
        # Build routing table dynamically based on loaded adapters
        self.routing_table = self._build_routing_table()
        self._total_cost_today = 0.0
        
        # Track current active provider (untuk dashboard)
        self.current_provider: str = "groq"  # Default ke Groq

        logger.info(
            "router_initialized",
            backend="litellm",
            adapters=list(self.adapters.keys()),
            budget_usd=self.daily_budget_usd,
            default_provider=self.current_provider,
        )

    def _build_routing_table(self) -> dict[TaskType, list[str]]:
        """Build routing table dynamically based on loaded adapters.
        
        Only include adapters that are actually loaded (have valid API keys).
        PRIORITAS: Groq → Gemini → Claude → GPT-4o
        """
        loaded = set(self.adapters.keys())
        
        # Helper to filter providers that are loaded
        def _filter(providers: list[str]) -> list[str]:
            return [p for p in providers if p in loaded]
        
        # Routing berdasarkan task type
        routing: dict[TaskType, list[str]] = {}
        
        # Chat replies - prioritize speed
        routing[TaskType.CHAT_REPLY] = _filter(["groq", "gemini", "claude", "gpt4o"])
        
        # Selling scripts - prioritize quality
        routing[TaskType.SELLING_SCRIPT] = _filter(["claude", "gpt4o", "groq", "gemini"])
        
        # Humor - prioritize speed
        routing[TaskType.HUMOR] = _filter(["groq", "gemini", "gpt4o", "claude"])
        
        # Product QA - prioritize accuracy
        routing[TaskType.PRODUCT_QA] = _filter(["claude", "gpt4o", "gemini", "groq"])
        
        # Emotion detection - prioritize speed
        routing[TaskType.EMOTION_DETECT] = _filter(["groq", "gemini", "claude", "gpt4o"])
        
        # Filler - prioritize speed
        routing[TaskType.FILLER] = _filter(["groq", "gemini", "gpt4o", "claude"])
        
        # Safety check - prioritize accuracy
        routing[TaskType.SAFETY_CHECK] = _filter(["claude", "gpt4o", "groq", "gemini"])
        
        # Ensure every task type has at least one provider
        for task_type, providers in routing.items():
            if not providers:
                # Fallback to any loaded adapter
                routing[task_type] = list(loaded)[:4]  # Use first 4 loaded
                logger.warning(
                    "routing_fallback",
                    task=task_type.value,
                    providers=routing[task_type],
                )
        
        logger.info(
            "routing_table_built",
            tasks=len(routing),
            total_providers=len(loaded),
        )
        
        return routing

    async def route(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: TaskType = TaskType.CHAT_REPLY,
        trace_id: str = "",
        preferred_provider: str | None = None,
    ) -> LLMResponse:
        """Route a request to the best available provider with fallback.

        Args:
            system_prompt: System instruction.
            user_prompt: User query.
            task_type: Type of task for routing.
            trace_id: Request trace ID. Generated if empty.
            preferred_provider: Override routing with specific provider.

        Returns:
            LLMResponse from first successful provider.

        Notes:
            - asyncio.TimeoutError is caught per-provider (outer wait_for guard)
            - All other exceptions from adapters are also caught so one broken
              provider never kills the entire fallback chain.
            - Adapters already handle their own retries internally, so the
              router only sees the final result after retries are exhausted.
        """
        if not trace_id:
            trace_id = generate_trace_id()

        # Budget check
        if self._total_cost_today >= self.daily_budget_usd:
            logger.warning("budget_exceeded", total=self._total_cost_today)
            # Fall back to local (free)
            providers = ["local"]
        elif preferred_provider and preferred_provider in self.adapters:
            # Preferred provider first, then fall through normal chain as backup
            normal_chain = self.routing_table.get(task_type, ["gemini", "gpt4o", "local"])
            providers = [preferred_provider] + [p for p in normal_chain if p != preferred_provider]
        else:
            providers = self.routing_table.get(task_type, ["gemini", "gpt4o", "local"])

        errors: list[str] = []

        # Try each provider in order
        for provider_name in providers:
            adapter = self.adapters.get(provider_name)
            if adapter is None or not adapter.is_available:
                continue

            try:
                # Outer timeout guard — adapters manage internal retries within
                # this window. We give extra headroom (2× adapter timeout) so
                # the adapter's internal retry logic has room to run.
                outer_timeout = (adapter.timeout_ms / 1000.0) * 2 + 5
                response = await asyncio.wait_for(
                    adapter.generate(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        task_type=task_type,
                        trace_id=trace_id,
                    ),
                    timeout=outer_timeout,
                )
            except asyncio.TimeoutError:
                msg = f"outer_timeout after {outer_timeout:.1f}s"
                errors.append(f"{provider_name}: {msg}")
                logger.warning(
                    "provider_outer_timeout",
                    provider=provider_name,
                    timeout_sec=outer_timeout,
                    trace_id=trace_id,
                )
                adapter.stats.error_count += 1
                continue
            except Exception as exc:
                # Unexpected exception from adapter (should not happen, but guard anyway)
                msg = str(exc)
                errors.append(f"{provider_name}: unexpected_exception: {msg}")
                logger.error(
                    "provider_unexpected_exception",
                    provider=provider_name,
                    error=msg,
                    trace_id=trace_id,
                )
                adapter.stats.error_count += 1
                continue

            if response.success:
                self._total_cost_today += response.cost_usd
                # Update current active provider
                self.current_provider = provider_name
                logger.info(
                    "route_success",
                    provider=provider_name,
                    task=task_type.value,
                    latency_ms=round(response.latency_ms, 1),
                    trace_id=trace_id,
                )
                return response
            else:
                errors.append(f"{provider_name}: {response.error}")
                logger.warning(
                    "provider_failed",
                    provider=provider_name,
                    error=response.error,
                    trace_id=trace_id,
                )

        # All providers failed — return structured error (no user-visible "sibuk" message)
        error_summary = " | ".join(errors) if errors else "no_providers_available"
        logger.error(
            "all_providers_failed",
            task=task_type.value,
            errors=error_summary,
            trace_id=trace_id,
        )
        return LLMResponse(
            text="",
            provider="none",
            model="none",
            task_type=task_type,
            success=False,
            error=error_summary,
            trace_id=trace_id,
        )

    async def health_check_all(self) -> dict[str, bool]:
        """Check health of all providers in parallel."""
        tasks = {
            name: adapter.health_check()
            for name, adapter in self.adapters.items()
        }
        # Run all health checks concurrently
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to provider names
        health_status: dict[str, bool] = {}
        for (name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                logger.warning("health_check_exception", provider=name, error=str(result))
                health_status[name] = False
            else:
                health_status[name] = result
        
        return health_status

    def get_usage_stats(self) -> dict[str, dict[str, Any]]:
        """Get usage stats for all providers."""
        stats: dict[str, dict[str, Any]] = {}
        for name, adapter in self.adapters.items():
            s = adapter.stats
            stats[name] = {
                "total_calls": s.total_calls,
                "total_tokens": s.total_tokens,
                "total_cost_usd": round(s.total_cost_usd, 6),
                "avg_latency_ms": round(s.avg_latency_ms, 1),
                "error_rate": round(s.error_rate, 3),
            }
        stats["_summary"] = {
            "daily_cost": round(self._total_cost_today, 4),
            "daily_budget": self.daily_budget_usd,
            "budget_remaining": round(self.daily_budget_usd - self._total_cost_today, 4),
        }
        return stats

    def reset_daily_cost(self) -> None:
        """Reset daily cost counter (call at midnight)."""
        self._total_cost_today = 0.0
        logger.info("daily_cost_reset")
