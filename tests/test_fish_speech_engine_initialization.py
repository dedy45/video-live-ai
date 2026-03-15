"""Tests for Task 3.8: Fish Speech Engine Initialization with Trained Model and Dataset Validation.

Tests verify:
- Trained model checkpoint loading from config
- Runtime state flag for trained model availability
- Dataset quality validation (duration, file count, quality metrics)
- Warning logs for insufficient dataset quality
- Preservation of reference audio/text loading
"""

from __future__ import annotations

import os
import tempfile
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

os.environ["MOCK_MODE"] = "true"


@pytest.fixture
def temp_checkpoint_dir(tmp_path: Path) -> Path:
    """Create a temporary trained model checkpoint directory with valid files."""
    checkpoint_dir = tmp_path / "trained_model"
    checkpoint_dir.mkdir()
    
    # Create required checkpoint files
    (checkpoint_dir / "model.pth").write_bytes(b"fake_model_data" * 1000)
    (checkpoint_dir / "config.json").write_text('{"model": "fish-speech-1.5"}')
    (checkpoint_dir / "tokenizer.tiktoken").write_bytes(b"fake_tokenizer_data" * 100)
    
    return checkpoint_dir


@pytest.fixture
def temp_audio_dataset(tmp_path: Path) -> Path:
    """Create a temporary audio dataset with WAV files."""
    dataset_dir = tmp_path / "training_dataset"
    dataset_dir.mkdir()
    
    # Create sample WAV files with different durations
    for i, duration_sec in enumerate([30, 45, 60, 90], start=1):
        wav_path = dataset_dir / f"segment_{i:03d}.wav"
        create_test_wav(wav_path, duration_sec=duration_sec, sample_rate=16000)
        
        # Create matching transcript
        txt_path = wav_path.with_suffix(".txt")
        txt_path.write_text(f"Ini adalah transkrip untuk segment {i}")
    
    return dataset_dir


def create_test_wav(path: Path, duration_sec: float = 30.0, sample_rate: int = 16000) -> None:
    """Create a test WAV file with specified duration and sample rate."""
    num_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        # Write silent audio data
        wav_file.writeframes(b"\x00\x00" * num_frames)


def test_fish_speech_engine_init_with_trained_model(temp_checkpoint_dir: Path) -> None:
    """FishSpeechEngine.__init__() should load trained model path from config."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(temp_checkpoint_dir)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        
        # Verify trained model path is loaded
        assert engine._trained_model_path == str(temp_checkpoint_dir)
        assert engine._trained_model_available is True
        
        # Verify runtime state is updated
        state = get_voice_runtime_state()
        assert state.trained_model_available is True
    
    reset_voice_runtime_state()


def test_fish_speech_engine_init_without_trained_model() -> None:
    """FishSpeechEngine.__init__() should handle missing trained model gracefully."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        
        # Verify no trained model is loaded
        assert engine._trained_model_path is None
        assert engine._trained_model_available is False
        
        # Verify runtime state reflects no trained model
        state = get_voice_runtime_state()
        assert state.trained_model_available is False
    
    reset_voice_runtime_state()


