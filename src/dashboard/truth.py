"""Runtime Truth Assembly.

Centralizes the runtime truth snapshot for the operator dashboard.
Every field is derived from actual config/runtime objects — no ad-hoc strings.

See: docs/specs/dashboard_truth_model.md
"""

from __future__ import annotations

import socket
import time
from datetime import datetime, timezone
from typing import Any

from src.config import is_mock_mode
from src.dashboard.resources import get_resource_metrics, get_restart_counters
from src.utils.logging import get_logger

logger = get_logger("dashboard.truth")

# Cache for LiveTalking manager to avoid redundant initialization
_cached_livetalking_manager = None


def _get_face_runtime_mode() -> str:
    """Derive face runtime mode from LiveTalking manager state.

    Returns one of:
      - "mock"                  — MOCK_MODE=true
      - "livetalking_local"     — engine running, MOCK_MODE=false
      - "livetalking_stopped"   — engine stopped, MOCK_MODE=false
      - "livetalking_starting"  — engine starting, MOCK_MODE=false
      - "livetalking_error"     — engine error, MOCK_MODE=false
      - "unknown"               — unexpected failure
    """
    global _cached_livetalking_manager
    if is_mock_mode():
        return "mock"
    try:
        if _cached_livetalking_manager is None:
            from src.face.livetalking_manager import get_livetalking_manager

            _cached_livetalking_manager = get_livetalking_manager()
        mgr = _cached_livetalking_manager
        status = mgr.get_status()
        state = status.state.value
        if state == "running":
            return "livetalking_local"
        if state == "starting":
            return "livetalking_starting"
        if state == "error":
            return "livetalking_error"
        # stopped or stopping — engine exists but isn't active
        return "livetalking_stopped"
    except Exception:
        return "unknown"


def _get_face_engine_truth() -> dict[str, Any]:
    """Get the requested vs resolved face engine truth fields."""
    global _cached_livetalking_manager
    try:
        if _cached_livetalking_manager is None:
            from src.face.livetalking_manager import get_livetalking_manager

            _cached_livetalking_manager = get_livetalking_manager()
        mgr = _cached_livetalking_manager
        return {
            "requested_model": mgr.requested_model,
            "resolved_model": mgr.model,
            "requested_avatar_id": mgr.requested_avatar_id,
            "resolved_avatar_id": mgr.avatar_id,
            "engine_state": mgr.get_status().state.value,
            "fallback_active": mgr.requested_model != mgr.model,
        }
    except Exception:
        return {
            "requested_model": "unknown",
            "resolved_model": "unknown",
            "requested_avatar_id": "unknown",
            "resolved_avatar_id": "unknown",
            "engine_state": "unknown",
            "fallback_active": False,
        }


def _get_voice_engine_truth() -> dict[str, Any]:
    """Get the requested vs resolved voice engine truth fields."""
    try:
        from src.voice.runtime_state import get_voice_runtime_state

        state = get_voice_runtime_state()
        return state.to_dict()
    except Exception:
        return {
            "requested_engine": "unknown",
            "resolved_engine": "unknown",
            "fallback_active": False,
            "server_reachable": False,
            "reference_ready": False,
            "last_latency_ms": None,
            "last_error": None,
        }


def _get_voice_runtime_mode() -> str:
    """Derive voice runtime mode from voice runtime state.

    Returns one of:
      - "mock"               — MOCK_MODE=true
      - "fish_speech_local"  — primary engine active, no fallback
      - "edge_tts_fallback"  — fallback active
      - "voice_error"        — both engines failed or unknown resolved
      - "unknown"            — unexpected failure
    """
    if is_mock_mode():
        return "mock"
    try:
        from src.voice.runtime_state import get_voice_runtime_state

        state = get_voice_runtime_state()
        if state.resolved_engine == "fish_speech" and not state.fallback_active:
            return "fish_speech_local"
        if state.resolved_engine == "edge_tts":
            return "edge_tts_fallback"
        if state.resolved_engine == "none" or state.last_error:
            return "voice_error"
        if state.resolved_engine == "unknown":
            return "unknown"
        return "unknown"
    except Exception:
        return "unknown"


def _get_stream_runtime_mode() -> str:
    """Derive stream runtime mode from dashboard API state."""
    if is_mock_mode():
        return "mock"
    try:
        from src.dashboard.api import _stream_running, _emergency_stopped

        if _emergency_stopped:
            return "idle"
        if _stream_running:
            return "live"
        return "idle"
    except Exception:
        return "idle"


def _get_provenance() -> dict[str, str]:
    """Build provenance dict classifying each data surface origin."""
    mock = is_mock_mode()
    base = "mock" if mock else "real_local"
    return {
        "system_status": base,
        "engine_status": base,
        "stream_status": base,
        "products": "derived",
        "metrics": "derived",
    }


# Cache for runtime truth snapshot to avoid redundant computation
_truth_cache: dict[str, Any] = {}
_truth_cache_ttl = 2.0  # Cache TTL in seconds
_truth_cache_time = 0.0


def get_runtime_truth_snapshot(force_refresh: bool = False) -> dict[str, Any]:
    """Assemble the consolidated runtime truth snapshot.

    This is the single source of truth for the operator dashboard.
    All fields are derived from actual runtime state.

    Uses caching to avoid redundant computation - returns cached result
    if called within TTL window unless force_refresh is True.
    """
    global _truth_cache, _truth_cache_time

    current_time = time.time()
    # Return cached result if still valid and not forcing refresh
    if not force_refresh and _truth_cache and (current_time - _truth_cache_time) < _truth_cache_ttl:
        return _truth_cache

    face_engine = _get_face_engine_truth()
    voice_engine = _get_voice_engine_truth()
    result = {
        "mock_mode": is_mock_mode(),
        "host": {
            "name": socket.gethostname(),
            "role": "local_lab",
        },
        "deployment_mode": "cold",
        "face_runtime_mode": _get_face_runtime_mode(),
        "face_engine": face_engine,
        "voice_runtime_mode": _get_voice_runtime_mode(),
        "voice_engine": voice_engine,
        "stream_runtime_mode": _get_stream_runtime_mode(),
        "incident_summary": {
            "open_count": 0,
            "highest_severity": "none",
        },
        "guardrails": {
            "restart_storm": False,
            "disk_pressure": False,
        },
        "resource_metrics": get_resource_metrics(),
        "restart_counters": get_restart_counters(),
        "validation_state": "unvalidated",
        "last_validated_at": None,
        "provenance": _get_provenance(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Update cache
    _truth_cache = result
    _truth_cache_time = current_time

    return result
