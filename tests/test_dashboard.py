"""Tests for Dashboard API and Analytics Engine."""

from __future__ import annotations

import os
import time
from unittest.mock import patch

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


@pytest.mark.asyncio
async def test_validate_rtmp_target_uses_ffmpeg_helper(monkeypatch: pytest.MonkeyPatch) -> None:
    """RTMP validation should use shared FFmpeg readiness helper."""
    from src.dashboard.api import validate_rtmp_target

    monkeypatch.setenv("TIKTOK_RTMP_URL", "rtmp://push.example/live/")
    monkeypatch.setenv("TIKTOK_STREAM_KEY", "abc123")

    with patch(
        "src.dashboard.api.check_ffmpeg_ready",
        return_value={"available": True, "path": r"C:\tools\ffmpeg\bin\ffmpeg.exe"},
    ):
        result = await validate_rtmp_target()

    assert result["status"] == "pass"
    ffmpeg_check = next(c for c in result["checks"] if c["check"] == "ffmpeg_available")
    assert ffmpeg_check["passed"] is True


# === LiveTalking API requested/resolved Tests ===

@pytest.mark.asyncio
async def test_livetalking_status_api_has_requested_resolved() -> None:
    """GET /api/engine/livetalking/status must include requested/resolved fields."""
    from src.dashboard.api import engine_livetalking_status

    result = await engine_livetalking_status()

    assert "requested_model" in result, "status API missing requested_model"
    assert "resolved_model" in result, "status API missing resolved_model"
    assert "requested_avatar_id" in result, "status API missing requested_avatar_id"
    assert "resolved_avatar_id" in result, "status API missing resolved_avatar_id"


@pytest.mark.asyncio
async def test_livetalking_config_api_has_requested_resolved() -> None:
    """GET /api/engine/livetalking/config must include requested/resolved fields."""
    from src.dashboard.api import engine_livetalking_config

    result = await engine_livetalking_config()

    assert "requested_model" in result, "config API missing requested_model"
    assert "resolved_model" in result, "config API missing resolved_model"
    assert "requested_avatar_id" in result, "config API missing requested_avatar_id"
    assert "resolved_avatar_id" in result, "config API missing resolved_avatar_id"


# === Runtime Truth API Tests ===

@pytest.mark.asyncio
async def test_runtime_truth_endpoint_exists() -> None:
    """GET /api/runtime/truth must return consolidated truth."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    assert "mock_mode" in result
    assert "face_runtime_mode" in result
    assert "voice_runtime_mode" in result
    assert "stream_runtime_mode" in result
    assert "validation_state" in result
    assert "last_validated_at" in result
    assert "provenance" in result
    assert "timestamp" in result


@pytest.mark.asyncio
async def test_runtime_truth_mock_mode_reflects_env() -> None:
    """Truth endpoint must reflect actual MOCK_MODE from env."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    # We're running with MOCK_MODE=true in test env
    assert result["mock_mode"] is True


@pytest.mark.asyncio
async def test_runtime_truth_provenance_is_dict() -> None:
    """Truth provenance must be a dict with known keys."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    prov = result["provenance"]
    assert isinstance(prov, dict)
    assert "system_status" in prov
    assert "engine_status" in prov
    assert "stream_status" in prov


@pytest.mark.asyncio
async def test_runtime_truth_validation_state_valid() -> None:
    """Validation state must be one of the defined states."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    valid_states = {"unvalidated", "validating", "passed", "partial", "failed", "blocked"}
    assert result["validation_state"] in valid_states


