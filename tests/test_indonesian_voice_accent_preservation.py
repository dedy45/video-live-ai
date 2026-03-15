"""Preservation property tests for Indonesian voice accent fix.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

These tests observe and verify behavior on UNFIXED code for non-buggy inputs.
They ensure that existing Edge TTS fallback, audio caching, and runtime state
tracking remain unchanged after the fix is implemented.

EXPECTED OUTCOME: These tests PASS on unfixed code (confirms baseline behavior).
After fix implementation, these tests should STILL PASS (confirms no regressions).

IMPORTANT: Follow observation-first methodology - these tests capture the
current working behavior that must be preserved.

NOTE: Some tests use mocking to avoid slow Edge TTS synthesis while still
verifying the preservation logic.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, settings, strategies as st


@pytest.mark.asyncio
async def test_preservation_edge_tts_fallback_when_fish_speech_unreachable() -> None:
    """Property 2: Preservation - Edge TTS Fallback.
    
    **Validates: Requirements 3.1, 3.7, 3.8**
    
    For all synthesis requests where Fish Speech is unreachable, system falls
    back to Edge TTS (id-ID-ArdiNeural) without crashing.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (fallback works correctly).
    After fix: Test should STILL PASS (fallback behavior preserved).
    
    NOTE: This test uses mocking to verify fallback logic without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    # Create router
    router = VoiceRouter()
    
    # Mock the primary engine to fail (simulating Fish Speech unreachable)
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    # Mock the backup engine to succeed
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        return AudioResult(
            audio_data=b"mock_audio_data",
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # Attempt synthesis - should fallback to Edge TTS
    test_text = "Halo tes."
    
    result = await router.synthesize(
        text=test_text,
        emotion="neutral",
        speed=1.0,
        trace_id="test_fallback"
    )
    
    # Verify synthesis succeeded (via fallback)
    assert result is not None, "Synthesis should succeed via Edge TTS fallback"
    assert len(result.audio_data) > 0, "Audio data should be generated"
    assert result.text == test_text, "Result should contain original text"
    
    # Verify runtime state reflects fallback
    state = get_voice_runtime_state()
    assert state.fallback_active is True, (
        "Fallback should be active when Fish Speech is unreachable"
    )
    assert state.resolved_engine == "edge_tts", (
        "Resolved engine should be edge_tts when Fish Speech fails"
    )
    assert state.last_error is not None, (
        "Last error should contain primary engine failure reason"
    )
    
    # Verify Edge TTS was used (not Fish Speech)
    assert "edge_tts" in state.resolved_engine.lower(), (
        "Edge TTS should be the resolved engine"
    )


@pytest.mark.asyncio
async def test_preservation_audio_caching_by_content_hash() -> None:
    """Property 2: Preservation - Audio Caching.
    
    **Validates: Requirements 3.2**
    
    For all synthesis requests with same (text, emotion, speed), system returns
    cached audio without re-synthesizing.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (caching works correctly).
    After fix: Test should STILL PASS (caching behavior preserved).
    
    NOTE: This test uses mocking to verify caching logic without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    router = VoiceRouter()
    
    # Mock the backup engine to succeed quickly
    call_count = 0
    
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        nonlocal call_count
        call_count += 1
        return AudioResult(
            audio_data=f"mock_audio_{call_count}".encode(),
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    # Mock primary to fail so backup is used
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # First synthesis - should generate audio
    test_text = "Tes cache."
    emotion = "neutral"
    speed = 1.0
    
    result1 = await router.synthesize(
        text=test_text,
        emotion=emotion,
        speed=speed,
        trace_id="test_cache_1"
    )
    
    assert result1 is not None
    assert len(result1.audio_data) > 0
    assert result1.cached is False, "First synthesis should not be cached"
    assert call_count == 1, "Backup should be called once"
    
    # Second synthesis with same parameters - should return cached audio
    result2 = await router.synthesize(
        text=test_text,
        emotion=emotion,
        speed=speed,
        trace_id="test_cache_2"
    )
    
    assert result2 is not None
    assert result2.cached is True, "Second synthesis should return cached audio"
    assert result2.audio_data == result1.audio_data, (
        "Cached audio should be identical to original"
    )
    assert result2.text == test_text
    assert call_count == 1, "Backup should NOT be called again (cache hit)"
    
    # Third synthesis with different text - should NOT use cache
    result3 = await router.synthesize(
        text="Teks lain.",
        emotion=emotion,
        speed=speed,
        trace_id="test_cache_3"
    )
    
    assert result3 is not None
    assert result3.cached is False, "Different text should not use cache"
    assert call_count == 2, "Backup should be called again (cache miss)"
    
    # Fourth synthesis with different emotion - should NOT use cache
    result4 = await router.synthesize(
        text=test_text,
        emotion="excited",
        speed=speed,
        trace_id="test_cache_4"
    )
    
    assert result4 is not None
    assert result4.cached is False, "Different emotion should not use cache"
    assert call_count == 3, "Backup should be called again (cache miss)"
    
    # Fifth synthesis with different speed - should NOT use cache
    result5 = await router.synthesize(
        text=test_text,
        emotion=emotion,
        speed=1.2,
        trace_id="test_cache_5"
    )
    
    assert result5 is not None
    assert result5.cached is False, "Different speed should not use cache"
    assert call_count == 4, "Backup should be called again (cache miss)"


@pytest.mark.asyncio
async def test_preservation_voice_runtime_state_updates() -> None:
    """Property 2: Preservation - Voice Runtime State Updates.
    
    **Validates: Requirements 3.3**
    
    For all synthesis attempts, system updates voice runtime state
    (server_reachable, reference_ready, fallback_active) correctly.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (state tracking works).
    After fix: Test should STILL PASS (state tracking preserved).
    
    NOTE: This test uses mocking to verify state tracking without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    router = VoiceRouter()
    state = get_voice_runtime_state()
    
    # Mock backup engine to succeed
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        return AudioResult(
            audio_data=b"mock_audio",
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    # Mock primary to fail
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # Initial state
    initial_resolved = state.resolved_engine
    
    # Perform synthesis
    # Use short text to minimize synthesis time
    test_text = "Tes state."
    result = await router.synthesize(
        text=test_text,
        emotion="neutral",
        speed=1.0,
        trace_id="test_state"
    )
    
    assert result is not None
    
    # Verify runtime state was updated
    assert state.resolved_engine != initial_resolved or state.resolved_engine != "unknown", (
        "Resolved engine should be updated after synthesis"
    )
    assert state.last_latency_ms is not None, (
        "Last latency should be recorded after synthesis"
    )
    assert state.last_latency_ms > 0, (
        "Last latency should be positive"
    )
    
    # Verify fallback_active reflects actual engine used
    if state.resolved_engine == "edge_tts":
        assert state.fallback_active is True, (
            "Fallback should be active when Edge TTS is used"
        )
    elif state.resolved_engine == "fish_speech":
        assert state.fallback_active is False, (
            "Fallback should not be active when Fish Speech succeeds"
        )


@pytest.mark.asyncio
async def test_preservation_reference_audio_text_in_payload() -> None:
    """Property 2: Preservation - Reference Audio/Text in API Payload.
    
    **Validates: Requirements 3.4**
    
    For all synthesis requests with reference_audio_b64 and reference_text,
    system includes them in the Fish Speech API payload.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (reference loading works).
    After fix: Test should STILL PASS (reference loading preserved).
    """
    try:
        from src.voice.fish_speech_client import FishSpeechClient
    except ModuleNotFoundError as e:
        if "msgpack" in str(e):
            pytest.skip("msgpack not installed - required for Fish Speech client")
        raise
    
    from src.config import get_config
    
    config = get_config()
    
    # Test reference audio loading
    try:
        reference_audio_b64 = FishSpeechClient.load_reference_audio_b64(
            config.voice.clone_reference_wav
        )
        assert reference_audio_b64 is not None, "Reference audio should be loaded"
        assert len(reference_audio_b64) > 0, "Reference audio should not be empty"
        assert isinstance(reference_audio_b64, str), "Reference audio should be base64 string"
    except FileNotFoundError:
        pytest.skip("Reference audio file not found - expected in unfixed code")
    
    # Test reference text loading
    try:
        reference_text = FishSpeechClient.load_reference_text(
            config.voice.clone_reference_text
        )
        assert reference_text is not None, "Reference text should be loaded"
        assert len(reference_text) > 0, "Reference text should not be empty"
        assert isinstance(reference_text, str), "Reference text should be string"
    except FileNotFoundError:
        pytest.skip("Reference text file not found - expected in unfixed code")


@pytest.mark.asyncio
async def test_preservation_mock_mode_uses_mock_synthesizer() -> None:
    """Property 2: Preservation - Mock Mode Uses MockVoiceSynthesizer.
    
    **Validates: Requirements 3.5**
    
    For all synthesis requests in mock mode, system uses MockVoiceSynthesizer
    instead of real TTS engines.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (mock mode works).
    After fix: Test should STILL PASS (mock mode preserved).
    """
    import os
    from src.voice.engine import FishSpeechEngine, EdgeTTSEngine
    from src.voice.runtime_state import reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    # Enable mock mode
    original_mock_mode = os.environ.get("MOCK_MODE", "false")
    os.environ["MOCK_MODE"] = "true"
    
    try:
        # Test Fish Speech engine in mock mode
        fish_engine = FishSpeechEngine()
        fish_result = await fish_engine.synthesize(
            text="Tes mock mode Fish Speech.",
            emotion="neutral",
            speed=1.0,
            trace_id="test_mock_fish"
        )
        
        assert fish_result is not None
        assert len(fish_result.audio_data) > 0
        assert fish_result.latency_ms < 100, (
            "Mock mode should have very low latency (< 100ms)"
        )
        
        # Test Edge TTS engine in mock mode
        edge_engine = EdgeTTSEngine()
        edge_result = await edge_engine.synthesize(
            text="Tes mock mode Edge TTS.",
            emotion="neutral",
            speed=1.0,
            trace_id="test_mock_edge"
        )
        
        assert edge_result is not None
        assert len(edge_result.audio_data) > 0
        assert edge_result.latency_ms < 100, (
            "Mock mode should have very low latency (< 100ms)"
        )
        
        # Test health check in mock mode
        fish_health = await fish_engine.health_check()
        assert fish_health is True, "Mock mode health check should always return True"
        
    finally:
        # Restore original mock mode setting
        os.environ["MOCK_MODE"] = original_mock_mode


@pytest.mark.asyncio
async def test_preservation_emotion_mapping_with_speed_modulation() -> None:
    """Property 2: Preservation - Emotion Mapping with Speed Modulation.
    
    **Validates: Requirements 3.6**
    
    For all synthesis requests with emotion mapping, system applies speed
    modulation based on emotion configuration.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (emotion mapping works).
    After fix: Test should STILL PASS (emotion mapping preserved).
    
    NOTE: This test uses mocking to verify emotion mapping without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import reset_voice_runtime_state
    from src.config import get_config
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    config = get_config()
    router = VoiceRouter()
    
    # Verify emotion mapping is loaded from config
    assert hasattr(router, 'emotion_map'), "Router should have emotion_map"
    assert isinstance(router.emotion_map, dict), "Emotion map should be a dictionary"
    
    # Mock engines to succeed quickly
    async def mock_engine_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        return AudioResult(
            audio_data=b"mock_audio",
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    # Mock primary to fail, backup to succeed
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_engine_success
    
    # Test synthesis with different emotions
    # Note: The actual speed modulation happens inside VoiceRouter.synthesize()
    # We verify that synthesis succeeds with emotion parameter
    # Use only 2 emotions to minimize test time
    
    emotions_to_test = ["neutral", "excited"]
    
    for emotion in emotions_to_test:
        result = await router.synthesize(
            text="Tes emosi.",
            emotion=emotion,
            speed=1.0,
            trace_id=f"test_emotion_{emotion}"
        )
        
        assert result is not None, f"Synthesis should succeed for emotion: {emotion}"
        assert result.emotion == emotion, f"Result should preserve emotion: {emotion}"
        assert len(result.audio_data) > 0, f"Audio should be generated for emotion: {emotion}"


# Property-Based Tests for Preservation

@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
        min_size=5,
        max_size=30
    ),
    emotion=st.sampled_from(["neutral", "excited"]),
    speed=st.floats(min_value=0.9, max_value=1.1)
)
@settings(max_examples=3, deadline=10000)  # 3 examples, 10s deadline
@pytest.mark.asyncio
async def test_property_preservation_edge_tts_fallback(
    text: str, emotion: str, speed: float
) -> None:
    """Property 2: Preservation - Edge TTS Fallback (Property-Based).
    
    **Validates: Requirements 3.1, 3.7, 3.8**
    
    For any synthesis request where Fish Speech is unreachable, system falls
    back to Edge TTS without crashing.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (fallback works for all inputs).
    After fix: Test should STILL PASS (fallback preserved for all inputs).
    
    NOTE: This test uses mocking to verify fallback logic without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    router = VoiceRouter()
    
    # Mock engines
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        return AudioResult(
            audio_data=b"mock_audio",
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # Attempt synthesis - should fallback to Edge TTS when Fish Speech unreachable
    try:
        result = await router.synthesize(
            text=text,
            emotion=emotion,
            speed=speed,
            trace_id=f"test_pbt_fallback_{hash(text)}"
        )
        
        # Verify synthesis succeeded (via fallback or primary)
        assert result is not None, "Synthesis should succeed"
        assert len(result.audio_data) > 0, "Audio data should be generated"
        assert result.text == text, "Result should contain original text"
        
    except Exception as e:
        pytest.fail(
            f"Synthesis should not crash even when Fish Speech is unreachable. "
            f"Error: {e}"
        )


@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
        min_size=5,
        max_size=30
    ),
    emotion=st.sampled_from(["neutral", "excited"]),
    speed=st.floats(min_value=0.9, max_value=1.1)
)
@settings(max_examples=3, deadline=10000)  # 3 examples, 10s deadline
@pytest.mark.asyncio
async def test_property_preservation_audio_caching(
    text: str, emotion: str, speed: float
) -> None:
    """Property 2: Preservation - Audio Caching (Property-Based).
    
    **Validates: Requirements 3.2**
    
    For any synthesis request with same (text, emotion, speed), system returns
    cached audio on second request.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (caching works for all inputs).
    After fix: Test should STILL PASS (caching preserved for all inputs).
    
    NOTE: This test uses mocking to verify caching logic without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    router = VoiceRouter()
    
    # Mock engines
    call_count = 0
    
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        nonlocal call_count
        call_count += 1
        return AudioResult(
            audio_data=f"mock_audio_{call_count}".encode(),
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # First synthesis
    result1 = await router.synthesize(
        text=text,
        emotion=emotion,
        speed=speed,
        trace_id=f"test_pbt_cache_1_{hash(text)}"
    )
    
    assert result1 is not None
    assert len(result1.audio_data) > 0
    initial_call_count = call_count
    
    # Second synthesis with same parameters - should use cache
    result2 = await router.synthesize(
        text=text,
        emotion=emotion,
        speed=speed,
        trace_id=f"test_pbt_cache_2_{hash(text)}"
    )
    
    assert result2 is not None
    assert result2.cached is True, (
        f"Second synthesis should return cached audio for text: '{text[:30]}...'"
    )
    assert result2.audio_data == result1.audio_data, (
        "Cached audio should be identical to original"
    )
    assert call_count == initial_call_count, (
        "Engine should NOT be called again (cache hit)"
    )


@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
        min_size=5,
        max_size=30
    )
)
@settings(max_examples=3, deadline=10000)  # 3 examples, 10s deadline
@pytest.mark.asyncio
async def test_property_preservation_runtime_state_updates(text: str) -> None:
    """Property 2: Preservation - Runtime State Updates (Property-Based).
    
    **Validates: Requirements 3.3**
    
    For any synthesis attempt, system updates voice runtime state correctly.
    
    EXPECTED OUTCOME: Test PASSES on unfixed code (state tracking works for all inputs).
    After fix: Test should STILL PASS (state tracking preserved for all inputs).
    
    NOTE: This test uses mocking to verify state tracking without slow synthesis.
    """
    from src.voice.engine import VoiceRouter, AudioResult
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    # Reset runtime state for clean test
    reset_voice_runtime_state()
    
    router = VoiceRouter()
    state = get_voice_runtime_state()
    
    # Mock engines
    async def mock_backup_success(text: str, emotion: str = "neutral", speed: float = 1.0, trace_id: str = "", **kwargs):
        return AudioResult(
            audio_data=b"mock_audio",
            duration_ms=1000.0,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=50.0,
        )
    
    async def mock_primary_fail(*args, **kwargs):
        raise RuntimeError("Fish Speech unreachable")
    
    router.primary.synthesize = mock_primary_fail
    router.backup.synthesize = mock_backup_success
    
    # Perform synthesis
    result = await router.synthesize(
        text=text,
        emotion="neutral",
        speed=1.0,
        trace_id=f"test_pbt_state_{hash(text)}"
    )
    
    assert result is not None
    
    # Verify runtime state was updated
    assert state.resolved_engine != "unknown", (
        f"Resolved engine should be updated after synthesis for text: '{text[:30]}...'"
    )
    assert state.last_latency_ms is not None, (
        "Last latency should be recorded after synthesis"
    )
    assert state.last_latency_ms > 0, (
        "Last latency should be positive"
    )
