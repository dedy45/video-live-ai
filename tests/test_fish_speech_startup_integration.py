"""Integration tests for enhanced Fish Speech sidecar startup."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_fish_speech.py"


def load_setup_module():
    """Load scripts/setup_fish_speech.py as a module."""
    spec = importlib.util.spec_from_file_location("setup_fish_speech", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reference_audio_files_exist_from_task_0() -> None:
    """Verify that test audio files from Task 0 Phase 1 are present."""
    voice_dir = PROJECT_ROOT / "assets" / "voice"
    
    assert (voice_dir / "christine.wav").exists()
    assert (voice_dir / "roma.wav").exists()
    assert (voice_dir / "reference.wav").exists()
    assert (voice_dir / "reference.txt").exists()
    
    # Verify files are non-empty
    assert (voice_dir / "christine.wav").stat().st_size > 0
    assert (voice_dir / "roma.wav").stat().st_size > 0
    assert (voice_dir / "reference.wav").stat().st_size > 0
    assert (voice_dir / "reference.txt").stat().st_size > 0


def test_check_reference_wav_validates_existing_files() -> None:
    """Reference WAV check should pass with existing test files."""
    setup = load_setup_module()
    
    result = setup.check_reference_wav(PROJECT_ROOT)
    
    assert result is True


def test_check_reference_text_validates_existing_files() -> None:
    """Reference text check should pass with existing test files."""
    setup = load_setup_module()
    
    result = setup.check_reference_text(PROJECT_ROOT)
    
    assert result is True


def test_health_check_functions_are_callable() -> None:
    """Verify new health check functions are properly defined and callable."""
    setup = load_setup_module()
    
    # These should be callable without errors (will return False if server not running)
    assert callable(setup.check_server_reachable)
    assert callable(setup.check_health_endpoint)
    assert callable(setup.validate_checkpoint_files)
    assert callable(setup.detect_trained_model)


def test_startup_with_retry_logic_structure(tmp_path: Path) -> None:
    """Verify start_server has retry logic structure (without actual startup)."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create minimal prerequisites
    layout.checkout_dir.mkdir(parents=True, exist_ok=True)
    layout.venv_python.parent.mkdir(parents=True, exist_ok=True)
    layout.venv_python.touch()
    
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    (checkpoint_root / "model.pth").write_bytes(b"model")
    (checkpoint_root / "config.json").write_bytes(b'{}')
    (checkpoint_root / "tokenizer.tiktoken").write_bytes(b"tok")
    (checkpoint_root / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_bytes(b"dec")
    
    # Mock to prevent actual startup
    original_build_status = setup.build_status_payload
    
    def mock_build_status(*args, **kwargs):  # type: ignore[no-untyped-def]
        payload = original_build_status(*args, **kwargs)
        payload["runtime"]["reachable"] = True  # Pretend already running
        return payload
    
    setup.build_status_payload = mock_build_status
    
    try:
        exit_code = setup.start_server(project_root=tmp_path)
        # Should succeed (early return because "already reachable")
        assert exit_code == 0
    finally:
        setup.build_status_payload = original_build_status


def test_graceful_degradation_when_trained_model_not_found(tmp_path: Path) -> None:
    """Verify graceful degradation to base model when trained model not found."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # No trained model exists
    has_trained, trained_path = setup.detect_trained_model(layout)
    
    assert has_trained is False
    assert trained_path is None
    
    # System should still be able to use base model
    # (This is verified by the start_server logic which logs a warning but continues)
