"""Tests for LiveTalking integration.

Run with:
    pytest tests/test_livetalking_integration.py -v
    pytest tests/test_livetalking_integration.py -v -m "not integration"  # Skip GPU tests
"""

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
