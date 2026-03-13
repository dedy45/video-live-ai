"""Runtime-only AI Brain configuration overlay.

Keeps operator edits in memory so they apply immediately without mutating
repo-tracked YAML or environment files.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.brain.adapters.base import TaskType
from src.config import get_config


def _normalize_task_name(task_name: str | TaskType) -> str:
    if isinstance(task_name, TaskType):
        return task_name.value
    return str(task_name).strip().lower()


def _normalize_routing_table(routing_table: dict[Any, list[str]] | None) -> dict[str, list[str]]:
    normalized: dict[str, list[str]] = {}
    for task_name, providers in (routing_table or {}).items():
        normalized[_normalize_task_name(task_name)] = list(providers)
    return normalized


class BrainRuntimeConfig:
    """Process-local runtime config overlay for the AI Brain cockpit."""

    def __init__(self) -> None:
        self._router_token: int | None = None
        self._daily_budget_usd = 0.0
        self._fallback_order: list[str] = []
        self._routing_table: dict[str, list[str]] = {}
        self._available_providers: list[str] = []

    def _seed_defaults(self) -> None:
        llm_cfg = get_config().llm_providers
        self._daily_budget_usd = float(llm_cfg.daily_budget_usd)
        self._fallback_order = list(llm_cfg.fallback_order)
        self._routing_table = {}
        self._available_providers = []

    def sync_from_router(self, router: Any | None) -> None:
        """Seed the overlay from the current singleton router when needed."""
        router_token = id(router) if router is not None else None
        if router_token == self._router_token:
            if router is not None:
                self._available_providers = sorted(router.adapters.keys())
            return

        self._seed_defaults()
        self._router_token = router_token

        if router is None:
            return

        self._available_providers = sorted(router.adapters.keys())
        self._daily_budget_usd = float(getattr(router, "daily_budget_usd", self._daily_budget_usd))
        self._routing_table = _normalize_routing_table(getattr(router, "routing_table", {}))

    def update(
        self,
        *,
        router: Any | None,
        daily_budget_usd: float,
        fallback_order: list[str],
        routing_table: dict[str, list[str]],
    ) -> None:
        """Apply a runtime-only overlay and mirror it into the live router."""
        self.sync_from_router(router)
        self._daily_budget_usd = float(daily_budget_usd)
        self._fallback_order = list(fallback_order)
        self._routing_table = _normalize_routing_table(routing_table)

        if router is not None:
            router.daily_budget_usd = float(daily_budget_usd)
            router.routing_table = {
                TaskType(task_name): list(providers)
                for task_name, providers in self._routing_table.items()
            }
            self._available_providers = sorted(router.adapters.keys())

    def snapshot(self, router: Any | None = None) -> dict[str, Any]:
        """Return the current runtime overlay as a plain serializable dict."""
        self.sync_from_router(router)
        return {
            "daily_budget_usd": self._daily_budget_usd,
            "fallback_order": deepcopy(self._fallback_order),
            "routing_table": deepcopy(self._routing_table),
            "available_providers": deepcopy(self._available_providers),
            "edit_mode": "runtime_only",
            "persists_across_restart": False,
        }


_brain_runtime_config: BrainRuntimeConfig | None = None


def get_brain_runtime_config() -> BrainRuntimeConfig:
    global _brain_runtime_config
    if _brain_runtime_config is None:
        _brain_runtime_config = BrainRuntimeConfig()
    return _brain_runtime_config


def reset_brain_runtime_config() -> BrainRuntimeConfig:
    global _brain_runtime_config
    _brain_runtime_config = BrainRuntimeConfig()
    return _brain_runtime_config