def test_fish_speech_engine_init_with_invalid_trained_model(tmp_path: Path) -> None:
    """FishSpeechEngine.__init__() should detect invalid trained model checkpoint."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Create checkpoint dir with missing files
    invalid_checkpoint = tmp_path / "invalid_checkpoint"
    invalid_checkpoint.mkdir()
    (invalid_checkpoint / "model.pth").write_bytes(b"data")  # Only one file
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(invalid_checkpoint)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        
        # Verify trained model is marked as unavailable
        assert engine._trained_model_path == str(invalid_checkpoint)
        assert engine._trained_model_available is False
        
        # Verify runtime state reflects invalid model
        state = get_voice_runtime_state()
        assert state.trained_model_available is False
    
    reset_voice_runtime_state()


def test_validate_trained_model_with_valid_checkpoint(temp_checkpoint_dir: Path) -> None:
    """_validate_trained_model() should return True for valid checkpoint."""
    from src.voice.engine import FishSpeechEngine
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(temp_checkpoint_dir)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        assert engine._validate_trained_model() is True


def test_validate_trained_model_with_missing_files(tmp_path: Path) -> None:
    """_validate_trained_model() should return False when required files are missing."""
    from src.voice.engine import FishSpeechEngine
    
    incomplete_checkpoint = tmp_path / "incomplete"
    incomplete_checkpoint.mkdir()
    (incomplete_checkpoint / "model.pth").write_bytes(b"data")
    # Missing config.json and tokenizer.tiktoken
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(incomplete_checkpoint)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        assert engine._validate_trained_model() is False


def test_validate_trained_model_with_empty_files(tmp_path: Path) -> None:
    """_validate_trained_model() should return False when files are empty."""
    from src.voice.engine import FishSpeechEngine
    
    empty_checkpoint = tmp_path / "empty"
    empty_checkpoint.mkdir()
    (empty_checkpoint / "model.pth").write_bytes(b"")  # Empty file
    (empty_checkpoint / "config.json").write_text("")
    (empty_checkpoint / "tokenizer.tiktoken").write_bytes(b"")
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(empty_checkpoint)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        
        engine = FishSpeechEngine()
        assert engine._validate_trained_model() is False


def test_load_references_validates_dataset_quality(temp_audio_dataset: Path, tmp_path: Path) -> None:
    """_load_references() should validate dataset quality and update runtime state."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import get_voice_runtime_state, reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Create reference files
    ref_wav = tmp_path / "reference.wav"
    ref_txt = tmp_path / "reference.txt"
    create_test_wav(ref_wav, duration_sec=5.0)
    ref_txt.write_text("Halo kak, selamat datang")
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = str(temp_audio_dataset)
        mock_config.return_value.voice.clone_reference_wav = str(ref_wav)
        mock_config.return_value.voice.clone_reference_text = str(ref_txt)
        
        engine = FishSpeechEngine()
        engine._load_references()
        
        # Verify runtime state is updated with dataset duration
        state = get_voice_runtime_state()
        assert state.reference_ready is True
        assert state.training_dataset_duration_min is not None
        # Total duration: 30 + 45 + 60 + 90 = 225 seconds = 3.75 minutes
        assert state.training_dataset_duration_min > 3.0
    
    reset_voice_runtime_state()


def test_load_references_logs_warning_for_insufficient_duration(tmp_path: Path) -> None:
    """_load_references() should log warning when dataset duration is insufficient."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Create small dataset (less than 30 min)
    small_dataset = tmp_path / "small_dataset"
    small_dataset.mkdir()
    wav_path = small_dataset / "short.wav"
    create_test_wav(wav_path, duration_sec=60.0)  # Only 1 minute
    (small_dataset / "short.txt").write_text("Short audio")
    
    # Create reference files
    ref_wav = tmp_path / "reference.wav"
    ref_txt = tmp_path / "reference.txt"
    create_test_wav(ref_wav, duration_sec=5.0)
    ref_txt.write_text("Halo kak")
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = str(small_dataset)
        mock_config.return_value.voice.clone_reference_wav = str(ref_wav)
        mock_config.return_value.voice.clone_reference_text = str(ref_txt)
        
        with patch("src.voice.engine.logger") as mock_logger:
            engine = FishSpeechEngine()
            engine._load_references()
            
            # Verify warning was logged
            mock_logger.warning.assert_called()
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if "fish_speech_dataset_insufficient_duration" in str(call)]
            assert len(warning_calls) > 0
    
    reset_voice_runtime_state()


def test_load_references_logs_quality_issues(tmp_path: Path) -> None:
    """_load_references() should log warning when dataset has quality issues."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Create dataset with quality issues (low sample rate)
    poor_dataset = tmp_path / "poor_dataset"
    poor_dataset.mkdir()
    
    # Create WAV with low sample rate (8kHz instead of 16kHz)
    wav_path = poor_dataset / "low_quality.wav"
    create_test_wav(wav_path, duration_sec=1800.0, sample_rate=8000)  # 30 min but low quality
    (poor_dataset / "low_quality.txt").write_text("Low quality audio")
    
    # Create reference files
    ref_wav = tmp_path / "reference.wav"
    ref_txt = tmp_path / "reference.txt"
    create_test_wav(ref_wav, duration_sec=5.0)
    ref_txt.write_text("Halo kak")
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = str(poor_dataset)
        mock_config.return_value.voice.clone_reference_wav = str(ref_wav)
        mock_config.return_value.voice.clone_reference_text = str(ref_txt)
        
        with patch("src.voice.engine.logger") as mock_logger:
            engine = FishSpeechEngine()
            engine._load_references()
            
            # Verify quality issues warning was logged
            mock_logger.warning.assert_called()
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if "fish_speech_dataset_quality_issues" in str(call)]
            assert len(warning_calls) > 0
    
    reset_voice_runtime_state()


