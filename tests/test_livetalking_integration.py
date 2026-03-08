"""Tests for LiveTalking integration.

Run with:
    pytest tests/test_livetalking_integration.py -v
    pytest tests/test_livetalking_integration.py -v -m "not integration"  # Skip GPU tests
"""

from unittest.mock import patch

import pytest

from src.face.livetalking_adapter import LiveTalkingEngine, LiveTalkingPipeline
from src.face.pipeline import VideoFrame


@pytest.mark.asyncio
async def test_livetalking_engine_init():
    """Test LiveTalking engine initialization."""
    engine = LiveTalkingEngine(
        reference_video="assets/avatar/reference.mp4",
        reference_audio="assets/avatar/reference.wav",
        resolution=(512, 512),
        fps=30,
    )
    
    assert engine.resolution == (512, 512)
    assert engine.fps == 30
    assert not engine._initialized


@pytest.mark.asyncio
async def test_livetalking_engine_mock_mode(monkeypatch):
    """Test LiveTalking engine in mock mode."""
    # Force mock mode
    monkeypatch.setenv("MOCK_MODE", "true")
    
    engine = LiveTalkingEngine()
    
    # Initialize should succeed in mock mode
    success = await engine.initialize()
    assert success
    
    # Health check should pass
    health = await engine.health_check()
    assert health


@pytest.mark.asyncio
async def test_livetalking_generate_frames_mock(monkeypatch):
    """Test frame generation in mock mode."""
    monkeypatch.setenv("MOCK_MODE", "true")
    
    engine = LiveTalkingEngine(resolution=(256, 256), fps=30)
    await engine.initialize()
    
    # Generate frames from dummy audio
    audio_data = b"\x00" * 1000  # Dummy audio
    duration_ms = 1000.0  # 1 second
    
    frames = []
    async for frame in engine.generate_frames(audio_data, duration_ms, trace_id="test"):
        frames.append(frame)
        assert isinstance(frame, VideoFrame)
        assert frame.width == 256
        assert frame.height == 256
        assert frame.enhanced  # LiveTalking includes GFPGAN
        assert frame.trace_id == "test"
    
    # Should generate approximately 30 frames for 1 second at 30fps
    assert len(frames) > 0


@pytest.mark.asyncio
async def test_livetalking_pipeline_mock(monkeypatch):
    """Test complete LiveTalking pipeline in mock mode."""
    monkeypatch.setenv("MOCK_MODE", "true")
    
    pipeline = LiveTalkingPipeline()
    
    # Health check
    health = await pipeline.health_check()
    assert health
    
    # Render frames
    audio_data = b"\x00" * 1000
    duration_ms = 500.0
    
    frames = []
    async for frame in pipeline.render(audio_data, duration_ms, trace_id="pipeline_test"):
        frames.append(frame)
        assert frame.frame_number == len(frames) - 1
    
    assert len(frames) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_livetalking_engine_real_gpu():
    """Test LiveTalking engine with real GPU (integration test).
    
    This test requires:
    - LiveTalking installed (external/livetalking)
    - Models downloaded
    - GPU available
    - Reference video and audio
    
    Skip with: pytest -m "not integration"
    """
    engine = LiveTalkingEngine(
        reference_video="assets/avatar/reference.mp4",
        reference_audio="assets/avatar/reference.wav",
    )
    
    # Initialize (will fail if models not available)
    success = await engine.initialize()
    
    if not success:
        pytest.skip("LiveTalking not properly configured")
    
    # Health check
    health = await engine.health_check()
    assert health
    
    # Try to generate frames
    audio_data = b"\x00" * 1000
    duration_ms = 100.0
    
    try:
        frames = []
        async for frame in engine.generate_frames(audio_data, duration_ms):
            frames.append(frame)
            if len(frames) >= 3:  # Just test a few frames
                break
        
        assert len(frames) > 0
        assert all(isinstance(f, VideoFrame) for f in frames)
        
    except NotImplementedError:
        pytest.skip("LiveTalking GPU inference not yet implemented")
    
    finally:
        await engine.shutdown()


@pytest.mark.asyncio
async def test_livetalking_shutdown():
    """Test clean shutdown of LiveTalking engine."""
    engine = LiveTalkingEngine()
    
    await engine.initialize()
    await engine.shutdown()
    
    assert not engine._initialized
    assert engine._process is None


def test_livetalking_path_detection():
    """Test that LiveTalking path is correctly detected."""
    from pathlib import Path
    
    engine = LiveTalkingEngine()
    
    assert engine.livetalking_path == Path("external/livetalking")
    
    # Should log warning if not found (check in logs)
    # This is just a smoke test to ensure no crashes


