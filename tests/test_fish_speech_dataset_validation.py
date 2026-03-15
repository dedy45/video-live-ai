"""Unit tests for Fish Speech dataset validation functions (Task 3.4)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.setup_fish_speech import (
    prepare_reference_audio,
    prepare_training_dataset,
    validate_reference_dataset,
)


class TestDatasetValidation:
    """Test dataset validation functions."""

    def test_validate_reference_dataset_with_existing_files(self, tmp_path: Path) -> None:
        """Test validation with existing Phase 1 files."""
        # Create mock voice directory structure
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        
        # Create mock WAV files (we'll mock wave.open to avoid actual audio)
        (voice_dir / "test1.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "test2.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        
        # Mock wave.open to return controlled audio properties
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 44100 * 60  # 60 seconds
        mock_wave_file.getframerate.return_value = 44100
        mock_wave_file.getnchannels.return_value = 2
        mock_wave_file.getsampwidth.return_value = 2  # 16-bit
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = validate_reference_dataset(tmp_path)
        
        assert isinstance(result, dict)
        assert "valid" in result
        assert "total_duration_min" in result
        assert "file_count" in result
        assert "issues" in result
        assert "files" in result
        assert "guidance" in result
        
        # With 2 files of 60s each = 2 min total (insufficient for training)
        assert result["file_count"] == 2
        assert result["total_duration_min"] == 2.0
        assert result["valid"] is False
        assert any("insufficient" in issue.lower() for issue in result["issues"])

    def test_validate_reference_dataset_no_files(self, tmp_path: Path) -> None:
        """Test validation when no WAV files exist."""
        result = validate_reference_dataset(tmp_path)
        
        assert result["valid"] is False
        assert result["file_count"] == 0
        assert result["total_duration_min"] == 0.0
        assert any("No WAV files found" in issue for issue in result["issues"])
        assert "Record 30-60 minutes" in result["guidance"]

    def test_validate_reference_dataset_quality_checks(self, tmp_path: Path) -> None:
        """Test quality checks for sample rate, channels, bit depth."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "low_quality.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        
        # Mock low-quality audio
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 8000 * 30  # 30 seconds
        mock_wave_file.getframerate.return_value = 8000  # Low sample rate
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 1  # 8-bit
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = validate_reference_dataset(tmp_path)
        
        # Should flag low sample rate
        assert any("sample rate" in issue.lower() and "too low" in issue.lower() 
                   for issue in result["issues"])

    def test_validate_reference_dataset_sufficient_duration(self, tmp_path: Path) -> None:
        """Test validation with sufficient duration (30+ minutes)."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "long_audio.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        
        # Mock 35 minutes of audio
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 35  # 35 minutes
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2  # 16-bit
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = validate_reference_dataset(tmp_path)
        
        assert result["total_duration_min"] == 35.0
        assert result["valid"] is True
        assert "meets quality requirements" in result["guidance"].lower()

    def test_prepare_reference_audio_creates_training_dir(self, tmp_path: Path) -> None:
        """Test that prepare_reference_audio creates training directory."""
        result = prepare_reference_audio(tmp_path)
        
        training_dir = tmp_path / "assets" / "voice" / "training_dataset"
        assert training_dir.exists()
        assert result["training_dir_exists"] is True

    def test_prepare_reference_audio_checks_transcripts(self, tmp_path: Path) -> None:
        """Test transcript validation in prepare_reference_audio."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        
        # Create WAV file without transcript
        (voice_dir / "audio1.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        
        # Create WAV file with transcript
        (voice_dir / "audio2.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "audio2.txt").write_text("This is a transcript", encoding="utf-8")
        
        # Mock wave.open
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 30
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_reference_audio(tmp_path)
        
        # Should flag missing transcript for audio1.wav
        assert any("audio1.wav" in issue and "missing transcript" in issue.lower() 
                   for issue in result["transcript_issues"])
        assert result["ready_for_training"] is False

    def test_prepare_reference_audio_empty_transcript(self, tmp_path: Path) -> None:
        """Test detection of empty transcript files."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        
        (voice_dir / "audio.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "audio.txt").write_text("", encoding="utf-8")  # Empty
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 30
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_reference_audio(tmp_path)
        
        assert any("empty" in issue.lower() for issue in result["transcript_issues"])


class TestDatasetValidationIntegration:
    """Integration tests with actual project files."""

    def test_validate_existing_phase1_files(self) -> None:
        """Test validation reports insufficient duration for Phase 1 files."""
        from scripts.setup_fish_speech import PROJECT_ROOT
        
        result = validate_reference_dataset(PROJECT_ROOT)
        
        # Phase 1 files total ~3.5 minutes
        assert result["file_count"] >= 4
        assert 3.0 <= result["total_duration_min"] <= 4.0
        assert result["valid"] is False
        assert "Quick Clone" in result["guidance"]
        assert "insufficient for fine-tuning" in result["guidance"]

    def test_prepare_dataset_with_phase1_files(self) -> None:
        """Test prepare_reference_audio with Phase 1 files."""
        from scripts.setup_fish_speech import PROJECT_ROOT
        
        result = prepare_reference_audio(PROJECT_ROOT)
        
        assert result["training_dir_exists"] is True
        assert result["ready_for_training"] is False
        
        # Should have transcript issues for christine.wav and roma.wav
        transcript_issues = result["transcript_issues"]
        assert any("christine.wav" in issue for issue in transcript_issues)
        assert any("roma.wav" in issue for issue in transcript_issues)


class TestDatasetStatistics:
    """Test dataset statistics reporting."""

    def test_file_statistics_include_all_fields(self, tmp_path: Path) -> None:
        """Test that file statistics include all required fields."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "test.wav").write_bytes(b"RIFF" + b"\x00" * 1024)
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = validate_reference_dataset(tmp_path)
        
        assert len(result["files"]) == 1
        file_info = result["files"][0]
        
        assert "path" in file_info
        assert "duration_sec" in file_info
        assert "sample_rate" in file_info
        assert "channels" in file_info
        assert "bit_depth" in file_info
        assert "size_mb" in file_info

    def test_guidance_messages_for_different_durations(self, tmp_path: Path) -> None:
        """Test guidance messages change based on dataset duration."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "test.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        
        mock_wave_file = Mock()
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            # Test < 3 minutes
            mock_wave_file.getnframes.return_value = 16000 * 60 * 2  # 2 min
            result = validate_reference_dataset(tmp_path)
            assert "Record 30-60 min" in result["guidance"]
            
            # Test 3-30 minutes
            mock_wave_file.getnframes.return_value = 16000 * 60 * 5  # 5 min
            result = validate_reference_dataset(tmp_path)
            assert "Quick Clone" in result["guidance"]
            assert "insufficient for fine-tuning" in result["guidance"]
            
            # Test 30+ minutes
            mock_wave_file.getnframes.return_value = 16000 * 60 * 35  # 35 min
            result = validate_reference_dataset(tmp_path)
            assert "meets quality requirements" in result["guidance"].lower()
