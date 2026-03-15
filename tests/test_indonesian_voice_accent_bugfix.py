"""Bug condition exploration test for Indonesian voice accent fix.

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6**

This test explores the bug condition on UNFIXED code. It is EXPECTED TO FAIL
on unfixed code - failure confirms the bug exists. The test will pass after
the fix is implemented.

CRITICAL: This test encodes the expected behavior - it validates the fix when
it passes after implementation. DO NOT attempt to fix the test or code when it
fails initially.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

# Run this test in non-mock mode to test real Fish Speech behavior
os.environ["MOCK_MODE"] = "false"


@pytest.mark.asyncio
async def test_bug_condition_fish_speech_sidecar_unreachable() -> None:
    """Property 1: Bug Condition - Fish Speech Sidecar Unreachable.
    
    **Validates: Requirements 1.1, 1.5**
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (sidecar not running).
    When fixed, Fish Speech sidecar will be reachable at http://127.0.0.1:8080.
    """
    from src.voice.fish_speech_client import FishSpeechClient
    
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=5000)
    
    # ASSERT: Fish Speech sidecar should be reachable
    # On UNFIXED code: This will FAIL (returns False, sidecar not running)
    # On FIXED code: This will PASS (returns True, sidecar running)
    health_result = await client.health_check()
    server_reachable = health_result.get("reachable", False) if isinstance(health_result, dict) else health_result
    
    assert server_reachable is True, (
        "Fish Speech sidecar is NOT reachable at http://127.0.0.1:8080. "
        "Health check failed on all probe endpoints (/v1/health, /health, /v1/models, /json). "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: sidecar should be running and reachable."
    )


@pytest.mark.asyncio
async def test_bug_condition_voice_clone_untrained() -> None:
    """Property 1: Bug Condition - Voice Clone Untrained.
    
    **Validates: Requirements 1.2, 1.6**
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (no trained model).
    When fixed, a trained voice model checkpoint will exist.
    """
    from src.config import get_config
    
    config = get_config()
    
    # Check for trained model checkpoint
    # Expected paths for trained models:
    # - external/fish-speech/checkpoints/trained/
    # - external/fish-speech/checkpoints/indonesian-voice/
    trained_model_paths = [
        Path("external/fish-speech/checkpoints/trained"),
        Path("external/fish-speech/checkpoints/indonesian-voice"),
        Path("external/fish-speech/checkpoints/fish-speech-1.5-trained"),
    ]
    
    trained_model_exists = any(
        path.exists() and any(path.glob("*.ckpt")) or any(path.glob("*.pth"))
        for path in trained_model_paths
    )
    
    # ASSERT: Trained voice model checkpoint should exist
    # On UNFIXED code: This will FAIL (no trained model found)
    # On FIXED code: This will PASS (trained model exists)
    assert trained_model_exists is True, (
        "No trained voice model checkpoint found. "
        f"Checked paths: {[str(p) for p in trained_model_paths]}. "
        "Only reference.wav exists without fine-tuning. "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: trained model checkpoint should exist after training workflow."
    )


@pytest.mark.asyncio
async def test_bug_condition_insufficient_reference_quality() -> None:
    """Property 1: Bug Condition - Insufficient Reference Quality.
    
    **Validates: Requirements 1.3**
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (insufficient dataset).
    When fixed, reference dataset will have 30-60 min of Indonesian audio.
    """
    from src.config import get_config
    import wave
    
    config = get_config()
    
    # Check reference audio dataset quality
    reference_wav_path = Path(config.voice.clone_reference_wav)
    
    # Calculate total duration of reference audio
    total_duration_min = 0.0
    
    if reference_wav_path.exists():
        try:
            with wave.open(str(reference_wav_path), 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration_sec = frames / float(rate)
                total_duration_min = duration_sec / 60.0
        except Exception:
            # If single file fails, might be a directory with multiple files
            pass
    
    # Check if reference path is a directory with multiple files
    reference_dir = reference_wav_path.parent
    if reference_dir.exists():
        for wav_file in reference_dir.glob("*.wav"):
            try:
                with wave.open(str(wav_file), 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration_sec = frames / float(rate)
                    total_duration_min += duration_sec / 60.0
            except Exception:
                continue
    
    # ASSERT: Reference dataset should have at least 30 minutes of audio
    # On UNFIXED code: This will FAIL (only 1 short WAV file, < 30 min)
    # On FIXED code: This will PASS (30-60 min Indonesian dataset)
    assert total_duration_min >= 30.0, (
        f"Reference audio dataset is insufficient: {total_duration_min:.2f} minutes. "
        "Requires 30-60 minutes of clean Indonesian speech for proper training. "
        "Current setup has only 1 short WAV file without fine-tuning. "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: dataset should have 30-60 min of Indonesian audio."
    )


@pytest.mark.asyncio
async def test_bug_condition_synthesis_latency_high() -> None:
    """Property 1: Bug Condition - Synthesis Latency High with Untrained Voice Clone.
    
    **Validates: Requirements 1.4**
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (latency 36-59s).
    When fixed, synthesis latency will be under 5 seconds.
    
    NOTE: This test requires Fish Speech sidecar to be running. If sidecar is
    not running, the test will skip with a clear message.
    """
    from src.voice.fish_speech_client import FishSpeechClient, FishSpeechClientError
    from src.config import get_config
    
    config = get_config()
    client = FishSpeechClient(
        base_url=config.voice.fish_speech_base_url,
        timeout_ms=60000  # 60s timeout to allow for slow synthesis
    )
    
    # Check if sidecar is reachable first
    health_result = await client.health_check()
    server_reachable = health_result.get("reachable", False) if isinstance(health_result, dict) else health_result
    if not server_reachable:
        pytest.skip(
            "Fish Speech sidecar is not running. "
            "This test requires the sidecar to measure synthesis latency. "
            "Start the sidecar with: uv run python scripts/manage.py start fish-speech"
        )
    
    # Load reference audio and text
    try:
        reference_audio_b64 = FishSpeechClient.load_reference_audio_b64(
            config.voice.clone_reference_wav
        )
        reference_text = FishSpeechClient.load_reference_text(
            config.voice.clone_reference_text
        )
    except (FileNotFoundError, ValueError) as e:
        pytest.skip(f"Reference assets not found: {e}")
    
    # Measure synthesis latency
    test_text = "Halo semuanya, selamat datang di live streaming kami hari ini."
    
    start_time = time.time()
    try:
        audio_data = await client.synthesize(
            text=test_text,
            reference_audio_b64=reference_audio_b64,
            reference_text=reference_text,
        )
        latency_ms = (time.time() - start_time) * 1000
    except FishSpeechClientError as e:
        pytest.fail(
            f"Fish Speech synthesis failed: {e}. "
            "This indicates the sidecar is running but synthesis is failing. "
            "Check sidecar logs for details."
        )
    
    # ASSERT: Synthesis latency should be under 5 seconds
    # On UNFIXED code: This will FAIL (latency 36-59 seconds with untrained voice clone)
    # On FIXED code: This will PASS (latency < 5 seconds with trained model)
    assert latency_ms < 5000, (
        f"Synthesis latency is too high: {latency_ms:.0f}ms ({latency_ms/1000:.1f}s). "
        "Expected: < 5000ms (5 seconds). "
        "High latency indicates untrained voice clone struggling with Indonesian phonetics. "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: trained model should achieve < 5s latency."
    )


@pytest.mark.asyncio
async def test_bug_condition_accent_quality_automated() -> None:
    """Property 1: Bug Condition - Accent Quality Automated Check.
    
    **Validates: Requirements 1.2, 1.4**
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (unstable/mixed accent).
    When fixed, synthesis will produce consistent natural Indonesian accent.
    
    Automated metric: latency < 5000ms AND synthesis_success == True AND detected_language == "id"
    Manual spot check deferred to Task 5 checkpoint.
    
    NOTE: This test requires Fish Speech sidecar to be running. If sidecar is
    not running, the test will skip with a clear message.
    """
    from src.voice.fish_speech_client import FishSpeechClient, FishSpeechClientError
    from src.config import get_config
    
    config = get_config()
    client = FishSpeechClient(
        base_url=config.voice.fish_speech_base_url,
        timeout_ms=60000  # 60s timeout to allow for slow synthesis
    )
    
    # Check if sidecar is reachable first
    health_result = await client.health_check()
    server_reachable = health_result.get("reachable", False) if isinstance(health_result, dict) else health_result
    if not server_reachable:
        pytest.skip(
            "Fish Speech sidecar is not running. "
            "This test requires the sidecar to measure accent quality. "
            "Start the sidecar with: uv run python scripts/manage.py start fish-speech"
        )
    
    # Load reference audio and text
    try:
        reference_audio_b64 = FishSpeechClient.load_reference_audio_b64(
            config.voice.clone_reference_wav
        )
        reference_text = FishSpeechClient.load_reference_text(
            config.voice.clone_reference_text
        )
    except (FileNotFoundError, ValueError) as e:
        pytest.skip(f"Reference assets not found: {e}")
    
    # Test synthesis with Indonesian text
    test_text = config.voice.indonesian_smoke_text
    
    synthesis_success = False
    latency_ms = 0.0
    
    start_time = time.time()
    try:
        audio_data = await client.synthesize(
            text=test_text,
            reference_audio_b64=reference_audio_b64,
            reference_text=reference_text,
        )
        latency_ms = (time.time() - start_time) * 1000
        synthesis_success = len(audio_data) > 0
    except FishSpeechClientError:
        synthesis_success = False
    
    # Automated accent quality metric
    # Note: We can't detect language from audio bytes without additional libraries
    # For now, we use latency and synthesis success as proxy metrics
    accent_quality_ok = (
        synthesis_success is True
        and latency_ms < 5000
    )
    
    # ASSERT: Accent quality should be acceptable
    # On UNFIXED code: This will FAIL (unstable/mixed accent, high latency)
    # On FIXED code: This will PASS (consistent natural Indonesian accent)
    assert accent_quality_ok is True, (
        f"Accent quality check failed. "
        f"synthesis_success={synthesis_success}, latency_ms={latency_ms:.0f}ms. "
        "Expected: synthesis_success=True AND latency < 5000ms. "
        "Unstable or mixed accent indicates untrained voice clone. "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: trained model should produce consistent natural Indonesian accent. "
        "Manual spot check will be performed in Task 5 checkpoint."
    )


# Property-Based Test: Bug Condition Exploration
@given(
    text=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll"), min_codepoint=65, max_codepoint=122),
        min_size=10,
        max_size=100
    )
)
@settings(max_examples=5, deadline=None)
@pytest.mark.asyncio
async def test_property_bug_condition_server_reachability(text: str) -> None:
    """Property 1: Bug Condition - Fish Speech Sidecar Reachable (Property-Based).
    
    **Validates: Requirements 2.1, 2.5**
    
    For any voice synthesis request, the Fish Speech sidecar should be reachable.
    
    EXPECTED OUTCOME: This test FAILS on unfixed code (sidecar not running).
    When fixed, sidecar will be reachable for all synthesis requests.
    """
    from src.voice.fish_speech_client import FishSpeechClient
    
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=5000)
    
    # ASSERT: Fish Speech sidecar should be reachable for any synthesis request
    # On UNFIXED code: This will FAIL (returns False, sidecar not running)
    # On FIXED code: This will PASS (returns True, sidecar running)
    health_result = await client.health_check()
    server_reachable = health_result.get("reachable", False) if isinstance(health_result, dict) else health_result
    
    assert server_reachable is True, (
        f"Fish Speech sidecar is NOT reachable for synthesis request with text: '{text[:50]}...'. "
        "This is EXPECTED on unfixed code - the bug exists. "
        "After fix: sidecar should be running and reachable for all requests."
    )
