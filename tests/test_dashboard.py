"""Tests for Dashboard API and Analytics Engine."""

from __future__ import annotations

import os
import time

import pytest

os.environ["MOCK_MODE"] = "true"


# === Analytics Engine Tests ===

def test_analytics_record_latency() -> None:
    """Analytics should record and aggregate latency."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    for i in range(10):
        engine.record_latency("llm.gemini", 50.0 + i * 10)

    stats = engine.get_latency_stats("llm.gemini")
    assert stats.count == 10
    assert stats.mean > 0
    assert stats.p50 > 0
    assert stats.p95 > stats.p50


def test_analytics_revenue() -> None:
    """Analytics should track revenue per platform."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.record_revenue(50000, "tiktok")
    engine.record_revenue(30000, "shopee")
    engine.record_revenue(20000, "tiktok")

    summary = engine.get_revenue_summary(3600)
    assert summary["tiktok"] == 70000
    assert summary["shopee"] == 30000
    assert summary["total"] == 100000


def test_analytics_counters() -> None:
    """Analytics should count events."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.record_event("chat_message")
    engine.record_event("chat_message")
    engine.record_event("product_switch")

    counters = engine.get_counters()
    assert counters["chat_message"] == 2
    assert counters["product_switch"] == 1


def test_analytics_gauges() -> None:
    """Analytics should track gauge values."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.set_gauge("viewers", 150)
    engine.set_gauge("gpu_usage", 72.5)

    gauges = engine.get_gauges()
    assert gauges["viewers"] == 150
    assert gauges["gpu_usage"] == 72.5


def test_analytics_dashboard_snapshot() -> None:
    """Analytics should produce a complete dashboard snapshot."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.record_latency("brain", 100)
    engine.record_revenue(5000, "tiktok")
    engine.record_event("sale")
    engine.set_gauge("viewers", 42)

    snap = engine.get_dashboard_snapshot()
    assert "uptime_sec" in snap
    assert "latency" in snap
    assert "revenue" in snap
    assert "counters" in snap
    assert "gauges" in snap


def test_analytics_llm_usage() -> None:
    """Analytics should track LLM usage (tokens, cost, latency)."""
    from src.commerce.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    engine.record_llm_usage("gemini", 150, 0.001, 85.0)
    engine.record_llm_usage("claude", 500, 0.01, 200.0)

    latency = engine.get_all_latency_stats(60.0)
    assert "llm.gemini" in latency
    assert "llm.claude" in latency


def test_analytics_window_filtering() -> None:
    """Analytics should filter by time window."""
    from src.commerce.analytics import MetricBuffer, MetricPoint

    buf = MetricBuffer()
    # Add an old point (60+ seconds ago)
    old = MetricPoint(name="test", value=999.0, timestamp=time.time() - 120)
    buf.add(old)
    # Add a fresh point
    buf.add(MetricPoint(name="test", value=100.0))

    window = buf.get_window(60.0)
    assert len(window) == 1
    assert window[0] == 100.0


# === Dashboard API Tests ===

def test_dashboard_state_init() -> None:
    """Dashboard state should initialize."""
    from src.dashboard.api import init_dashboard_state
    from src.commerce.manager import ProductManager, AffiliateTracker

    pm = ProductManager()
    at = AffiliateTracker()
    # Should not raise
    init_dashboard_state(pm, at)


def test_dashboard_record_chat() -> None:
    """Dashboard should record chat events."""
    from src.dashboard.api import record_chat_event, _recent_chats

    initial = len(_recent_chats)
    record_chat_event({
        "platform": "tiktok",
        "username": "test_user",
        "message": "Mau beli!",
        "intent": "purchase",
        "priority": 1,
        "timestamp": time.time(),
    })
    assert len(_recent_chats) > initial


def test_analytics_singleton() -> None:
    """Analytics should be a singleton."""
    from src.commerce.analytics import get_analytics

    a1 = get_analytics()
    a2 = get_analytics()
    assert a1 is a2
