"""Analytics Engine — Real-time metrics collection and aggregation.

Collects viewer, revenue, latency, and conversion metrics.
60-second aggregation window with P50/P95 percentile tracking.
Requirements: 8.4, 8.5, 11.6
"""

from __future__ import annotations

import statistics
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from src.utils.logging import get_logger

logger = get_logger("analytics")


@dataclass
class MetricPoint:
    """Single metric data point."""

    name: str
    value: float
    timestamp: float = 0.0
    tags: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp == 0.0:
            self.timestamp = time.time()


@dataclass
class AggregatedMetrics:
    """Metrics aggregated over a time window."""

    window_start: float
    window_end: float
    count: int = 0
    mean: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    p50: float = 0.0
    p95: float = 0.0
    total: float = 0.0


class MetricBuffer:
    """Ring buffer for storing recent metric values."""

    def __init__(self, max_size: int = 1000) -> None:
        self._values: deque[MetricPoint] = deque(maxlen=max_size)

    def add(self, point: MetricPoint) -> None:
        self._values.append(point)

    def get_window(self, window_sec: float = 60.0) -> list[float]:
        """Get values within the last N seconds."""
        cutoff = time.time() - window_sec
        return [p.value for p in self._values if p.timestamp >= cutoff]

    def aggregate(self, window_sec: float = 60.0) -> AggregatedMetrics:
        """Aggregate metrics over a time window."""
        values = self.get_window(window_sec)
        now = time.time()

        if not values:
            return AggregatedMetrics(window_start=now - window_sec, window_end=now)

        sorted_vals = sorted(values)
        n = len(sorted_vals)
        p50_idx = max(0, int(n * 0.50) - 1)
        p95_idx = max(0, int(n * 0.95) - 1)

        return AggregatedMetrics(
            window_start=now - window_sec,
            window_end=now,
            count=n,
            mean=statistics.mean(values),
            min_val=min(values),
            max_val=max(values),
            p50=sorted_vals[p50_idx],
            p95=sorted_vals[p95_idx],
            total=sum(values),
        )

    @property
    def size(self) -> int:
        return len(self._values)


class AnalyticsEngine:
    """Central analytics engine for all system metrics.

    Tracks:
    - Viewer metrics (count, peak, join rate)
    - Revenue metrics (sales, commission, conversion)
    - Technical metrics (latency, FPS, GPU usage, errors)
    - LLM metrics (tokens, cost, provider usage)
    """

    def __init__(self) -> None:
        self._buffers: dict[str, MetricBuffer] = {}
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._session_start = time.time()
        logger.info("analytics_engine_init")

    def _get_buffer(self, name: str) -> MetricBuffer:
        if name not in self._buffers:
            self._buffers[name] = MetricBuffer()
        return self._buffers[name]

    # ── Recording ────────────────────────────────────────────────

    def record_latency(self, component: str, latency_ms: float) -> None:
        """Record a latency measurement."""
        self._get_buffer(f"latency.{component}").add(
            MetricPoint(f"latency.{component}", latency_ms)
        )

    def record_event(self, event_type: str) -> None:
        """Increment an event counter."""
        self._counters[event_type] = self._counters.get(event_type, 0) + 1

    def record_revenue(self, amount: float, platform: str = "tiktok") -> None:
        """Record revenue."""
        self._get_buffer(f"revenue.{platform}").add(
            MetricPoint(f"revenue.{platform}", amount)
        )
        self.record_event(f"sale.{platform}")

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge value (point-in-time metric)."""
        self._gauges[name] = value

    def record_llm_usage(self, provider: str, tokens: int, cost_usd: float, latency_ms: float) -> None:
        """Record LLM usage."""
        self.record_latency(f"llm.{provider}", latency_ms)
        self._get_buffer(f"tokens.{provider}").add(
            MetricPoint(f"tokens.{provider}", float(tokens))
        )
        self._get_buffer(f"cost.{provider}").add(
            MetricPoint(f"cost.{provider}", cost_usd)
        )

    # ── Querying ─────────────────────────────────────────────────

    def get_latency_stats(self, component: str, window_sec: float = 60.0) -> AggregatedMetrics:
        """Get latency stats for a component."""
        return self._get_buffer(f"latency.{component}").aggregate(window_sec)

    def get_all_latency_stats(self, window_sec: float = 60.0) -> dict[str, dict[str, float]]:
        """Get latency stats for all tracked components."""
        result: dict[str, dict[str, float]] = {}
        for name, buf in self._buffers.items():
            if name.startswith("latency."):
                component = name.replace("latency.", "")
                agg = buf.aggregate(window_sec)
                if agg.count > 0:
                    result[component] = {
                        "count": agg.count,
                        "mean_ms": round(agg.mean, 1),
                        "p50_ms": round(agg.p50, 1),
                        "p95_ms": round(agg.p95, 1),
                        "min_ms": round(agg.min_val, 1),
                        "max_ms": round(agg.max_val, 1),
                    }
        return result

    def get_revenue_summary(self, window_sec: float = 3600.0) -> dict[str, float]:
        """Get revenue summary for the last N seconds."""
        result: dict[str, float] = {"total": 0.0}
        for name, buf in self._buffers.items():
            if name.startswith("revenue."):
                platform = name.replace("revenue.", "")
                agg = buf.aggregate(window_sec)
                result[platform] = round(agg.total, 2)
                result["total"] += agg.total
        result["total"] = round(result["total"], 2)
        return result

    def get_counters(self) -> dict[str, int]:
        """Get all event counters."""
        return dict(self._counters)

    def get_gauges(self) -> dict[str, float]:
        """Get all current gauge values."""
        return dict(self._gauges)

    def get_dashboard_snapshot(self) -> dict[str, Any]:
        """Get a complete snapshot for the dashboard."""
        uptime = time.time() - self._session_start
        return {
            "uptime_sec": round(uptime, 0),
            "latency": self.get_all_latency_stats(60.0),
            "revenue": self.get_revenue_summary(3600.0),
            "counters": self.get_counters(),
            "gauges": self.get_gauges(),
        }


# Global singleton
_analytics: AnalyticsEngine | None = None


def get_analytics() -> AnalyticsEngine:
    """Get or create the global analytics engine."""
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsEngine()
    return _analytics
