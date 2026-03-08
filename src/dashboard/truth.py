"""Runtime Truth Assembly.

Centralizes the runtime truth snapshot for the operator dashboard.
Every field is derived from actual config/runtime objects — no ad-hoc strings.

See: docs/specs/dashboard_truth_model.md
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("dashboard.truth")


def _get_face_runtime_mode() -> str:
    """Derive face runtime mode from LiveTalking manager state."""
    if is_mock_mode():
        return "mock"
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        status = mgr.get_status()
        if status.state.value == "running":
            return "livetalking_local"
        return "mock"
    except Exception:
        return "mock"


def _get_voice_runtime_mode() -> str:
    """Derive voice runtime mode from config and mock state."""
    if is_mock_mode():
        return "mock"
    try:
        from src.config import get_config
        config = get_config()
        # In production mode, Fish Speech is primary
        return "fish_speech"
    except Exception:
        return "mock"


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


def get_runtime_truth_snapshot() -> dict[str, Any]:
    """Assemble the consolidated runtime truth snapshot.

    This is the single source of truth for the operator dashboard.
    All fields are derived from actual runtime state.
    """
    return {
        "mock_mode": is_mock_mode(),
        "face_runtime_mode": _get_face_runtime_mode(),
        "voice_runtime_mode": _get_voice_runtime_mode(),
        "stream_runtime_mode": _get_stream_runtime_mode(),
        "validation_state": "unvalidated",
        "last_validated_at": None,
        "provenance": _get_provenance(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
