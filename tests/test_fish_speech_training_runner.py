"""Tests for Fish Speech training job runner.

Tests Task 3.5c implementation:
- run_training_job() function
- Training progress tracking
- Checkpoint saving
- Training completion handling
- Error handling
- Training queue integration
"""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest


@pytest.fixture
def mock_project_root(tmp_path: Path) -> Path:
    """Create a mock project root with necessary structure."""
    project_root = tmp_path / "videoliveai"
    project_root.mkdir()
    
    # Create directory structure
    (project_root / "external" / "fish-speech" / "upstream" / "fish-speech").mkdir(parents=True)
    (project_root / "external" / "fish-speech" / "checkpoints" / "fish-speech-1.5").mkdir(parents=True)
    (project_root / "external" / "fish-speech" / "runtime").mkdir(parents=True)
    (project_root / "assets" / "voice" / "training_dataset").mkdir(parents=True)
    (project_root / "src" / "config").mkdir(parents=True)
    (project_root / "src" / "voice").mkdir(parents=True)
    (project_root / "src" / "data").mkdir(parents=True)
    
    # Create venv python
    venv_python = project_root / "external" / "fish-speech" / "runtime" / ".venv" / "Scripts" / "python.exe"
    venv_python.parent.mkdir(parents=True)
    venv_python.write_text("mock python")
    
    # Create checkpoint files
    checkpoint_dir = project_root / "external" / "fish-speech" / "checkpoints" / "fish-speech-1.5"
    (checkpoint_dir / "model.pth").write_text("mock model")
    (checkpoint_dir / "config.json").write_text("{}")
    (checkpoint_dir / "tokenizer.tiktoken").write_text("mock tokenizer")
    (checkpoint_dir / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_text("mock decoder")
    
    return project_root


@pytest.fixture
def mock_config():
    """Mock config with training settings."""
    config = Mock()
    config.voice.training_enabled = True
    config.voice.training_epochs = 10
    config.voice.training_batch_size = 4
    config.voice.training_learning_rate = 1e-4
    config.voice.training_dataset_path = "assets/voice/training_dataset/"
    config.voice.fish_speech_base_url = "http://127.0.0.1:8080"
    config.voice.fish_speech_timeout_ms = 30000
    config.voice.clone_reference_wav = "assets/voice/reference.wav"
    config.voice.clone_reference_text = "assets/voice/reference.txt"
    config.voice.trained_model_path = None
    return config


def test_run_training_job_validates_command_build(mock_project_root: Path, mock_config):
    """Test that run_training_job validates training command build."""
    from scripts.setup_fish_speech import run_training_job, resolve_layout
    
    layout = resolve_layout(mock_project_root)
    
    # Mock config to disable training
    mock_config.voice.training_enabled = False
    
    with patch("src.config.get_config", return_value=mock_config):
        result = run_training_job(layout, mock_project_root)
    
    assert result["success"] is False
    assert result["status"] == "failed"
    assert "training_enabled" in result["error"].lower() or "disabled" in result["error"].lower()
    assert result["epochs_completed"] == 0


def test_parse_training_log_extracts_epochs(mock_project_root: Path):
    """Test that _parse_training_log extracts epoch count correctly."""
    from scripts.setup_fish_speech import _parse_training_log
    
    log_file = mock_project_root / "training.log"
    log_file.write_text("""
    Starting training...
    Epoch 1/100 - loss: 0.5
    Epoch 2/100 - loss: 0.4
    Epoch 5/100 - loss: 0.3
    """)
    
    result = _parse_training_log(log_file, 100)
    
    assert result["epochs_completed"] == 5


def test_parse_training_log_extracts_validation_loss(mock_project_root: Path):
    """Test that _parse_training_log extracts validation loss correctly."""
    from scripts.setup_fish_speech import _parse_training_log
    
    log_file = mock_project_root / "training.log"
    log_file.write_text("""
    Epoch 1/100 - val_loss: 0.5
    Epoch 2/100 - val_loss: 0.4
    Epoch 5/100 - val_loss: 0.123
    """)
    
    result = _parse_training_log(log_file, 100)
    
    assert result["validation_loss"] == 0.123


def test_parse_training_log_handles_missing_file(mock_project_root: Path):
    """Test that _parse_training_log handles missing log file."""
    from scripts.setup_fish_speech import _parse_training_log
    
    log_file = mock_project_root / "nonexistent.log"
    
    result = _parse_training_log(log_file, 100)
    
    assert result["epochs_completed"] == 0
    assert result["validation_loss"] is None


def test_parse_training_log_handles_alternative_epoch_format(mock_project_root: Path):
    """Test that _parse_training_log handles alternative epoch format."""
    from scripts.setup_fish_speech import _parse_training_log
    
    log_file = mock_project_root / "training.log"
    log_file.write_text("""
    epoch: 1
    epoch: 2
    epoch: 10
    validation loss: 0.234
    """)
    
    result = _parse_training_log(log_file, 100)
    
    assert result["epochs_completed"] == 10
    assert result["validation_loss"] == 0.234


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
