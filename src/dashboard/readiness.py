"""Dashboard Readiness Checks.

Provides a consolidated readiness checklist for the operator dashboard.
Answers "is the system ready to go live?" from one endpoint.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import get_config, is_mock_mode
from src.data.database import check_database_health
from src.utils.logging import get_logger

logger = get_logger("dashboard.readiness")


@dataclass
class ReadinessCheck:
    name: str
    passed: bool
    status: str  # ok | warning | fail
    message: str = ""
    blocking: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "passed": self.passed,
            "status": self.status,
            "message": self.message,
            "blocking": self.blocking,
        }


@dataclass
class ReadinessResult:
    overall_status: str  # ready | not_ready | degraded
    checks: list[ReadinessCheck] = field(default_factory=list)
    blocking_issues: list[str] = field(default_factory=list)
    recommended_next_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_status": self.overall_status,
            "checks": [c.to_dict() for c in self.checks],
            "blocking_issues": self.blocking_issues,
            "recommended_next_action": self.recommended_next_action,
        }


def run_readiness_checks() -> ReadinessResult:
    """Run all readiness checks and return consolidated result."""
    checks: list[ReadinessCheck] = []
    blocking: list[str] = []

    # 1. Config loaded
    try:
        config = get_config()
        checks.append(ReadinessCheck(
            name="config_loaded",
            passed=True,
            status="ok",
            message=f"{config.app.name} v{config.app.version}",
        ))
    except Exception as e:
        checks.append(ReadinessCheck(
            name="config_loaded",
            passed=False,
            status="fail",
            message=str(e),
            blocking=True,
        ))
        blocking.append("Config failed to load")

    # 2. Database healthy
    try:
        db_health = check_database_health()
        db_ok = db_health.get("healthy", False)
        checks.append(ReadinessCheck(
            name="database_healthy",
            passed=db_ok,
            status="ok" if db_ok else "fail",
            message=str(db_health.get("message", "")),
            blocking=not db_ok,
        ))
        if not db_ok:
            blocking.append("Database is not healthy")
    except Exception as e:
        checks.append(ReadinessCheck(
            name="database_healthy",
            passed=False,
            status="fail",
            message=str(e),
            blocking=True,
        ))
        blocking.append(f"Database check failed: {e}")

    # 3. LiveTalking installed
    lt_path = Path("external/livetalking")
    app_py = lt_path / "app.py"
    lt_installed = app_py.exists()
    checks.append(ReadinessCheck(
        name="livetalking_installed",
        passed=lt_installed,
        status="ok" if lt_installed else "fail",
        message=str(app_py) if lt_installed else "app.py not found",
        blocking=not lt_installed,
    ))
    if not lt_installed:
        blocking.append("LiveTalking not installed (run: git submodule update --init)")

    # 4. LiveTalking model ready
    model_name = os.getenv("LIVETALKING_MODEL", "wav2lip")
    if model_name == "wav2lip":
        model_path = lt_path / "models" / "wav2lip.pth"
    elif model_name == "musetalk":
        model_path = lt_path / "models" / "musetalk"
    else:
        model_path = lt_path / "models"
    model_ready = model_path.exists()
    checks.append(ReadinessCheck(
        name="livetalking_model_ready",
        passed=model_ready,
        status="ok" if model_ready else "warning",
        message=f"{model_name}: {model_path}" if model_ready else f"Model not found: {model_path}",
    ))

    # 5. LiveTalking avatar ready
    avatar_id = os.getenv("LIVETALKING_AVATAR_ID", "wav2lip256_avatar1")
    avatar_path = lt_path / "data" / "avatars" / avatar_id
    avatar_ready = avatar_path.exists()
    checks.append(ReadinessCheck(
        name="livetalking_avatar_ready",
        passed=avatar_ready,
        status="ok" if avatar_ready else "warning",
        message=f"{avatar_id}: {avatar_path}" if avatar_ready else f"Avatar not found: {avatar_path}",
    ))

    # 6. FFmpeg available
    ffmpeg_path = shutil.which("ffmpeg")
    ffmpeg_ok = ffmpeg_path is not None
    checks.append(ReadinessCheck(
        name="ffmpeg_available",
        passed=ffmpeg_ok,
        status="ok" if ffmpeg_ok else "warning",
        message=ffmpeg_path or "FFmpeg not found in PATH",
    ))

    # 7. RTMP target configured
    rtmp_url = os.getenv("TIKTOK_RTMP_URL", "")
    stream_key = os.getenv("TIKTOK_STREAM_KEY", "")
    rtmp_configured = bool(rtmp_url and stream_key)
    checks.append(ReadinessCheck(
        name="rtmp_target_configured",
        passed=rtmp_configured,
        status="ok" if rtmp_configured else "warning",
        message="TikTok RTMP configured" if rtmp_configured else "No RTMP target configured (set TIKTOK_RTMP_URL + TIKTOK_STREAM_KEY)",
    ))

    # 8. Mock mode / production mode
    mock = is_mock_mode()
    checks.append(ReadinessCheck(
        name="mode_explicit",
        passed=True,
        status="ok",
        message=f"MOCK_MODE={'true' if mock else 'false'}",
    ))

    # Determine overall status
    if blocking:
        overall = "not_ready"
        action = f"Fix blocking issues: {blocking[0]}"
    elif all(c.passed for c in checks):
        overall = "ready"
        action = "System is ready. Start LiveTalking engine from dashboard."
    else:
        overall = "degraded"
        warnings = [c.name for c in checks if not c.passed]
        action = f"Optional fixes: {', '.join(warnings)}"

    return ReadinessResult(
        overall_status=overall,
        checks=checks,
        blocking_issues=blocking,
        recommended_next_action=action,
    )
