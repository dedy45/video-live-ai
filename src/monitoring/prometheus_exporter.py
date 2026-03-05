"""Prometheus Exporter for AI Live Commerce Platform.

Exposes internal analytics metrics to Prometheus format on `/metrics` endpoint.
Requirements: 13.6
"""

from __future__ import annotations

import time

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from src.commerce.analytics import get_analytics
from src.utils.health import get_health_manager

router = APIRouter(tags=["monitoring"])


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> str:
    """Export metrics in Prometheus text format."""
    analytics = get_analytics()
    lines = []

    # 1. Counters
    counters = analytics.get_counters()
    for name, value in counters.items():
        metric = f"videoliveai_{name}_total"
        lines.append(f"# HELP {metric} Total count of {name}")
        lines.append(f"# TYPE {metric} counter")
        lines.append(f"{metric} {value}")

    # 2. Gauges
    gauges = analytics.get_gauges()
    for name, value in gauges.items():
        metric = f"videoliveai_{name}"
        lines.append(f"# HELP {metric} Current value of {name}")
        lines.append(f"# TYPE {metric} gauge")
        lines.append(f"{metric} {value}")

    # 3. Latency
    latency = analytics.get_all_latency_stats(window_sec=60.0)
    for op_name, stats in latency.items():
        safe_name = op_name.replace("-", "_")
        for stat_type, value in stats.items():
            if stat_type in ("avg", "p50", "p95", "max", "count"):
                metric = f"videoliveai_latency_ms_{stat_type}"
                lines.append(f'{metric}{{operation="{safe_name}"}} {value}')

    # 4. System Health
    hm = get_health_manager()
    status = 1 if hm.overall_status == "healthy" else (0 if hm.overall_status == "failed" else 0.5)
    lines.append("# HELP videoliveai_up Overall system health (1=healthy, 0=failed, 0.5=degraded)")
    lines.append("# TYPE videoliveai_up gauge")
    lines.append(f"videoliveai_up {status}")

    return "\n".join(lines) + "\n"
