"""Dashboard Readiness Checks.

Provides a consolidated readiness checklist for the operator dashboard.
Answers "is the system ready to go live?" from one endpoint.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import get_config, is_mock_mode
from src.data.database import check_database_health
from src.face.engine_resolver import resolve_avatar_id, resolve_engine
from src.utils.ffmpeg import check_ffmpeg_ready
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
    config = None

    # 1. Config loaded
    try:
        config = get_config()
        checks.append(
            ReadinessCheck(
                name="config_loaded",
                passed=True,
                status="ok",
                message=f"{config.app.name} v{config.app.version}",
            )
        )
    except Exception as e:
        checks.append(
            ReadinessCheck(
                name="config_loaded",
                passed=False,
                status="fail",
                message=str(e),
                blocking=True,
            )
        )
        blocking.append("Config failed to load")

    # 2. Database healthy
    try:
        db_health = check_database_health()
        db_ok = db_health.get("healthy", False)
        checks.append(
            ReadinessCheck(
                name="database_healthy",
                passed=db_ok,
                status="ok" if db_ok else "fail",
                message=str(db_health.get("message", "")),
                blocking=not db_ok,
            )
        )
        if not db_ok:
            blocking.append("Database is not healthy")
    except Exception as e:
        checks.append(
            ReadinessCheck(
                name="database_healthy",
                passed=False,
                status="fail",
                message=str(e),
                blocking=True,
            )
        )
        blocking.append(f"Database check failed: {e}")

    # 3. LiveTalking installed
    lt_path = Path("external/livetalking")
    app_py = lt_path / "app.py"
    lt_installed = app_py.exists()
    checks.append(
        ReadinessCheck(
            name="livetalking_installed",
            passed=lt_installed,
            status="ok" if lt_installed else "fail",
            message=str(app_py) if lt_installed else "app.py not found",
            blocking=not lt_installed,
        )
    )
    if not lt_installed:
        blocking.append("LiveTalking not installed (run: git submodule update --init)")

    # 3b. Avatar reference assets (video + audio)
    ref_video = Path("assets/avatar/reference.mp4")
    ref_audio = Path("assets/avatar/reference.wav")
    ref_video_ok = ref_video.exists()
    ref_audio_ok = ref_audio.exists()
    checks.append(
        ReadinessCheck(
            name="avatar_reference_video",
            passed=ref_video_ok,
            status="ok" if ref_video_ok else "fail",
            message=str(ref_video) if ref_video_ok else "reference.mp4 not found",
            blocking=not ref_video_ok,
        )
    )
    if not ref_video_ok:
        blocking.append("Avatar reference video missing: assets/avatar/reference.mp4")
    checks.append(
        ReadinessCheck(
            name="avatar_reference_audio",
            passed=ref_audio_ok,
            status="ok" if ref_audio_ok else "fail",
            message=str(ref_audio)
            if ref_audio_ok
            else "reference.wav not found (extract from reference.mp4 with ffmpeg -i reference.mp4 -vn -ar 16000 -ac 1 reference.wav)",
            blocking=not ref_audio_ok,
        )
    )
    if not ref_audio_ok:
        blocking.append("Avatar reference audio missing: assets/avatar/reference.wav")

    default_model = config.avatar.livetalking.model if config else "musetalk"
    default_avatar_id = config.avatar.livetalking.avatar_id if config else "musetalk_avatar1"
    requested_model = os.getenv("LIVETALKING_MODEL", default_model)
    requested_avatar_id = os.getenv("LIVETALKING_AVATAR_ID", default_avatar_id)
    resolved_model = resolve_engine(
        requested_model,
        musetalk_model_dir=lt_path / "models" / "musetalk",
        musetalk_avatar_dir=lt_path / "data" / "avatars" / requested_avatar_id,
    )
    resolved_avatar_id = resolve_avatar_id(
        requested_avatar_id,
        resolved_model,
        avatars_dir=lt_path / "data" / "avatars",
    )

    # 4. LiveTalking model ready
    if resolved_model == "wav2lip":
        model_path = lt_path / "models" / "wav2lip.pth"
    elif resolved_model == "musetalk":
        model_path = lt_path / "models" / "musetalk"
    else:
        model_path = lt_path / "models"
    model_ready = model_path.exists()
    model_status = "ok" if model_ready and requested_model == resolved_model else "warning"
    model_message = f"{resolved_model}: {model_path}"
    if requested_model != resolved_model:
        model_message = f"requested={requested_model}, resolved={resolved_model}: {model_path}"
    checks.append(
        ReadinessCheck(
            name="livetalking_model_ready",
            passed=model_ready,
            status=model_status if model_ready else "warning",
            message=model_message if model_ready else f"Model not found: {model_path}",
        )
    )

    # 5. LiveTalking avatar ready
    avatar_path = lt_path / "data" / "avatars" / resolved_avatar_id
    avatar_ready = avatar_path.exists()
    avatar_status = (
        "ok" if avatar_ready and requested_avatar_id == resolved_avatar_id else "warning"
    )
    avatar_message = f"{resolved_avatar_id}: {avatar_path}"
    if requested_avatar_id != resolved_avatar_id:
        avatar_message = (
            f"requested={requested_avatar_id}, resolved={resolved_avatar_id}: {avatar_path}"
        )
    checks.append(
        ReadinessCheck(
            name="livetalking_avatar_ready",
            passed=avatar_ready,
            status=avatar_status if avatar_ready else "warning",
            message=avatar_message if avatar_ready else f"Avatar not found: {avatar_path}",
        )
    )

    # 6. FFmpeg available
    ffmpeg_status = check_ffmpeg_ready()
    ffmpeg_ok = bool(ffmpeg_status["available"])
    checks.append(
        ReadinessCheck(
            name="ffmpeg_available",
            passed=ffmpeg_ok,
            status="ok" if ffmpeg_ok else "warning",
            message=ffmpeg_status["path"] or "FFmpeg not found in PATH or known install locations",
        )
    )

    # 7. RTMP target configured
    rtmp_url = os.getenv("TIKTOK_RTMP_URL", "")
    stream_key = os.getenv("TIKTOK_STREAM_KEY", "")
    rtmp_configured = bool(rtmp_url and stream_key)
    checks.append(
        ReadinessCheck(
            name="rtmp_target_configured",
            passed=rtmp_configured,
            status="ok" if rtmp_configured else "warning",
            message="TikTok RTMP configured"
            if rtmp_configured
            else "No RTMP target configured (set TIKTOK_RTMP_URL + TIKTOK_STREAM_KEY)",
        )
    )

    # 8. Mock mode / production mode
    mock = is_mock_mode()
    checks.append(
        ReadinessCheck(
            name="mode_explicit",
            passed=True,
            status="ok",
            message=f"MOCK_MODE={'true' if mock else 'false'}",
        )
    )

    # 9. Voice clone reference WAV
    voice_cfg = config.voice if config else None
    voice_ref_wav = Path(
        voice_cfg.clone_reference_wav if voice_cfg else "assets/voice/reference.wav"
    )
    voice_wav_ok = voice_ref_wav.exists()
    checks.append(
        ReadinessCheck(
            name="voice_reference_wav_ready",
            passed=voice_wav_ok,
            status="ok" if voice_wav_ok else "warning",
            message=str(voice_ref_wav)
            if voice_wav_ok
            else f"Voice clone reference WAV not found: {voice_ref_wav}",
        )
    )

    # 10. Voice clone reference text
    voice_ref_txt = Path(
        voice_cfg.clone_reference_text if voice_cfg else "assets/voice/reference.txt"
    )
    voice_txt_ok = voice_ref_txt.exists()
    voice_txt_nonempty = False
    if voice_txt_ok:
        voice_txt_nonempty = len(voice_ref_txt.read_text(encoding="utf-8").strip()) > 0
    checks.append(
        ReadinessCheck(
            name="voice_reference_text_ready",
            passed=voice_txt_ok and voice_txt_nonempty,
            status="ok" if (voice_txt_ok and voice_txt_nonempty) else "warning",
            message=str(voice_ref_txt)
            if (voice_txt_ok and voice_txt_nonempty)
            else f"Voice clone reference text missing or empty: {voice_ref_txt}",
        )
    )

    # 11. Fish-Speech server reachable (non-blocking, advisory)
    # Use cached result if available to avoid blocking
    fish_speech_reachable = False
    fish_speech_url = voice_cfg.fish_speech_base_url if voice_cfg else "http://127.0.0.1:8080"

    # Try to get cached reachability state first (non-blocking)
    try:
        from src.voice.runtime_state import get_voice_runtime_state

        vrs = get_voice_runtime_state()
        if vrs.server_reachable is not None:
            fish_speech_reachable = vrs.server_reachable
        else:
            fish_speech_reachable = False
    except Exception:
        pass

    # Only do socket check if we don't have cached state
    if not fish_speech_reachable:
        try:
            import socket
            from urllib.parse import urlparse

            parsed = urlparse(fish_speech_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8080
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.5)  # Reduced timeout for faster failure
                fish_speech_reachable = sock.connect_ex((host, port)) == 0
        except Exception:
            pass
    checks.append(
        ReadinessCheck(
            name="fish_speech_server_reachable",
            passed=fish_speech_reachable,
            status="ok" if fish_speech_reachable else "warning",
            message=f"Fish-Speech at {fish_speech_url}"
            if fish_speech_reachable
            else f"Fish-Speech not reachable at {fish_speech_url} (start sidecar for real voice)",
        )
    )

    # Update voice runtime state with readiness info
    try:
        from src.voice.runtime_state import get_voice_runtime_state

        vrs = get_voice_runtime_state()
        vrs.server_reachable = fish_speech_reachable
        vrs.reference_ready = voice_wav_ok and voice_txt_ok and voice_txt_nonempty
    except Exception:
        pass

    # Determine overall status
    warnings = [c.name for c in checks if c.status == "warning"]
    soft_failures = [c.name for c in checks if not c.passed and not c.blocking]

    if blocking:
        overall = "not_ready"
        action = f"Fix blocking issues: {blocking[0]}"
    elif warnings or soft_failures:
        overall = "degraded"
        degraded_checks = warnings + [name for name in soft_failures if name not in warnings]
        action = f"Optional fixes: {', '.join(degraded_checks)}"
    elif all(c.passed for c in checks):
        overall = "ready"
        action = "System is ready. Start LiveTalking engine from dashboard."
    else:
        overall = "degraded"
        action = "Optional fixes: review readiness checks"

    return ReadinessResult(
        overall_status=overall,
        checks=checks,
        blocking_issues=blocking,
        recommended_next_action=action,
    )