@pytest.mark.parametrize("resolution,fps", [
    ((256, 256), 25),
    ((512, 512), 30),
    ((1024, 1024), 60),
])
def test_livetalking_different_configs(resolution, fps):
    """Test LiveTalking with different configurations."""
    engine = LiveTalkingEngine(
        resolution=resolution,
        fps=fps,
    )
    
    assert engine.resolution == resolution
    assert engine.fps == fps


@pytest.mark.asyncio
async def test_livetalking_error_handling_missing_reference():
    """Test error handling when reference files are missing."""
    engine = LiveTalkingEngine(
        reference_video="nonexistent.mp4",
        reference_audio="nonexistent.wav",
    )

    # Should fail gracefully
    success = await engine.initialize()

    # In mock mode, should still succeed
    # In real mode, should fail
    # Either way, should not crash
    assert isinstance(success, bool)


# === LiveTalking Manager Tests ===

def test_livetalking_manager_init():
    """Test LiveTalkingManager initialization."""
    from src.face.livetalking_manager import LiveTalkingManager
    mgr = LiveTalkingManager()
    assert mgr.port == 8010
    assert mgr.model in ("wav2lip", "musetalk", "ultralight")
    assert mgr.app_py.name == "app.py"


def test_livetalking_manager_build_command():
    """Test launch command construction."""
    from src.face.livetalking_manager import LiveTalkingManager
    mgr = LiveTalkingManager()
    cmd = mgr.build_launch_command()
    assert "app.py" in " ".join(cmd)
    assert "--transport" in cmd
    assert "--model" in cmd
    assert "--avatar_id" in cmd
    assert "--listenport" in cmd


def test_livetalking_manager_status():
    """Test engine status reporting."""
    from src.face.livetalking_manager import LiveTalkingManager
    mgr = LiveTalkingManager()
    status = mgr.get_status()
    assert status.state.value == "stopped"
    assert status.app_py_exists is True  # external/livetalking/app.py exists
    d = status.to_dict()
    assert "state" in d
    assert "port" in d
    assert "model" in d


def test_livetalking_manager_config_dict():
    """Test engine config dict."""
    from src.face.livetalking_manager import LiveTalkingManager
    mgr = LiveTalkingManager()
    cfg = mgr.get_config_dict()
    assert "port" in cfg
    assert "transport" in cfg
    assert "launch_command" in cfg
    assert "supported_transports" in cfg
    assert "supported_models" in cfg


def test_livetalking_manager_mock_start_stop(monkeypatch):
    """Test start/stop in mock mode."""
    monkeypatch.setenv("MOCK_MODE", "true")
    from src.face.livetalking_manager import LiveTalkingManager
    mgr = LiveTalkingManager()

    status = mgr.start()
    assert status.state.value == "running"

    assert mgr.is_running() is True

    status = mgr.stop()
    assert status.state.value == "stopped"


def test_livetalking_manager_singleton():
    """Test global singleton."""
    from src.face.livetalking_manager import get_livetalking_manager
    m1 = get_livetalking_manager()
    m2 = get_livetalking_manager()
    assert m1 is m2


# === Readiness Tests ===

def test_readiness_checks_run():
    """Test readiness checks execute without error."""
    from src.dashboard.readiness import run_readiness_checks
    result = run_readiness_checks()
    assert result.overall_status in ("ready", "not_ready", "degraded")
    assert len(result.checks) > 0
    d = result.to_dict()
    assert "overall_status" in d
    assert "checks" in d
    assert "blocking_issues" in d
    assert "recommended_next_action" in d


def test_readiness_check_structure():
    """Test readiness check data structure."""
    from src.dashboard.readiness import ReadinessCheck
    check = ReadinessCheck(name="test", passed=True, status="ok", message="good")
    d = check.to_dict()
    assert d["name"] == "test"
    assert d["passed"] is True
    assert d["status"] == "ok"


def test_readiness_uses_ffmpeg_helper_when_path_lookup_fails():
    """Readiness should use ffmpeg helper, not PATH lookup alone."""
    from src.dashboard.readiness import run_readiness_checks

    with patch(
        "src.dashboard.readiness.check_ffmpeg_ready",
        return_value={"available": True, "path": r"C:\ffmpeg\bin\ffmpeg.exe"},
    ):
        result = run_readiness_checks()

    ffmpeg_check = next(c for c in result.checks if c.name == "ffmpeg_available")
    assert ffmpeg_check.passed is True
    assert "ffmpeg.exe" in ffmpeg_check.message


