"""Tests for Voice Engine and VoiceRouter with Fish-Speech integration."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

os.environ["MOCK_MODE"] = "true"


@pytest.mark.asyncio
async def test_fish_speech_engine_mock_mode_returns_audio() -> None:
    """FishSpeechEngine in mock mode should return valid AudioResult."""
    from src.voice.engine import FishSpeechEngine

    engine = FishSpeechEngine()
    result = await engine.synthesize("halo kak", emotion="calm")
    assert result.audio_data is not None
    assert len(result.audio_data) > 0
    assert result.text == "halo kak"
    assert result.emotion == "calm"


@pytest.mark.asyncio
async def test_fish_speech_engine_health_check_mock_mode() -> None:
    """FishSpeechEngine health check should return True in mock mode."""
    from src.voice.engine import FishSpeechEngine

    engine = FishSpeechEngine()
    assert await engine.health_check() is True


@pytest.mark.asyncio
async def test_fish_speech_engine_non_mock_requires_clone_references(monkeypatch) -> None:
    """Non-mock Fish-Speech must fail explicitly when clone references are missing."""
    from src.voice import fish_speech_client as client_module
    from src.voice.engine import FishSpeechEngine

    monkeypatch.setenv("MOCK_MODE", "false")
    engine = FishSpeechEngine()

    class DummyClient:
        async def synthesize(self, **kwargs):
            raise AssertionError("client should not be called without references")

    def raise_missing_reference(_path: str) -> str:
        raise FileNotFoundError("missing reference.wav")

    monkeypatch.setattr(engine, "_get_client", lambda: DummyClient())
    monkeypatch.setattr(
        client_module.FishSpeechClient,
        "load_reference_audio_b64",
        staticmethod(raise_missing_reference),
    )

    with pytest.raises(RuntimeError, match="Voice clone reference"):
        await engine.synthesize("halo kak")


@pytest.mark.asyncio
async def test_voice_router_uses_fish_speech_when_primary_healthy(monkeypatch) -> None:
    """VoiceRouter should use FishSpeechEngine when primary succeeds."""
    from src.voice.engine import AudioResult, VoiceRouter
    from src.voice.runtime_state import reset_voice_runtime_state, get_voice_runtime_state

    reset_voice_runtime_state()
    router = VoiceRouter()

    mock_result = AudioResult(
        audio_data=b"wav_data",
        duration_ms=100.0,
        emotion="neutral",
        text="halo kak",
        latency_ms=50.0,
    )
    monkeypatch.setattr(router.primary, "synthesize", AsyncMock(return_value=mock_result))

    result = await router.synthesize("halo kak", emotion="neutral")
    assert result.audio_data == b"wav_data"

    state = get_voice_runtime_state()
    assert state.resolved_engine == "fish_speech"
    assert state.fallback_active is False
    reset_voice_runtime_state()


@pytest.mark.asyncio
async def test_voice_router_falls_back_to_edge_tts_on_primary_failure(monkeypatch) -> None:
    """VoiceRouter should fallback to EdgeTTS when FishSpeech fails."""
    from src.voice.engine import AudioResult, VoiceRouter
    from src.voice.runtime_state import reset_voice_runtime_state, get_voice_runtime_state

    reset_voice_runtime_state()
    router = VoiceRouter()

    monkeypatch.setattr(
        router.primary, "synthesize",
        AsyncMock(side_effect=RuntimeError("Fish-Speech unavailable")),
    )
    fallback_result = AudioResult(
        audio_data=b"edge_wav",
        duration_ms=200.0,
        emotion="neutral",
        text="halo kak",
        latency_ms=100.0,
    )
    monkeypatch.setattr(router.backup, "synthesize", AsyncMock(return_value=fallback_result))

    result = await router.synthesize("halo kak", emotion="neutral")
    assert result.audio_data == b"edge_wav"

    state = get_voice_runtime_state()
    assert state.resolved_engine == "edge_tts"
    assert state.fallback_active is True
    assert "Fish-Speech unavailable" in (state.last_error or "")
    reset_voice_runtime_state()


@pytest.mark.asyncio
async def test_voice_router_raises_when_all_engines_fail(monkeypatch) -> None:
    """VoiceRouter should raise RuntimeError when both engines fail."""
    from src.voice.engine import VoiceRouter
    from src.voice.runtime_state import reset_voice_runtime_state, get_voice_runtime_state

    reset_voice_runtime_state()
    router = VoiceRouter()

    monkeypatch.setattr(
        router.primary, "synthesize",
        AsyncMock(side_effect=RuntimeError("primary down")),
    )
    monkeypatch.setattr(
        router.backup, "synthesize",
        AsyncMock(side_effect=RuntimeError("backup down")),
    )

    with pytest.raises(RuntimeError, match="All TTS engines failed"):
        await router.synthesize("halo kak")

    state = get_voice_runtime_state()
    assert state.resolved_engine == "none"
    assert state.last_error is not None
    reset_voice_runtime_state()


def test_voice_runtime_state_update_success() -> None:
    """VoiceRuntimeState.update_success should set resolved engine and clear error."""
    from src.voice.runtime_state import VoiceRuntimeState

    state = VoiceRuntimeState()
    state.update_success("fish_speech", 123.4)
    assert state.resolved_engine == "fish_speech"
    assert state.fallback_active is False
    assert state.last_latency_ms == 123.4
    assert state.last_error is None


def test_voice_runtime_state_update_fallback() -> None:
    """VoiceRuntimeState.update_fallback_success should set fallback_active=True."""
    from src.voice.runtime_state import VoiceRuntimeState

    state = VoiceRuntimeState()
    state.update_fallback_success("edge_tts", 200.0, "primary down")
    assert state.resolved_engine == "edge_tts"
    assert state.fallback_active is True
    assert state.last_latency_ms == 200.0
    assert "primary" in (state.last_error or "")


def test_voice_runtime_state_to_dict() -> None:
    """VoiceRuntimeState.to_dict should return all expected fields."""
    from src.voice.runtime_state import VoiceRuntimeState

    state = VoiceRuntimeState()
    d = state.to_dict()
    assert "requested_engine" in d
    assert "resolved_engine" in d
    assert "fallback_active" in d
    assert "server_reachable" in d
    assert "reference_ready" in d
    assert "last_latency_ms" in d
    assert "last_error" in d