def test_validate_dataset_quality_with_sufficient_dataset(temp_audio_dataset: Path) -> None:
    """_validate_dataset_quality() should return valid=True for sufficient dataset."""
    from src.voice.engine import FishSpeechEngine
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = str(temp_audio_dataset)
        
        engine = FishSpeechEngine()
        validation = engine._validate_dataset_quality()
        
        # Total duration: 30 + 45 + 60 + 90 = 225 seconds = 3.75 minutes
        assert validation["total_duration_min"] > 3.0
        # File count may include files from both temp_audio_dataset and assets/voice if it exists
        assert validation["file_count"] >= 4
        # Note: valid will be False because 3.75 min < 30 min requirement
        assert validation["valid"] is False
        assert "Quick Clone" in validation["guidance"]


def test_validate_dataset_quality_with_no_files(tmp_path: Path) -> None:
    """_validate_dataset_quality() should handle empty dataset gracefully."""
    from src.voice.engine import FishSpeechEngine
    
    empty_dataset = tmp_path / "empty_dataset"
    empty_dataset.mkdir()
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = str(empty_dataset)
        
        # Also patch Path to prevent reading from actual assets/voice directory
        with patch("src.voice.engine.Path") as mock_path_class:
            # Make voice_dir.exists() return False to simulate no files
            mock_voice_dir = MagicMock()
            mock_voice_dir.exists.return_value = False
            mock_voice_dir.glob.return_value = []
            
            mock_training_dir = MagicMock()
            mock_training_dir.exists.return_value = True
            mock_training_dir.glob.return_value = []
            
            def path_side_effect(arg):
                if arg == "assets/voice":
                    return mock_voice_dir
                elif arg == str(empty_dataset):
                    return mock_training_dir
                return Path(arg)
            
            mock_path_class.side_effect = path_side_effect
            
            engine = FishSpeechEngine()
            validation = engine._validate_dataset_quality()
            
            assert validation["valid"] is False
            assert validation["total_duration_min"] == 0.0
            assert validation["file_count"] == 0
            assert "No WAV files found" in validation["issues"][0]


def test_get_client_passes_trained_model_path(temp_checkpoint_dir: Path) -> None:
    """_get_client() should pass trained_model_path to FishSpeechClient."""
    from src.voice.engine import FishSpeechEngine
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = str(temp_checkpoint_dir)
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        mock_config.return_value.voice.fish_speech_base_url = "http://127.0.0.1:8080"
        mock_config.return_value.voice.fish_speech_timeout_ms = 10000
        
        with patch("src.voice.fish_speech_client.FishSpeechClient") as mock_client_class:
            engine = FishSpeechEngine()
            client = engine._get_client()
            
            # Verify FishSpeechClient was instantiated with trained_model_path
            mock_client_class.assert_called_once_with(
                base_url="http://127.0.0.1:8080",
                timeout_ms=10000,
                trained_model_path=str(temp_checkpoint_dir),
            )


def test_preservation_reference_loading_unchanged(tmp_path: Path) -> None:
    """Reference audio/text loading from config paths must remain unchanged."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Create reference files
    ref_wav = tmp_path / "reference.wav"
    ref_txt = tmp_path / "reference.txt"
    create_test_wav(ref_wav, duration_sec=5.0)
    ref_txt.write_text("Halo kak, selamat datang di live streaming kami")
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        mock_config.return_value.voice.clone_reference_wav = str(ref_wav)
        mock_config.return_value.voice.clone_reference_text = str(ref_txt)
        
        engine = FishSpeechEngine()
        engine._load_references()
        
        # Verify reference audio and text are loaded correctly
        assert engine._reference_audio_b64 is not None
        assert len(engine._reference_audio_b64) > 0
        assert engine._reference_text == "Halo kak, selamat datang di live streaming kami"
    
    reset_voice_runtime_state()


def test_preservation_missing_reference_raises_error(tmp_path: Path) -> None:
    """Missing reference files should still raise RuntimeError as before."""
    from src.voice.engine import FishSpeechEngine
    from src.voice.runtime_state import reset_voice_runtime_state
    
    reset_voice_runtime_state()
    
    # Reference files don't exist
    ref_wav = tmp_path / "nonexistent.wav"
    ref_txt = tmp_path / "nonexistent.txt"
    
    with patch("src.voice.engine.get_config") as mock_config:
        mock_config.return_value.voice.trained_model_path = None
        mock_config.return_value.voice.training_dataset_path = "assets/voice/training_dataset/"
        mock_config.return_value.voice.clone_reference_wav = str(ref_wav)
        mock_config.return_value.voice.clone_reference_text = str(ref_txt)
        
        engine = FishSpeechEngine()
        
        with pytest.raises(RuntimeError, match="Voice clone reference"):
            engine._load_references()
    
    reset_voice_runtime_state()