def test_readiness_degrades_when_musetalk_falls_back_to_wav2lip(monkeypatch):
    """Fallback warnings must surface as degraded, not ready."""
    from src.dashboard.readiness import run_readiness_checks

    monkeypatch.delenv("LIVETALKING_MODEL", raising=False)
    monkeypatch.delenv("LIVETALKING_AVATAR_ID", raising=False)
    monkeypatch.setenv("TIKTOK_RTMP_URL", "rtmp://push.example/live")
    monkeypatch.setenv("TIKTOK_STREAM_KEY", "test-key")

    with patch(
        "src.dashboard.readiness.check_database_health",
        return_value={"healthy": True, "message": "OK"},
    ), patch(
        "src.dashboard.readiness.check_ffmpeg_ready",
        return_value={"available": True, "path": r"C:\tools\ffmpeg\bin\ffmpeg.exe"},
    ), patch(
        "src.dashboard.readiness.resolve_engine",
        return_value="wav2lip",
    ), patch(
        "src.dashboard.readiness.resolve_avatar_id",
        return_value="wav2lip256_avatar1",
    ):
        result = run_readiness_checks()

    assert result.overall_status == "degraded"
    assert any(check.status == "warning" for check in result.checks)


# === Adapter Constants Tests ===

def test_adapter_constants():
    """Test adapter module constants."""
    from src.face.livetalking_adapter import (
        SUPPORTED_TRANSPORTS, SUPPORTED_MODELS,
        DEFAULT_PORT, DEFAULT_MODEL, DEFAULT_AVATAR_ID,
    )
    assert "webrtc" in SUPPORTED_TRANSPORTS
    assert "rtmp" in SUPPORTED_TRANSPORTS
    assert "wav2lip" in SUPPORTED_MODELS
    assert "musetalk" in SUPPORTED_MODELS
    assert DEFAULT_PORT == 8010
    assert DEFAULT_MODEL == "musetalk"
    assert DEFAULT_AVATAR_ID == "musetalk_avatar1"


def test_livetalking_manager_fallback_avatar_matches_resolved_model():
    """Resolved wav2lip fallback must use a wav2lip-compatible avatar."""
    from src.face.livetalking_manager import LiveTalkingManager

    with patch("src.face.livetalking_manager.resolve_engine", return_value="wav2lip"):
        mgr = LiveTalkingManager()

    assert mgr.model == "wav2lip"
    assert mgr.avatar_id == "wav2lip256_avatar1"
    assert "wav2lip256_avatar1" in " ".join(mgr.build_launch_command())


def test_engine_transport_determination():
    """Test transport mode is determined correctly from flags."""
    engine_webrtc = LiveTalkingEngine(use_webrtc=True, use_rtmp=False)
    assert engine_webrtc.transport == "webrtc"

    engine_rtmp = LiveTalkingEngine(use_webrtc=False, use_rtmp=True)
    assert engine_rtmp.transport == "rtmp"

    engine_default = LiveTalkingEngine(use_webrtc=False, use_rtmp=False)
    assert engine_default.transport == "webrtc"


# === Requested vs Resolved State Tests ===

def test_manager_status_includes_requested_fields():
    """EngineStatus.to_dict() must include requested_model and requested_avatar_id."""
    from src.face.livetalking_manager import LiveTalkingManager

    mgr = LiveTalkingManager()
    d = mgr.get_status().to_dict()

    assert "requested_model" in d, "status missing requested_model"
    assert "resolved_model" in d, "status missing resolved_model"
    assert "requested_avatar_id" in d, "status missing requested_avatar_id"
    assert "resolved_avatar_id" in d, "status missing resolved_avatar_id"
    # resolved_model must equal the current model
    assert d["resolved_model"] == d["model"]
    assert d["resolved_avatar_id"] == d["avatar_id"]


def test_manager_config_includes_requested_fields():
    """get_config_dict() must include requested_model and requested_avatar_id."""
    from src.face.livetalking_manager import LiveTalkingManager

    mgr = LiveTalkingManager()
    cfg = mgr.get_config_dict()

    assert "requested_model" in cfg, "config missing requested_model"
    assert "resolved_model" in cfg, "config missing resolved_model"
    assert "requested_avatar_id" in cfg, "config missing requested_avatar_id"
    assert "resolved_avatar_id" in cfg, "config missing resolved_avatar_id"


def test_manager_requested_vs_resolved_on_fallback():
    """When engine falls back to wav2lip, requested != resolved must be visible."""
    from src.face.livetalking_manager import LiveTalkingManager

    with patch("src.face.livetalking_manager.resolve_engine", return_value="wav2lip"):
        mgr = LiveTalkingManager()

    d = mgr.get_status().to_dict()
    assert d["requested_model"] == "musetalk"
    assert d["resolved_model"] == "wav2lip"
    assert d["resolved_model"] != d["requested_model"]
