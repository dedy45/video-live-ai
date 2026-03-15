#!/usr/bin/env python3
"""Tests for Fish Speech status reporting with training status (Task 3.6)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def test_build_status_payload_includes_training_fields():
    """Test that build_status_payload includes all required training status fields."""
    from scripts.setup_fish_speech import build_status_payload
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create minimal directory structure
        voice_dir = project_root / "assets" / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal reference files
        (voice_dir / "reference.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "reference.txt").write_text("Test reference text", encoding="utf-8")
        
        # Mock dependencies
        with patch("scripts.setup_fish_speech.check_server_reachable", return_value=False), \
             patch("scripts.setup_fish_speech.check_config_alignment", return_value=(True, "test")), \
             patch("scripts.setup_fish_speech.get_fish_speech_url", return_value="http://127.0.0.1:8080"), \
             patch("src.config.get_config") as mock_config:
            
            # Mock config
            mock_cfg = MagicMock()
            mock_cfg.voice.training_enabled = True
            mock_cfg.voice.training_epochs = 100
            mock_config.return_value = mock_cfg
            
            # Build status payload
            payload = build_status_payload(project_root)
            
            # Verify training section exists
            assert "training" in payload
            training = payload["training"]
            
            # Verify required fields exist
            assert "status" in training
            assert "enabled" in training
            assert "trained_model" in training
            assert "dataset" in training
            assert "active_job" in training
            assert "progress" in training
            
            # Verify training status is one of allowed values
            assert training["status"] in [
                "not_started", "queued", "in_progress", "completed", "failed",
                "ready", "dataset_insufficient"
            ]
            
            # Verify trained_model structure
            trained_model = training["trained_model"]
            assert "exists" in trained_model
            assert "path" in trained_model
            assert "valid" in trained_model
            assert "message" in trained_model
            
            # Verify dataset structure
            dataset = training["dataset"]
            assert "valid" in dataset
            assert "total_duration_min" in dataset
            assert "file_count" in dataset
            assert "ready_for_training" in dataset
            assert "guidance" in dataset


def test_build_status_payload_preserves_existing_fields():
    """Test that enhancement preserves all existing status payload fields."""
    from scripts.setup_fish_speech import build_status_payload
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create minimal directory structure
        voice_dir = project_root / "assets" / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal reference files
        (voice_dir / "reference.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "reference.txt").write_text("Test reference text", encoding="utf-8")
        
        # Mock dependencies
        with patch("scripts.setup_fish_speech.check_server_reachable", return_value=True), \
             patch("scripts.setup_fish_speech.check_config_alignment", return_value=(True, "test")), \
             patch("scripts.setup_fish_speech.get_fish_speech_url", return_value="http://127.0.0.1:8080"), \
             patch("src.config.get_config") as mock_config:
            
            # Mock config
            mock_cfg = MagicMock()
            mock_cfg.voice.training_enabled = False
            mock_config.return_value = mock_cfg
            
            # Build status payload
            payload = build_status_payload(project_root)
            
            # Verify all existing top-level sections exist
            assert "paths" in payload
            assert "assets" in payload
            assert "config" in payload
            assert "runtime" in payload
            assert "training" in payload
            
            # Verify paths section structure
            paths = payload["paths"]
            assert "root" in paths
            assert "upstream" in paths
            assert "checkout" in paths
            assert "checkpoints" in paths
            assert "runtime" in paths
            assert "venv" in paths
            assert "venv_python" in paths
            assert "pid_file" in paths
            assert "log_file" in paths
            
            # Verify assets section structure
            assets = payload["assets"]
            assert "reference_wav" in assets
            assert "reference_text" in assets
            assert "checkpoint_root_exists" in assets
            assert "decoder_exists" in assets
            assert "checkout_exists" in assets
            assert "venv_python_exists" in assets
            
            # Verify config section structure
            config = payload["config"]
            assert "aligned" in config
            assert "message" in config
            assert "base_url" in config
            
            # Verify runtime section structure
            runtime = payload["runtime"]
            assert "pid" in runtime
            assert "pid_running" in runtime
            assert "reachable" in runtime
            assert "listen" in runtime
            assert "status" in runtime


def test_build_status_payload_json_serializable():
    """Test that status payload is JSON serializable."""
    from scripts.setup_fish_speech import build_status_payload
    
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create minimal directory structure
        voice_dir = project_root / "assets" / "voice"
        voice_dir.mkdir(parents=True, exist_ok=True)
        
        # Create minimal reference files
        (voice_dir / "reference.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "reference.txt").write_text("Test reference text", encoding="utf-8")
        
        # Mock dependencies
        with patch("scripts.setup_fish_speech.check_server_reachable", return_value=False), \
             patch("scripts.setup_fish_speech.check_config_alignment", return_value=(True, "test")), \
             patch("scripts.setup_fish_speech.get_fish_speech_url", return_value="http://127.0.0.1:8080"), \
             patch("src.config.get_config") as mock_config:
            
            # Mock config
            mock_cfg = MagicMock()
            mock_cfg.voice.training_enabled = True
            mock_cfg.voice.training_epochs = 100
            mock_config.return_value = mock_cfg
            
            # Build status payload
            payload = build_status_payload(project_root)
            
            # Verify payload is JSON serializable
            json_str = json.dumps(payload, indent=2)
            assert json_str is not None
            assert len(json_str) > 0
            
            # Verify can be deserialized
            deserialized = json.loads(json_str)
            assert deserialized == payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
