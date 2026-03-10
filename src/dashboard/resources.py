from __future__ import annotations

from typing import Any


_restart_counters: dict[str, int] = {
    "voice": 0,
    "face": 0,
    "stream": 0,
}


def get_resource_metrics() -> dict[str, Any]:
    return {
        "cpu_pct": 0.0,
        "ram_pct": 0.0,
        "disk_pct": 0.0,
        "vram_pct": None,
    }


def get_restart_counters() -> dict[str, int]:
    return dict(_restart_counters)


def increment_restart_counter(component: str) -> None:
    _restart_counters[component] = _restart_counters.get(component, 0) + 1


def reset_restart_counters() -> None:
    for key in list(_restart_counters.keys()):
        _restart_counters[key] = 0