@pytest.mark.asyncio
async def test_runtime_truth_exposes_ops_contract() -> None:
    """Runtime truth should expose server-hosted ops controller fields."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    assert "host" in result
    assert "deployment_mode" in result
    assert "incident_summary" in result
    assert "guardrails" in result


def test_incident_registry_tracks_open_incidents() -> None:
    """Incident registry should track unresolved incidents."""
    from src.dashboard.incidents import IncidentRegistry

    reg = IncidentRegistry()
    incident = reg.open("voice.timeout", "error", subsystem="voice")
    assert incident["resolved"] is False
    assert reg.summary()["open_count"] == 1


@pytest.mark.asyncio
async def test_ops_summary_exposes_resource_and_restart_state() -> None:
    """Ops summary should expose resource metrics and restart counters."""
    from src.dashboard.api import get_ops_summary

    result = await get_ops_summary()
    assert "resource_metrics" in result
    assert "restart_counters" in result


@pytest.mark.asyncio
async def test_voice_warmup_receipt_shape() -> None:
    """Voice warmup should return an explicit operator receipt."""
    from src.dashboard.api import voice_warmup

    result = await voice_warmup()
    assert result["status"] in {"success", "blocked", "error"}
    assert "message" in result


@pytest.mark.asyncio
async def test_voice_test_speak_receipt_shape() -> None:
    """Voice test speak should return an explicit operator receipt."""
    from src.dashboard.api import voice_test_speak

    result = await voice_test_speak(text="halo operator")
    assert result["status"] in {"success", "blocked", "error"}
    assert "message" in result
    assert "text" in result
    assert result["text"] == "halo operator"


def test_products_api_exposes_affiliate_fields() -> None:
    """Products API should expose affiliate-friendly fields."""
    import asyncio
    from src.dashboard.api import list_products

    result = asyncio.run(list_products())
    if len(result) > 0:
        first = result[0]
        assert "affiliate_links" in first
        assert "selling_points" in first
        assert "commission_rate" in first
        assert "objection_handling" in first
        assert "compliance_notes" in first


@pytest.mark.asyncio
async def test_audio_chunking_smoke_endpoint_shape() -> None:
    """Audio chunking smoke endpoint should return validation receipt shape."""
    from src.dashboard.api import validate_audio_chunking_smoke

    result = await validate_audio_chunking_smoke()
    assert result["status"] in {"pass", "fail", "blocked", "error"}
    assert "checks" in result


# === Validation History Tests ===

def test_validation_history_record_and_retrieve() -> None:
    """Validation history should record and retrieve entries."""
    from src.dashboard.validation_history import record_validation, get_history, clear_history

    clear_history()
    entry = record_validation("test-check", "pass", [{"check": "test", "passed": True, "message": "ok"}], provenance="mock")
    assert entry["check_name"] == "test-check"
    assert entry["status"] == "pass"
    assert "id" in entry
    assert "timestamp" in entry

    history = get_history(limit=10)
    assert len(history) >= 1
    assert history[0]["check_name"] == "test-check"
    clear_history()


def test_validation_history_respects_limit() -> None:
    """get_history should respect limit parameter."""
    from src.dashboard.validation_history import record_validation, get_history, clear_history

    clear_history()
    for i in range(5):
        record_validation(f"check-{i}", "pass", [], provenance="mock")

    history = get_history(limit=3)
    assert len(history) == 3
    clear_history()


def test_validation_history_reverse_chronological() -> None:
    """History entries should be in reverse chronological order."""
    from src.dashboard.validation_history import record_validation, get_history, clear_history
    import time

    clear_history()
    record_validation("first", "pass", [], provenance="mock")
    time.sleep(0.01)
    record_validation("second", "pass", [], provenance="mock")

    history = get_history(limit=10)
    assert history[0]["check_name"] == "second"
    assert history[1]["check_name"] == "first"
    clear_history()


@pytest.mark.asyncio
async def test_validate_runtime_truth_endpoint() -> None:
    """POST /api/validate/runtime-truth should return checks with evidence."""
    from src.dashboard.api import validate_runtime_truth

    result = await validate_runtime_truth()
    assert result["status"] in ("pass", "fail", "error")
    assert "checks" in result
    assert "evidence_id" in result


@pytest.mark.asyncio
async def test_validate_real_mode_readiness_endpoint() -> None:
    """POST /api/validate/real-mode-readiness should return checks with blockers."""
    from src.dashboard.api import validate_real_mode_readiness

    result = await validate_real_mode_readiness()
    assert result["status"] in ("pass", "blocked", "error")
    assert "checks" in result
    assert "blockers" in result


@pytest.mark.asyncio
async def test_validation_history_endpoint() -> None:
    """GET /api/validation/history should return list."""
    from src.dashboard.api import validation_history

    result = await validation_history()
    assert isinstance(result, list)


# === Product Hydration + Readiness Contract Tests ===


def test_product_manager_load_from_json() -> None:
    """ProductManager.load_from_json() should hydrate products from canonical file."""
    from src.commerce.manager import ProductManager

    pm = ProductManager()
    count = pm.load_from_json()

    assert count > 0, "data/products.json should load at least one product"
    assert len(pm.get_all_active()) == count
    first = pm.get_all_active()[0]
    assert first.name != "", "loaded product must have a name"
    assert first.price > 0, "loaded product must have a positive price"


def test_product_manager_load_from_missing_file(tmp_path) -> None:
    """ProductManager.load_from_json() should return 0 for missing file."""
    from pathlib import Path
    from src.commerce.manager import ProductManager

    pm = ProductManager()
    count = pm.load_from_json(path=tmp_path / "nonexistent.json")

    assert count == 0
    assert len(pm.get_all_active()) == 0


def test_app_startup_hydrates_products() -> None:
    """After create_app(), the dashboard product manager must have products loaded."""
    from src.main import create_app
    import src.dashboard.api as dashboard_api

    create_app()

    pm = dashboard_api._product_manager
    assert pm is not None, "dashboard must have a product manager"
    products = pm.get_all_active()
    assert len(products) > 0, (
        "After app startup, ProductManager must be hydrated from data/products.json"
    )


@pytest.mark.asyncio
async def test_api_products_returns_hydrated_data() -> None:
    """GET /api/products must return products from hydrated manager, not empty."""
    from src.main import create_app
    from src.dashboard.api import list_products

    create_app()
    result = await list_products()

    assert isinstance(result, list)
    assert len(result) > 0, "/api/products must return non-empty after app startup"
    assert "name" in result[0]
    assert "price" in result[0]


@pytest.mark.asyncio
async def test_api_real_mode_readiness_products_pass_after_hydration() -> None:
    """After app startup with data/products.json, real-mode-readiness must not fail on products."""
    from src.main import create_app
    from src.dashboard.api import validate_real_mode_readiness

    create_app()
    result = await validate_real_mode_readiness()

    product_source = next(
        (c for c in result["checks"] if c["check"] == "product_data_source"), None
    )
    products_loaded = next(
        (c for c in result["checks"] if c["check"] == "products_loaded"), None
    )

    assert product_source is not None, "readiness must check product_data_source"
    assert product_source["passed"] is True, "data/products.json must exist"
    assert products_loaded is not None, "readiness must check products_loaded"
    assert products_loaded["passed"] is True, (
        "products must be loaded into runtime after app startup"
    )


@pytest.mark.asyncio
async def test_runtime_truth_has_face_engine_fields() -> None:
    """Runtime truth must include face_engine with requested/resolved fields."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    assert "face_engine" in result, "truth must include face_engine"
    fe = result["face_engine"]
    assert "requested_model" in fe
    assert "resolved_model" in fe
    assert "requested_avatar_id" in fe
    assert "resolved_avatar_id" in fe
    assert "fallback_active" in fe
    assert isinstance(fe["fallback_active"], bool)


