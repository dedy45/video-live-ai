"""Tests for Mock Mode infrastructure."""

from __future__ import annotations

import os

import pytest

os.environ["MOCK_MODE"] = "true"


def test_mock_audio_result_silence() -> None:
    """MockAudioResult.silence() should return valid silent audio."""
    from src.utils.mock_mode import MockAudioResult

    result = MockAudioResult.silence(duration_ms=1000.0)
    assert result.duration_ms == 1000.0
    assert result.sample_rate == 24000
    assert result.format == "wav"
    assert len(result.audio_data) > 0


def test_mock_video_frame_placeholder() -> None:
    """MockVideoFrame.placeholder() should return correct dimensions."""
    from src.utils.mock_mode import MockVideoFrame

    frame = MockVideoFrame.placeholder(width=512, height=512)
    assert frame.width == 512
    assert frame.height == 512
    assert frame.pixels.shape == (512, 512, 3)


@pytest.mark.asyncio
async def test_mock_voice_synthesizer() -> None:
    """MockVoiceSynthesizer should return silence matching production format."""
    from src.utils.mock_mode import MockVoiceSynthesizer

    synth = MockVoiceSynthesizer()
    result = await synth.synthesize("Hello world", emotion="happy")
    assert result.sample_rate == 24000
    assert result.duration_ms > 0
    assert len(result.audio_data) > 0


@pytest.mark.asyncio
async def test_mock_avatar_renderer_stream() -> None:
    """MockAvatarRenderer should yield placeholder frames."""
    from src.utils.mock_mode import MockAvatarRenderer

    renderer = MockAvatarRenderer(width=256, height=256)
    frames = []
    async for frame in renderer.generate_stream(b"fake_audio", duration_ms=100.0):
        frames.append(frame)

    assert len(frames) >= 1
    assert frames[0].width == 256
    assert frames[0].height == 256


def test_get_mock_helpers_in_mock_mode() -> None:
    """get_mock_voice/avatar should return instances in Mock Mode."""
    os.environ["MOCK_MODE"] = "true"
    from src.utils.mock_mode import get_mock_avatar, get_mock_voice

    assert get_mock_voice() is not None
    assert get_mock_avatar() is not None


def test_get_mock_helpers_not_in_mock_mode() -> None:
    """get_mock_voice/avatar should return None when not in Mock Mode."""
    os.environ["MOCK_MODE"] = "false"
    from src.utils.mock_mode import get_mock_avatar, get_mock_voice

    assert get_mock_voice() is None
    assert get_mock_avatar() is None

    # Reset
    os.environ["MOCK_MODE"] = "true"
