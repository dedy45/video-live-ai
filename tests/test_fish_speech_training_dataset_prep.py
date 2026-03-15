"""Unit tests for Fish Speech training dataset preparation (Task 3.5b)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from scripts.setup_fish_speech import prepare_training_dataset


class TestPrepareTrainingDataset:
    """Test prepare_training_dataset function."""

    def test_prepare_training_dataset_no_files(self, tmp_path: Path) -> None:
        """Test preparation when no WAV files exist."""
        result = prepare_training_dataset(tmp_path)
        
        assert result["valid"] is False
        assert result["file_count"] == 0
        assert result["total_duration_min"] == 0.0
        assert result["segmentation_needed"] is False
        assert result["format_conversion_needed"] is False
        assert result["transcript_alignment_valid"] is False
        assert any("No WAV files found" in issue for issue in result["issues"])
        assert "Record 30-60 minutes" in result["guidance"]

    def test_prepare_training_dataset_insufficient_duration(self, tmp_path: Path) -> None:
        """Test preparation with insufficient duration (< 30 min)."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "short.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "short.txt").write_text("Short transcript", encoding="utf-8")
        
        # Mock 5 minutes of audio
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 5  # 5 minutes
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["valid"] is False
        assert result["total_duration_min"] == 5.0
        assert result["transcript_alignment_valid"] is True
        assert any("insufficient for training" in issue.lower() for issue in result["issues"])
        assert "Quick Clone" in result["guidance"]

    def test_prepare_training_dataset_sufficient_duration(self, tmp_path: Path) -> None:
        """Test preparation with sufficient duration (30-60 min)."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "long.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "long.txt").write_text("Long transcript content", encoding="utf-8")
        
        # Mock 35 minutes of audio at 16kHz mono
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 35  # 35 minutes
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["valid"] is True
        assert result["total_duration_min"] == 35.0
        assert result["segmentation_needed"] is True  # File > 30s
        assert result["format_conversion_needed"] is False  # Already 16kHz mono
        assert result["transcript_alignment_valid"] is True
        assert "meets duration and quality requirements" in result["guidance"]


    def test_prepare_training_dataset_segmentation_needed(self, tmp_path: Path) -> None:
        """Test detection of files needing segmentation (> 30s)."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "long_file.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "long_file.txt").write_text("Long file transcript", encoding="utf-8")
        
        # Mock 45 seconds of audio (exceeds 30s chunk size)
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 45  # 45 seconds
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["segmentation_needed"] is True
        assert any("exceeds recommended 30s chunk size" in issue for issue in result["issues"])
        assert any("Segmentation recommended" in action for action in result["actions_taken"])

    def test_prepare_training_dataset_format_conversion_needed(self, tmp_path: Path) -> None:
        """Test detection of files needing format conversion."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "wrong_format.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "wrong_format.txt").write_text("Transcript", encoding="utf-8")
        
        # Mock 10 minutes at 44.1kHz stereo (needs conversion)
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 44100 * 60 * 10  # 10 minutes
        mock_wave_file.getframerate.return_value = 44100  # Should be 16kHz
        mock_wave_file.getnchannels.return_value = 2  # Should be mono
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["format_conversion_needed"] is True
        assert any("should be resampled to 16kHz" in issue for issue in result["issues"])
        assert any("should be converted to mono" in issue for issue in result["issues"])
        assert any("Format conversion recommended" in action for action in result["actions_taken"])

    def test_prepare_training_dataset_missing_transcripts(self, tmp_path: Path) -> None:
        """Test detection of missing transcript files."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "audio1.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        # No transcript for audio1.wav
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 10
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["transcript_alignment_valid"] is False
        assert any("missing transcript file" in issue for issue in result["issues"])
        assert any("Transcript alignment required" in action for action in result["actions_taken"])

    def test_prepare_training_dataset_empty_transcript(self, tmp_path: Path) -> None:
        """Test detection of empty transcript files."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "audio.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "audio.txt").write_text("", encoding="utf-8")  # Empty
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 10
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["transcript_alignment_valid"] is False
        assert any("transcript is empty" in issue for issue in result["issues"])

    def test_prepare_training_dataset_short_transcript(self, tmp_path: Path) -> None:
        """Test detection of too-short transcript files."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "audio.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "audio.txt").write_text("Hi", encoding="utf-8")  # Too short
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 10
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["transcript_alignment_valid"] is False
        assert any("transcript too short" in issue for issue in result["issues"])


    def test_prepare_training_dataset_multiple_files(self, tmp_path: Path) -> None:
        """Test preparation with multiple files totaling 30+ minutes."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        
        # Create 3 files of 12 minutes each = 36 minutes total
        for i in range(3):
            (voice_dir / f"segment_{i}.wav").write_bytes(b"RIFF" + b"\x00" * 100)
            (voice_dir / f"segment_{i}.txt").write_text(f"Transcript {i}", encoding="utf-8")
        
        # Mock 12 minutes per file
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 12  # 12 minutes
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["valid"] is True
        assert result["file_count"] == 3
        assert result["total_duration_min"] == 36.0
        assert result["transcript_alignment_valid"] is True
        assert "meets duration and quality requirements" in result["guidance"]

    def test_prepare_training_dataset_exceeds_maximum(self, tmp_path: Path) -> None:
        """Test preparation with duration exceeding 60 min maximum."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "very_long.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "very_long.txt").write_text("Very long transcript", encoding="utf-8")
        
        # Mock 75 minutes of audio
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 75  # 75 minutes
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["total_duration_min"] == 75.0
        assert any("exceeds recommended 60 min maximum" in issue for issue in result["issues"])

    def test_prepare_training_dataset_low_sample_rate(self, tmp_path: Path) -> None:
        """Test detection of low sample rate (< 16kHz)."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "low_rate.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (voice_dir / "low_rate.txt").write_text("Transcript", encoding="utf-8")
        
        # Mock 35 minutes at 8kHz (too low)
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 8000 * 60 * 35
        mock_wave_file.getframerate.return_value = 8000  # Too low
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert any("sample rate" in issue.lower() and "too low" in issue.lower() 
                   for issue in result["issues"])

    def test_prepare_training_dataset_file_statistics(self, tmp_path: Path) -> None:
        """Test that file statistics are included in result."""
        voice_dir = tmp_path / "assets" / "voice"
        voice_dir.mkdir(parents=True)
        (voice_dir / "test.wav").write_bytes(b"RIFF" + b"\x00" * 1024)
        (voice_dir / "test.txt").write_text("Test transcript", encoding="utf-8")
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 35
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert "files" in result
        assert len(result["files"]) == 1
        file_info = result["files"][0]
        
        assert "path" in file_info
        assert "duration_sec" in file_info
        assert "sample_rate" in file_info
        assert "channels" in file_info
        assert "bit_depth" in file_info
        assert "size_mb" in file_info

    def test_prepare_training_dataset_training_dir_structure(self, tmp_path: Path) -> None:
        """Test that function works with training_dataset subdirectory."""
        training_dir = tmp_path / "assets" / "voice" / "training_dataset"
        training_dir.mkdir(parents=True)
        
        (training_dir / "segment_001.wav").write_bytes(b"RIFF" + b"\x00" * 100)
        (training_dir / "segment_001.txt").write_text("Segment 1 transcript", encoding="utf-8")
        
        mock_wave_file = Mock()
        mock_wave_file.getnframes.return_value = 16000 * 60 * 35
        mock_wave_file.getframerate.return_value = 16000
        mock_wave_file.getnchannels.return_value = 1
        mock_wave_file.getsampwidth.return_value = 2
        
        with patch("wave.open") as mock_open:
            mock_open.return_value.__enter__.return_value = mock_wave_file
            
            result = prepare_training_dataset(tmp_path)
        
        assert result["file_count"] == 1
        assert result["valid"] is True


class TestPrepareTrainingDatasetIntegration:
    """Integration tests with actual project files."""

    def test_prepare_training_dataset_with_phase1_files(self) -> None:
        """Test prepare_training_dataset with Phase 1 files."""
        from scripts.setup_fish_speech import PROJECT_ROOT
        
        result = prepare_training_dataset(PROJECT_ROOT)
        
        # Phase 1 files total ~3.5 minutes
        assert result["file_count"] >= 4
        assert 3.0 <= result["total_duration_min"] <= 4.0
        assert result["valid"] is False
        assert "Quick Clone" in result["guidance"]
        assert "insufficient for fine-tuning" in result["guidance"]
        
        # Should flag missing transcripts
        assert result["transcript_alignment_valid"] is False
        assert any("Transcript alignment required" in action for action in result["actions_taken"])
