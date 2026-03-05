"""LLM Router — Intelligent task routing with fallback chain.

Menggunakan LiteLLM (https://github.com/BerriAI/litellm) sebagai
backend universal untuk semua provider LLM. LiteLLM sudah proven
mendukung 100+ provider dengan interface yang konsisten.

Provider yang dikonfigurasi:
  - gemini          → Google Gemini 2.0 Flash
  - claude          → Anthropic Claude Sonnet
  - gpt4o           → OpenAI GPT-4o Mini
  - groq            → Groq Llama 3.3 70B (ultra-fast)
  - chutes          → Chutes.ai MiniMax M2.5 (via custom base_url)
  - gemini_local_pro   → Local proxy gemini-3.1-pro-high (localhost:8091)
  - gemini_local_flash → Local proxy gemini-3-flash (localhost:8091)
  - local           → Local Ollama/vLLM (localhost:11434)

Requirements: 1.1, 1.6, 1.7, 1.8, 1.9, 1.10
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from src.brain.adapters.base import BaseLLMAdapter, LLMResponse, TaskType
from src.brain.adapters.chutes import ChutesAdapter
from src.brain.adapters.litellm_adapter import LiteLLMAdapter
from src.config import get_config
from src.utils.logging import generate_trace_id, get_logger

logger = get_logger("brain.router")

# Default task→provider mapping
# Prioritaskan Cherry Studio (8091) yang gratis dan sudah terbukti berfungsi
# Groq sebagai cloud provider tercepat
# Gemini cloud di akhir karena quota sering habis
DEFAULT_ROUTING: dict[TaskType, list[str]] = {
    TaskType.CHAT_REPLY:     ["groq", "gemini_local_flash", "gemini_25_flash", "gpt4o_local", "claude_local", "chutes", "local", "gemini"],
    TaskType.SELLING_SCRIPT: ["claude_local", "gemini_local_pro", "gpt4o_local", "chutes", "groq", "gemini"],
    TaskType.HUMOR:          ["groq", "gemini_local_flash", "gemini_25_flash", "gpt4o_local", "local", "gemini"],
    TaskType.PRODUCT_QA:     ["gemini_local_pro", "claude_local", "gpt4o_local", "chutes", "groq", "gemini"],
    TaskType.EMOTION_DETECT: ["groq", "gemini_local_flash", "gemini_25_flash", "gpt4o_local", "gemini"],
    TaskType.FILLER:         ["gemini_local_flash", "groq", "local", "gemini_25_flash", "gemini"],
    TaskType.SAFETY_CHECK:   ["claude_local", "gemini_local_pro", "gpt4o_local", "groq", "gemini"],
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

    Semua adapter menggunakan LiteLLMAdapter — tidak ada custom HTTP client.
    LiteLLM handles authentication, retry, dan token counting secara internal.
    """
    # Pastikan .env sudah ter-load
    _load_env()

    # ── Env vars ──────────────────────────────────────────
    gemini_key    = os.getenv("GEMINI_API_KEY", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key    = os.getenv("OPENAI_API_KEY", "")
    groq_key      = os.getenv("GROQ_API_KEY", "")
    # Chutes: coba CHUTES_API_TOKEN dulu, fallback ke CHUTES_API_KEY
    chutes_token  = (os.getenv("CHUTES_API_TOKEN", "")
                     or os.getenv("CHUTES_API_KEY", ""))
    # Local LLM: bisa Ollama (11434) atau Cherry Studio (8091)
    local_url     = os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1")
    local_key     = os.getenv("LOCAL_API", "ollama")
    local_model   = os.getenv("LOCAL_LLM_MODEL", getattr(llm_cfg.qwen, "model", "qwen2.5:7b"))
    # Local Gemini proxy (Cherry Studio port 8091)
    gem_local_url = os.getenv("LOCAL_GEMINI_URL", "http://127.0.0.1:8091/v1")
    gem_local_key = os.getenv("LOCAL_GEMINI_API_KEY",
                               os.getenv("LOCAL_API", "sk-231d5e6912b44d929ac0b93ba2d2e033"))

    adapters: dict[str, BaseLLMAdapter] = {}

    # ── Google Gemini ──────────────────────────────────────
    # LiteLLM model string: "gemini/gemini-2.0-flash"
    adapters["gemini"] = LiteLLMAdapter(
        provider_name="gemini",
        litellm_model=f"gemini/{llm_cfg.gemini.model}",
        max_tokens=llm_cfg.gemini.max_tokens,
        timeout_ms=llm_cfg.gemini.timeout_ms,
        api_key=gemini_key or None,
        cost_per_input_token=0.075 / 1_000_000,
        cost_per_output_token=0.30 / 1_000_000,
    )

    # ── Anthropic Claude ───────────────────────────────────
    # LiteLLM model string: "anthropic/claude-sonnet-4-5"
    adapters["claude"] = LiteLLMAdapter(
        provider_name="claude",
        litellm_model=f"anthropic/{llm_cfg.claude.model}",
        max_tokens=llm_cfg.claude.max_tokens,
        timeout_ms=llm_cfg.claude.timeout_ms,
        api_key=anthropic_key or None,
        cost_per_input_token=3.0 / 1_000_000,
        cost_per_output_token=15.0 / 1_000_000,
    )

    # ── OpenAI GPT-4o ──────────────────────────────────────
    # LiteLLM model string: "openai/gpt-4o-mini"
    adapters["gpt4o"] = LiteLLMAdapter(
        provider_name="gpt4o",
        litellm_model=f"openai/{llm_cfg.gpt4o.model}",
        max_tokens=llm_cfg.gpt4o.max_tokens,
        timeout_ms=llm_cfg.gpt4o.timeout_ms,
        api_key=openai_key or None,
        cost_per_input_token=0.15 / 1_000_000,
        cost_per_output_token=0.60 / 1_000_000,
    )

    # ── Groq (ultra-fast Llama 3.3) ────────────────────────
    # LiteLLM model string: "groq/llama-3.3-70b-versatile"
    adapters["groq"] = LiteLLMAdapter(
        provider_name="groq",
        litellm_model="groq/llama-3.3-70b-versatile",
        max_tokens=300,
        timeout_ms=8000,
        api_key=groq_key or None,
        cost_per_input_token=0.59 / 1_000_000,
        cost_per_output_token=0.79 / 1_000_000,
    )

    # ── Chutes.ai MiniMax M2.5 ─────────────────────────────
    # Chutes pakai SSE streaming custom — LiteLLM tidak bisa handle dengan benar
    # Gunakan ChutesAdapter (aiohttp) yang sudah terbukti berfungsi
    _chutes_model = os.getenv("CHUTES_MODEL", "MiniMaxAI/MiniMax-M2.5-TEE")
    adapters["chutes"] = ChutesAdapter(
        model=_chutes_model,
        max_tokens=1024,
        timeout_ms=30000,
        api_key=chutes_token,
        max_retries=2,
    )

    # ── Local Gemini Proxy Flash (localhost:8091) — FAST ──────────
    adapters["gemini_local_flash"] = LiteLLMAdapter(
        provider_name="gemini_local_flash",
        litellm_model="openai/gemini-3-flash",
        max_tokens=500,
        timeout_ms=15000,  # Raised: Cherry Studio bisa lambat
        api_key=gem_local_key,
        api_base=gem_local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
    )

    # ── Local Gemini 2.5 Flash (localhost:8091) — FAST ALT ────────
    adapters["gemini_25_flash"] = LiteLLMAdapter(
        provider_name="gemini_25_flash",
        litellm_model="openai/gemini-2.5-flash",
        max_tokens=500,
        timeout_ms=15000,
        api_key=gem_local_key,
        api_base=gem_local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
    )

    # ── Local Gemini Proxy Pro (localhost:8091) — HIGH QUALITY ────
    adapters["gemini_local_pro"] = LiteLLMAdapter(
        provider_name="gemini_local_pro",
        litellm_model="openai/gemini-3.1-pro-high",
        max_tokens=1000,
        timeout_ms=60000,  # Pro model butuh waktu lebih lama
        api_key=gem_local_key,
        api_base=gem_local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
    )

    # ── Local Claude Sonnet via Cherry Studio (localhost:8091) ────
    adapters["claude_local"] = LiteLLMAdapter(
        provider_name="claude_local",
        litellm_model="openai/claude-sonnet-4-5",
        max_tokens=1000,
        timeout_ms=30000,
        api_key=gem_local_key,
        api_base=gem_local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
    )

    # ── Local GPT-4o via Cherry Studio (localhost:8091) ───────────
    adapters["gpt4o_local"] = LiteLLMAdapter(
        provider_name="gpt4o_local",
        litellm_model="openai/gpt-4o",
        max_tokens=500,
        timeout_ms=20000,
        api_key=gem_local_key,
        api_base=gem_local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
    )

    # ── Local Ollama/vLLM / Cherry Studio fallback ─────────────────────────────────────────
    # LOCAL_LLM_URL bisa Ollama (11434) atau Cherry Studio (8091)
    # Jika LOCAL_LLM_URL sama dengan gem_local_url → pakai model yang sama (gemini-3-flash)
    # Jika berbeda → pakai model dari config (qwen2.5:7b untuk Ollama)
    # Normalize URL untuk perbandingan (localhost == 127.0.0.1, trailing slash)
    def _norm_url(u: str) -> str:
        return u.rstrip("/").replace("localhost", "127.0.0.1")

    if _norm_url(local_url) == _norm_url(gem_local_url):
        # LOCAL_LLM_URL menunjuk ke Cherry Studio — pakai model yang tersedia di sana
        _local_model_name = os.getenv("LOCAL_LLM_MODEL", "gemini-3-flash")
        _local_key = gem_local_key
        logger.info("local_adapter_using_cherry_studio", url=local_url, model=_local_model_name)
    else:
        _local_model_name = local_model
        _local_key = local_key or "ollama"
        logger.info("local_adapter_using_ollama", url=local_url, model=_local_model_name)

    adapters["local"] = LiteLLMAdapter(
        provider_name="local",
        litellm_model=f"openai/{_local_model_name}",
        max_tokens=getattr(llm_cfg.qwen, "max_tokens", 300),
        timeout_ms=getattr(llm_cfg.qwen, "timeout_ms", 15000),
        api_key=_local_key,
        api_base=local_url,
        cost_per_input_token=0.0,
        cost_per_output_token=0.0,
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
        self.routing_table = DEFAULT_ROUTING.copy()
        self._total_cost_today = 0.0

        logger.info(
            "router_initialized",
            backend="litellm",
            adapters=list(self.adapters.keys()),
            budget_usd=self.daily_budget_usd,
        )

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
        """Check health of all providers."""
        results: dict[str, bool] = {}
        for name, adapter in self.adapters.items():
            results[name] = await adapter.health_check()
        return results

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