@pytest.mark.asyncio
async def test_health_summary_face_pipeline_healthy_with_ready_prerequisites(monkeypatch) -> None:
    """Health summary should report healthy face_pipeline on readiness-complete non-mock local setup."""
    monkeypatch.setenv("MOCK_MODE", "false")
    from src.main import create_app
    from src.dashboard.api import health_summary

    create_app()
    result = await health_summary()

    assert "components" in result
    assert result["components"].get("face_pipeline") == "healthy"


@pytest.mark.asyncio
async def test_runtime_truth_face_mode_not_mock_when_mock_false(monkeypatch) -> None:
    """When MOCK_MODE=false, face_runtime_mode must NOT be 'mock'."""
    monkeypatch.setenv("MOCK_MODE", "false")

    from src.dashboard.truth import _get_face_runtime_mode
    mode = _get_face_runtime_mode()

    assert mode != "mock", (
        f"face_runtime_mode must not be 'mock' when MOCK_MODE=false, got '{mode}'"
    )
    assert "livetalking" in mode, (
        f"face_runtime_mode should indicate livetalking state, got '{mode}'"
    )


# === Voice Engine Runtime Truth Tests ===


@pytest.mark.asyncio
async def test_runtime_truth_has_voice_engine_fields() -> None:
    """Runtime truth must include voice_engine with requested/resolved fields."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()

    assert "voice_engine" in result, "truth must include voice_engine"
    ve = result["voice_engine"]
    assert "requested_engine" in ve
    assert "resolved_engine" in ve
    assert "fallback_active" in ve
    assert "server_reachable" in ve
    assert "reference_ready" in ve
    assert "last_latency_ms" in ve
    assert "last_error" in ve
    assert isinstance(ve["fallback_active"], bool)


@pytest.mark.asyncio
async def test_runtime_truth_voice_mode_is_mock_in_mock_mode() -> None:
    """When MOCK_MODE=true, voice_runtime_mode must be 'mock'."""
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()
    assert result["voice_runtime_mode"] == "mock"


@pytest.mark.asyncio
async def test_runtime_truth_voice_mode_not_mock_when_mock_false(monkeypatch) -> None:
    """When MOCK_MODE=false, voice_runtime_mode must NOT be 'mock'."""
    monkeypatch.setenv("MOCK_MODE", "false")

    from src.dashboard.truth import _get_voice_runtime_mode
    mode = _get_voice_runtime_mode()

    assert mode != "mock", (
        f"voice_runtime_mode must not be 'mock' when MOCK_MODE=false, got '{mode}'"
    )
    valid_modes = {"fish_speech_local", "edge_tts_fallback", "voice_error", "unknown"}
    assert mode in valid_modes, f"voice_runtime_mode must be one of {valid_modes}, got '{mode}'"


def test_runtime_truth_voice_mode_unknown_until_engine_is_resolved(monkeypatch) -> None:
    """Non-mock runtime truth must not claim Fish-Speech is active before first resolution."""
    monkeypatch.setenv("MOCK_MODE", "false")

    from src.dashboard.truth import _get_voice_runtime_mode
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state

    reset_voice_runtime_state()
    state = get_voice_runtime_state()
    state.resolved_engine = "unknown"
    state.fallback_active = False
    state.server_reachable = False
    state.reference_ready = False
    state.last_error = None

    assert _get_voice_runtime_mode() == "unknown"
    reset_voice_runtime_state()


@pytest.mark.asyncio
async def test_validate_voice_local_clone_endpoint_exists() -> None:
    """POST /api/validate/voice-local-clone must return a valid response."""
    from src.dashboard.api import validate_voice_local_clone

    result = await validate_voice_local_clone()
    assert result["status"] in ("pass", "fail", "blocked", "error")
    assert "checks" in result


def test_readiness_includes_voice_checks() -> None:
    """Readiness checks must include voice clone readiness."""
    from src.dashboard.readiness import run_readiness_checks

    result = run_readiness_checks()
    check_names = [c.name for c in result.checks]
    assert "voice_reference_wav_ready" in check_names
    assert "voice_reference_text_ready" in check_names
    assert "fish_speech_server_reachable" in check_names
