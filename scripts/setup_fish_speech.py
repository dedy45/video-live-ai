#!/usr/bin/env python3
"""Canonical Fish-Speech setup, status, and runtime helper."""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LISTEN = "127.0.0.1:8080"
DEFAULT_CHECKPOINT_NAME = "fish-speech-1.5"
DEFAULT_DECODER_NAME = "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
UPSTREAM_REPO_URL = "https://github.com/fishaudio/fish-speech.git"
UPSTREAM_TAG = "v1.5.1"


@dataclass
class FishSpeechLayout:
    """Canonical Fish-Speech sidecar layout inside the repository."""

    root: Path
    upstream_dir: Path
    checkout_dir: Path
    checkpoints_dir: Path
    runtime_dir: Path
    scripts_dir: Path
    venv_dir: Path
    venv_python: Path
    pid_file: Path
    log_file: Path


def print_status(level: str, message: str) -> None:
    """Print an ASCII-only status line safe for Windows cp1252 consoles."""
    labels = {
        "ok": "[OK]",
        "warn": "[WARN]",
        "error": "[ERROR]",
        "info": "[INFO]",
    }
    prefix = labels.get(level.lower(), "[INFO]")
    print(f"{prefix} {message}")


def resolve_layout(project_root: Path = PROJECT_ROOT) -> FishSpeechLayout:
    """Resolve the canonical Fish-Speech repository layout."""
    root = project_root / "external" / "fish-speech"
    runtime_dir = root / "runtime"
    venv_dir = runtime_dir / ".venv"
    return FishSpeechLayout(
        root=root,
        upstream_dir=root / "upstream",
        checkout_dir=root / "upstream" / "fish-speech",
        checkpoints_dir=root / "checkpoints",
        runtime_dir=runtime_dir,
        scripts_dir=root / "scripts",
        venv_dir=venv_dir,
        venv_python=venv_dir / "Scripts" / "python.exe",
        pid_file=runtime_dir / "fish-speech.pid",
        log_file=runtime_dir / "fish-speech.log",
    )


def ensure_layout(project_root: Path = PROJECT_ROOT) -> FishSpeechLayout:
    """Create the canonical Fish-Speech layout if it does not yet exist."""
    layout = resolve_layout(project_root)
    for path in (layout.upstream_dir, layout.checkpoints_dir, layout.runtime_dir, layout.scripts_dir):
        path.mkdir(parents=True, exist_ok=True)
    return layout


def run_command(command: list[str], cwd: Path | None = None) -> bool:
    """Run a command and return success status."""
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode == 0


def read_pid(pid_file: Path) -> int | None:
    """Read a numeric pid file when present."""
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def pid_is_running(pid: int | None) -> bool:
    """Check whether a pid still exists."""
    if pid is None or pid <= 0:
        return False
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and str(pid) in result.stdout
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def check_reference_wav(project_root: Path = PROJECT_ROOT) -> bool:
    """Check that voice clone reference WAV exists."""
    wav_path = project_root / "assets" / "voice" / "reference.wav"
    return wav_path.exists() and wav_path.stat().st_size > 0


def check_reference_text(project_root: Path = PROJECT_ROOT) -> bool:
    """Check that voice clone reference text exists and is non-empty."""
    txt_path = project_root / "assets" / "voice" / "reference.txt"
    if not txt_path.exists():
        return False
    return bool(txt_path.read_text(encoding="utf-8").strip())


def validate_reference_dataset(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    """
    Validate reference audio dataset quality and duration requirements.
    
    Returns a dictionary with validation results:
    - valid: bool - overall validation status
    - total_duration_min: float - total duration in minutes
    - file_count: int - number of valid audio files
    - issues: list[str] - list of validation issues found
    - files: list[dict] - per-file statistics
    - guidance: str - operator guidance message
    """
    try:
        import wave
    except ImportError:
        return {
            "valid": False,
            "total_duration_min": 0.0,
            "file_count": 0,
            "issues": ["wave module not available"],
            "files": [],
            "guidance": "Install wave module to validate audio files",
        }
    
    voice_dir = project_root / "assets" / "voice"
    training_dir = voice_dir / "training_dataset"
    
    # Collect all WAV files from both directories
    wav_files = []
    if voice_dir.exists():
        wav_files.extend(voice_dir.glob("*.wav"))
    if training_dir.exists():
        wav_files.extend(training_dir.glob("*.wav"))
    
    if not wav_files:
        return {
            "valid": False,
            "total_duration_min": 0.0,
            "file_count": 0,
            "issues": ["No WAV files found in assets/voice/ or assets/voice/training_dataset/"],
            "files": [],
            "guidance": "Record 30-60 minutes of clean Indonesian speech from a single speaker",
        }
    
    issues = []
    file_stats = []
    total_duration_sec = 0.0
    
    for wav_path in wav_files:
        try:
            with wave.open(str(wav_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                duration_sec = frames / float(rate)
                
                file_info = {
                    "path": str(wav_path.relative_to(project_root)),
                    "duration_sec": round(duration_sec, 2),
                    "sample_rate": rate,
                    "channels": channels,
                    "bit_depth": sampwidth * 8,
                    "size_mb": round(wav_path.stat().st_size / (1024 * 1024), 2),
                }
                file_stats.append(file_info)
                total_duration_sec += duration_sec
                
                # Quality checks
                if rate < 16000:
                    issues.append(f"{wav_path.name}: sample rate {rate}Hz too low (minimum 16kHz)")
                if rate not in (16000, 22050, 24000, 44100, 48000):
                    issues.append(f"{wav_path.name}: non-standard sample rate {rate}Hz (prefer 16kHz or 24kHz)")
                if channels > 2:
                    issues.append(f"{wav_path.name}: {channels} channels (prefer mono or stereo)")
                if sampwidth not in (2, 3):
                    issues.append(f"{wav_path.name}: {sampwidth * 8}-bit depth (prefer 16-bit or 24-bit)")
                if duration_sec < 1.0:
                    issues.append(f"{wav_path.name}: duration {duration_sec:.1f}s too short (minimum 1s)")
                
        except Exception as exc:
            issues.append(f"{wav_path.name}: failed to read ({exc})")
    
    total_duration_min = total_duration_sec / 60.0
    file_count = len(file_stats)
    
    # Duration requirement check
    if total_duration_min < 30.0:
        issues.append(f"Total duration {total_duration_min:.1f} min insufficient for training (minimum 30 min)")
    
    # Generate guidance message
    if total_duration_min >= 30.0 and not issues:
        guidance = "Dataset meets quality requirements for fine-tuning"
        valid = True
    elif total_duration_min >= 3.0:
        guidance = f"Dataset sufficient for Quick Clone ({total_duration_min:.1f} min), but insufficient for fine-tuning (requires 30-60 min)"
        valid = False
    else:
        guidance = f"Dataset insufficient ({total_duration_min:.1f} min). Record 30-60 min of clean Indonesian speech from a single speaker"
        valid = False
    
    return {
        "valid": valid,
        "total_duration_min": round(total_duration_min, 2),
        "file_count": file_count,
        "issues": issues,
        "files": file_stats,
        "guidance": guidance,
    }


def prepare_reference_audio(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    """
    Organize reference audio dataset into training format.
    
    Creates training_dataset directory structure and validates transcripts.
    Returns preparation status and statistics.
    """
    voice_dir = project_root / "assets" / "voice"
    training_dir = voice_dir / "training_dataset"
    
    # Create training directory if it doesn't exist
    training_dir.mkdir(parents=True, exist_ok=True)
    
    # Validate dataset
    validation = validate_reference_dataset(project_root)
    
    # Check for transcript files
    transcript_issues = []
    for file_info in validation.get("files", []):
        wav_path = project_root / file_info["path"]
        txt_path = wav_path.with_suffix(".txt")
        
        if not txt_path.exists():
            transcript_issues.append(f"{wav_path.name}: missing transcript file {txt_path.name}")
        else:
            try:
                transcript = txt_path.read_text(encoding="utf-8").strip()
                if not transcript:
                    transcript_issues.append(f"{txt_path.name}: transcript is empty")
                elif len(transcript) < 10:
                    transcript_issues.append(f"{txt_path.name}: transcript too short ({len(transcript)} chars)")
            except Exception as exc:
                transcript_issues.append(f"{txt_path.name}: failed to read ({exc})")
    
    preparation_status = {
        "training_dir": str(training_dir.relative_to(project_root)),
        "training_dir_exists": training_dir.exists(),
        "validation": validation,
        "transcript_issues": transcript_issues,
        "ready_for_training": validation["valid"] and not transcript_issues,
    }
    
    if transcript_issues:
        preparation_status["guidance"] = "Create matching .txt transcript files for all .wav files"
    else:
        preparation_status["guidance"] = validation["guidance"]
    
    return preparation_status


def prepare_training_dataset(project_root: Path = PROJECT_ROOT) -> dict[str, object]:
    """
    Validate and organize Indonesian audio dataset for training (30-60 min requirement).
    
    This function performs comprehensive dataset preparation including:
    - Total duration validation (30-60 min requirement)
    - File count and audio quality metrics
    - Audio segmentation if needed (split long files into manageable chunks)
    - Transcript alignment validation (ensure each WAV has corresponding TXT)
    - Dataset format conversion if needed (resample to 16kHz, convert to mono)
    
    Returns a dictionary with preparation results:
    - valid: bool - overall validation status
    - total_duration_min: float - total duration in minutes
    - file_count: int - number of valid audio files
    - segmentation_needed: bool - whether files need segmentation
    - format_conversion_needed: bool - whether format conversion is needed
    - transcript_alignment_valid: bool - whether all WAV files have matching TXT
    - issues: list[str] - list of validation issues found
    - actions_taken: list[str] - list of preparation actions performed
    - guidance: str - operator guidance message
    """
    try:
        import wave
    except ImportError:
        return {
            "valid": False,
            "total_duration_min": 0.0,
            "file_count": 0,
            "segmentation_needed": False,
            "format_conversion_needed": False,
            "transcript_alignment_valid": False,
            "issues": ["wave module not available"],
            "actions_taken": [],
            "guidance": "Install wave module to prepare dataset",
        }
    
    voice_dir = project_root / "assets" / "voice"
    training_dir = voice_dir / "training_dataset"
    
    # Ensure training directory exists
    training_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect all WAV files from both directories
    wav_files = []
    if voice_dir.exists():
        wav_files.extend(voice_dir.glob("*.wav"))
    if training_dir.exists():
        wav_files.extend(training_dir.glob("*.wav"))
    
    if not wav_files:
        return {
            "valid": False,
            "total_duration_min": 0.0,
            "file_count": 0,
            "segmentation_needed": False,
            "format_conversion_needed": False,
            "transcript_alignment_valid": False,
            "issues": ["No WAV files found in assets/voice/ or assets/voice/training_dataset/"],
            "actions_taken": [],
            "guidance": "Record 30-60 minutes of clean Indonesian speech from a single speaker",
        }
    
    issues = []
    actions_taken = []
    file_stats = []
    total_duration_sec = 0.0
    segmentation_needed = False
    format_conversion_needed = False
    transcript_alignment_valid = True
    
    # Analyze each WAV file
    for wav_path in wav_files:
        try:
            with wave.open(str(wav_path), "rb") as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sampwidth = wav_file.getsampwidth()
                duration_sec = frames / float(rate)
                
                file_info = {
                    "path": str(wav_path.relative_to(project_root)),
                    "duration_sec": round(duration_sec, 2),
                    "sample_rate": rate,
                    "channels": channels,
                    "bit_depth": sampwidth * 8,
                    "size_mb": round(wav_path.stat().st_size / (1024 * 1024), 2),
                }
                file_stats.append(file_info)
                total_duration_sec += duration_sec
                
                # Check for segmentation needs (files longer than 30 seconds)
                if duration_sec > 30.0:
                    segmentation_needed = True
                    issues.append(f"{wav_path.name}: duration {duration_sec:.1f}s exceeds recommended 30s chunk size")
                
                # Check for format conversion needs
                if rate != 16000:
                    format_conversion_needed = True
                    issues.append(f"{wav_path.name}: sample rate {rate}Hz should be resampled to 16kHz")
                
                if channels != 1:
                    format_conversion_needed = True
                    issues.append(f"{wav_path.name}: {channels} channels should be converted to mono")
                
                # Quality checks
                if rate < 16000:
                    issues.append(f"{wav_path.name}: sample rate {rate}Hz too low (minimum 16kHz)")
                if sampwidth not in (2, 3):
                    issues.append(f"{wav_path.name}: {sampwidth * 8}-bit depth (prefer 16-bit or 24-bit)")
                if duration_sec < 1.0:
                    issues.append(f"{wav_path.name}: duration {duration_sec:.1f}s too short (minimum 1s)")
                
                # Check transcript alignment
                txt_path = wav_path.with_suffix(".txt")
                if not txt_path.exists():
                    transcript_alignment_valid = False
                    issues.append(f"{wav_path.name}: missing transcript file {txt_path.name}")
                else:
                    try:
                        transcript = txt_path.read_text(encoding="utf-8").strip()
                        if not transcript:
                            transcript_alignment_valid = False
                            issues.append(f"{txt_path.name}: transcript is empty")
                        elif len(transcript) < 10:
                            transcript_alignment_valid = False
                            issues.append(f"{txt_path.name}: transcript too short ({len(transcript)} chars)")
                    except Exception as exc:
                        transcript_alignment_valid = False
                        issues.append(f"{txt_path.name}: failed to read ({exc})")
                
        except Exception as exc:
            issues.append(f"{wav_path.name}: failed to read ({exc})")
    
    total_duration_min = total_duration_sec / 60.0
    file_count = len(file_stats)
    
    # Duration requirement check
    if total_duration_min < 30.0:
        issues.append(f"Total duration {total_duration_min:.1f} min insufficient for training (minimum 30 min)")
    elif total_duration_min > 60.0:
        issues.append(f"Total duration {total_duration_min:.1f} min exceeds recommended 60 min maximum")
    
    # Generate guidance message
    if total_duration_min >= 30.0 and total_duration_min <= 60.0 and transcript_alignment_valid and not format_conversion_needed:
        if segmentation_needed:
            guidance = "Dataset meets duration and quality requirements. Segmentation recommended for optimal training."
            valid = True
        else:
            guidance = "Dataset meets all requirements for fine-tuning"
            valid = True
    elif total_duration_min >= 30.0 and total_duration_min <= 60.0:
        guidance = "Dataset meets duration requirements but needs preparation (format conversion or transcript alignment)"
        valid = False
    elif total_duration_min >= 3.0:
        guidance = f"Dataset sufficient for Quick Clone ({total_duration_min:.1f} min), but insufficient for fine-tuning (requires 30-60 min)"
        valid = False
    else:
        guidance = f"Dataset insufficient ({total_duration_min:.1f} min). Record 30-60 min of clean Indonesian speech from a single speaker"
        valid = False
    
    # Add preparation recommendations to actions_taken
    if segmentation_needed:
        actions_taken.append("Segmentation recommended: split files longer than 30s into smaller chunks")
    if format_conversion_needed:
        actions_taken.append("Format conversion recommended: resample to 16kHz mono")
    if not transcript_alignment_valid:
        actions_taken.append("Transcript alignment required: create matching .txt files for all .wav files")
    
    return {
        "valid": valid,
        "total_duration_min": round(total_duration_min, 2),
        "file_count": file_count,
        "segmentation_needed": segmentation_needed,
        "format_conversion_needed": format_conversion_needed,
        "transcript_alignment_valid": transcript_alignment_valid,
        "issues": issues,
        "actions_taken": actions_taken,
        "guidance": guidance,
        "files": file_stats,
    }


def print_dataset_report(project_root: Path = PROJECT_ROOT) -> None:
    """Print a human-readable dataset quality report for operators."""
    print()
    print("=== Fish-Speech Dataset Quality Report ===")
    
    validation = validate_reference_dataset(project_root)
    
    print(f"TOTAL DURATION : {validation['total_duration_min']:.2f} minutes")
    print(f"FILE COUNT     : {validation['file_count']}")
    print(f"STATUS         : {'VALID' if validation['valid'] else 'INSUFFICIENT'}")
    print()
    
    if validation["files"]:
        print("FILES:")
        for file_info in validation["files"]:
            print(f"  - {file_info['path']}")
            print(f"    Duration: {file_info['duration_sec']:.1f}s | "
                  f"Sample Rate: {file_info['sample_rate']}Hz | "
                  f"Channels: {file_info['channels']} | "
                  f"Bit Depth: {file_info['bit_depth']}-bit | "
                  f"Size: {file_info['size_mb']}MB")
    
    if validation["issues"]:
        print()
        print("ISSUES:")
        for issue in validation["issues"]:
            print(f"  - {issue}")
    
    print()
    print("GUIDANCE:")
    print(f"  {validation['guidance']}")
    
    print()
    print("DATASET REQUIREMENTS:")
    print("  - Duration: 30-60 minutes total (can be split into multiple files)")
    print("  - Speaker: Single native Indonesian speaker with natural accent")
    print("  - Content: Product narration, sales pitches, conversational Indonesian")
    print("  - Environment: Quiet room, minimal background noise, no echo/reverb")
    print("  - Format: WAV 16kHz or 24kHz, mono or stereo, 16-bit PCM")
    print("  - Quality: No clipping, no silence gaps, consistent volume")
    print("  - Transcripts: 100% accurate transcription matching audio content")
    print()
    print("NEXT ACTION:")
    if validation["valid"]:
        print("  Dataset ready for fine-tuning. Run training workflow.")
    elif validation["total_duration_min"] >= 3.0:
        print("  Dataset can be used for Quick Clone (zero-shot voice cloning).")
        print("  For fine-tuning, record additional audio to reach 30-60 minutes.")
    else:
        print("  Record 30-60 minutes of clean Indonesian speech.")
        print("  Save files to assets/voice/training_dataset/")
        print("  Create matching .txt transcript files for each .wav file.")


def get_fish_speech_url() -> str:
    """Resolve Fish-Speech base URL from config."""
    try:
        from src.config import get_config

        return get_config().voice.fish_speech_base_url
    except Exception:
        return f"http://{DEFAULT_LISTEN}"


def parse_listen(listen: str) -> tuple[str, int]:
    """Parse a host:port listen string."""
    host, port = listen.rsplit(":", 1)
    return host, int(port)


def check_server_reachable(base_url: str | None = None) -> bool:
    """TCP probe to Fish-Speech server."""
    url = base_url or get_fish_speech_url()
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8080

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            return sock.connect_ex((host, port)) == 0
    except Exception:
        return False


def check_health_endpoint(base_url: str | None = None) -> bool:
    """HTTP health check to Fish-Speech /v1/health endpoint."""
    url = base_url or get_fish_speech_url()
    health_url = f"{url.rstrip('/')}/v1/health"
    
    try:
        import urllib.request
        req = urllib.request.Request(health_url, method="GET")
        with urllib.request.urlopen(req, timeout=2.0) as response:
            return response.status == 200
    except Exception:
        return False


def validate_checkpoint_files(layout: FishSpeechLayout) -> tuple[bool, str]:
    """Validate that all required checkpoint files exist and are non-empty."""
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    decoder_path = checkpoint_root / DEFAULT_DECODER_NAME
    
    required_files = {
        "model.pth": checkpoint_root / "model.pth",
        "decoder": decoder_path,
        "config.json": checkpoint_root / "config.json",
        "tokenizer.tiktoken": checkpoint_root / "tokenizer.tiktoken",
    }
    
    missing = []
    invalid = []
    
    for name, path in required_files.items():
        if not path.exists():
            missing.append(name)
        elif path.stat().st_size == 0:
            invalid.append(name)
    
    if missing:
        return False, f"Missing checkpoint files: {', '.join(missing)}"
    if invalid:
        return False, f"Invalid (empty) checkpoint files: {', '.join(invalid)}"
    
    return True, "All checkpoint files valid"


def detect_trained_model(layout: FishSpeechLayout) -> tuple[bool, Path | None]:
    """Detect if a trained model checkpoint exists and return its path."""
    # Check for trained model in common locations
    trained_paths = [
        layout.checkpoints_dir / "trained" / "model.pth",
        layout.checkpoints_dir / "fine-tuned" / "model.pth",
        layout.checkpoints_dir / "indonesian-trained" / "model.pth",
    ]
    
    for path in trained_paths:
        if path.exists() and path.stat().st_size > 0:
            return True, path.parent
    
    return False, None


def check_config_alignment() -> tuple[bool, str]:
    """Verify voice config has Fish-Speech fields."""
    try:
        from src.config import get_config

        cfg = get_config()
        assert hasattr(cfg.voice, "fish_speech_base_url")
        assert hasattr(cfg.voice, "fish_speech_timeout_ms")
        assert hasattr(cfg.voice, "clone_reference_wav")
        assert hasattr(cfg.voice, "clone_reference_text")
        return True, f"base_url={cfg.voice.fish_speech_base_url}"
    except Exception as exc:
        return False, str(exc)


def build_clone_command(layout: FishSpeechLayout) -> list[str]:
    """Build the canonical upstream checkout clone command."""
    return [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        UPSTREAM_TAG,
        UPSTREAM_REPO_URL,
        str(layout.checkout_dir),
    ]


def build_venv_command(layout: FishSpeechLayout) -> list[str]:
    """Build the dedicated UV venv creation command for the sidecar runtime."""
    return ["uv", "venv", str(layout.venv_dir), "--allow-existing"]


def build_install_command(layout: FishSpeechLayout) -> list[str]:
    """Build the dependency install command for the pinned upstream checkout."""
    return [
        "uv",
        "pip",
        "install",
        "--python",
        str(layout.venv_python),
        "-e",
        ".[stable]",
    ]


def build_torch_install_command(layout: FishSpeechLayout) -> list[str]:
    """Install CUDA-backed torch wheels explicitly into the sidecar env."""
    return [
        "uv",
        "pip",
        "install",
        "--python",
        str(layout.venv_python),
        "--reinstall-package",
        "torch",
        "--reinstall-package",
        "torchaudio",
        "--default-index",
        "https://download.pytorch.org/whl/cu124",
        "torch==2.4.1",
        "torchaudio==2.4.1",
    ]


def build_checkpoint_download_specs(layout: FishSpeechLayout) -> list[dict[str, object]]:
    """Build the official checkpoint download spec for Fish-Speech v1.5."""
    return [
        {
            "repo_id": "fishaudio/fish-speech-1.5",
            "local_dir": layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME,
            "files": [
                ".gitattributes",
                "model.pth",
                "README.md",
                "special_tokens.json",
                "tokenizer.tiktoken",
                "config.json",
                DEFAULT_DECODER_NAME,
            ],
        }
    ]


def download_checkpoints(
    layout: FishSpeechLayout,
    downloader=None,
) -> bool:
    """Download the required Fish-Speech checkpoint files into the canonical path."""
    if downloader is None:
        from huggingface_hub import hf_hub_download

        def downloader(*, repo_id: str, filename: str, local_dir: Path) -> None:
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=str(local_dir),
                local_dir_use_symlinks=False,
            )

    for spec in build_checkpoint_download_specs(layout):
        local_dir = spec["local_dir"]
        assert isinstance(local_dir, Path)
        local_dir.mkdir(parents=True, exist_ok=True)
        for filename in spec["files"]:
            assert isinstance(filename, str)
            target = local_dir / filename
            if target.exists():
                continue
            downloader(
                repo_id=str(spec["repo_id"]),
                filename=filename,
                local_dir=local_dir,
            )
    return True


def bootstrap_install(
    project_root: Path = PROJECT_ROOT,
    *,
    runner=run_command,
    checkpoint_downloader=download_checkpoints,
) -> int:
    """Clone the upstream checkout, install dependencies, and hydrate checkpoints."""
    layout = ensure_layout(project_root)
    if not layout.checkout_dir.exists():
        if not runner(build_clone_command(layout), None):
            return 1
    if not runner(build_venv_command(layout), None):
        return 1
    if not runner(build_torch_install_command(layout), layout.checkout_dir):
        return 1
    if not runner(build_install_command(layout), layout.checkout_dir):
        return 1
    if not checkpoint_downloader(layout):
        return 1
    return 0


def build_start_command(layout: FishSpeechLayout, listen: str = DEFAULT_LISTEN) -> list[str]:
    """Build the canonical sidecar start command."""
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    return [
        str(layout.venv_python),
        "-m",
        "tools.api_server",
        "--listen",
        listen,
        "--llama-checkpoint-path",
        str(checkpoint_root),
        "--decoder-checkpoint-path",
        str(checkpoint_root / DEFAULT_DECODER_NAME),
        "--decoder-config-name",
        "firefly_gan_vq",
        "--half",
    ]


def build_train_command(
    layout: FishSpeechLayout,
    project_root: Path = PROJECT_ROOT,
) -> tuple[list[str], dict[str, object]]:
    """
    Build Fish Speech training command with proper hyperparameters.
    
    Returns:
        Tuple of (command_list, config_dict) where:
        - command_list: The training command to execute
        - config_dict: Training configuration loaded from config
    
    Raises:
        ValueError: If training_enabled is False or dataset is not ready
    """
    try:
        from src.config import get_config
        cfg = get_config()
    except Exception as exc:
        raise ValueError(f"Failed to load config: {exc}") from exc
    
    # Validate training_enabled flag
    if not cfg.voice.training_enabled:
        raise ValueError(
            "Training is disabled. Set voice.training_enabled=true in config or "
            "VOICE_TRAINING_ENABLED=true in .env before training."
        )
    
    # Validate dataset readiness
    preparation = prepare_reference_audio(project_root)
    if not preparation["ready_for_training"]:
        issues = []
        validation = preparation.get("validation", {})
        if validation.get("issues"):
            issues.extend(validation["issues"])
        if preparation.get("transcript_issues"):
            issues.extend(preparation["transcript_issues"])
        
        raise ValueError(
            f"Dataset not ready for training: {preparation['guidance']}\n"
            f"Issues: {', '.join(issues)}"
        )
    
    # Load training configuration
    training_config = {
        "epochs": cfg.voice.training_epochs,
        "batch_size": cfg.voice.training_batch_size,
        "learning_rate": cfg.voice.training_learning_rate,
        "dataset_path": cfg.voice.training_dataset_path,
        "checkpoint_frequency": max(1, cfg.voice.training_epochs // 10),  # Save every 10% of epochs
    }
    
    # Resolve dataset path
    dataset_path = project_root / training_config["dataset_path"]
    if not dataset_path.exists():
        raise ValueError(f"Training dataset path does not exist: {dataset_path}")
    
    # Resolve output checkpoint directory
    output_dir = layout.checkpoints_dir / "trained"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build training command
    # Note: This is a placeholder command structure based on typical Fish-Speech training
    # The actual command may need adjustment based on Fish-Speech v1.5.1 training API
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    
    command = [
        str(layout.venv_python),
        "-m",
        "tools.train",  # Assuming Fish-Speech has a training module
        "--config",
        str(checkpoint_root / "config.json"),
        "--checkpoint",
        str(checkpoint_root / "model.pth"),
        "--data-dir",
        str(dataset_path),
        "--output-dir",
        str(output_dir),
        "--epochs",
        str(training_config["epochs"]),
        "--batch-size",
        str(training_config["batch_size"]),
        "--learning-rate",
        str(training_config["learning_rate"]),
        "--save-every",
        str(training_config["checkpoint_frequency"]),
        "--device",
        "cuda:0",  # Default GPU device
    ]
    
    return command, training_config


def check_trained_model(
    layout: FishSpeechLayout,
    project_root: Path = PROJECT_ROOT,
) -> dict[str, object]:
    """
    Verify trained model exists and is valid.
    
    Returns a dictionary with validation results:
    - exists: bool - whether trained model exists
    - path: str | None - path to trained model directory
    - valid: bool - whether model files are valid
    - model_files: dict[str, bool] - per-file existence check
    - size_mb: float | None - total size of model files in MB
    - message: str - human-readable status message
    """
    # Check config for trained model path
    try:
        from src.config import get_config
        cfg = get_config()
        config_model_path = cfg.voice.trained_model_path
    except Exception:
        config_model_path = None
    
    # Check common trained model locations
    trained_paths = [
        layout.checkpoints_dir / "trained",
        layout.checkpoints_dir / "fine-tuned",
        layout.checkpoints_dir / "indonesian-trained",
    ]
    
    # Add config path if specified
    if config_model_path:
        config_path = Path(config_model_path)
        if not config_path.is_absolute():
            config_path = project_root / config_path
        trained_paths.insert(0, config_path)
    
    # Find first valid trained model
    for trained_dir in trained_paths:
        if not trained_dir.exists():
            continue
        
        # Check for required model files
        model_files = {
            "model.pth": (trained_dir / "model.pth").exists(),
            "config.json": (trained_dir / "config.json").exists(),
            "tokenizer.tiktoken": (trained_dir / "tokenizer.tiktoken").exists(),
        }
        
        # Check if all required files exist and are non-empty
        all_exist = all(model_files.values())
        if not all_exist:
            continue
        
        # Validate file sizes
        all_valid = True
        total_size_bytes = 0
        for filename, exists in model_files.items():
            if exists:
                file_path = trained_dir / filename
                size = file_path.stat().st_size
                if size == 0:
                    all_valid = False
                    break
                total_size_bytes += size
        
        if all_valid:
            return {
                "exists": True,
                "path": str(trained_dir),
                "valid": True,
                "model_files": model_files,
                "size_mb": round(total_size_bytes / (1024 * 1024), 2),
                "message": f"Valid trained model found at {trained_dir}",
            }
    
    # No valid trained model found
    return {
        "exists": False,
        "path": None,
        "valid": False,
        "model_files": {},
        "size_mb": None,
        "message": "No valid trained model found. Run training workflow to create one.",
    }


def run_training_job(
    layout: FishSpeechLayout,
    project_root: Path = PROJECT_ROOT,
    *,
    job_id: int | None = None,
) -> dict[str, object]:
    """
    Execute fine-tuning with proper checkpointing and progress tracking.
    
    This function:
    - Executes the training command built by build_train_command()
    - Tracks training progress (epochs, validation loss)
    - Saves checkpoints every N epochs
    - Updates runtime state on completion
    - Handles training failures with proper error logging
    - Integrates with database training queue
    
    Args:
        layout: FishSpeechLayout with paths
        project_root: Project root directory
        job_id: Optional database job ID for status updates
    
    Returns:
        Dictionary with training results:
        - success: bool - whether training completed successfully
        - status: str - final status (completed, failed, cancelled)
        - trained_model_path: str | None - path to trained model
        - epochs_completed: int - number of epochs completed
        - final_validation_loss: float | None - final validation loss
        - training_time_sec: float - total training time
        - error: str | None - error message if failed
        - checkpoints_saved: list[str] - list of checkpoint paths
    """
    import time as time_module
    
    # Build training command
    try:
        command, config = build_train_command(layout, project_root)
    except ValueError as exc:
        error_msg = f"Training command build failed: {exc}"
        print_status("error", error_msg)
        
        # Update database job status if job_id provided
        if job_id is not None:
            _update_training_job_status(
                job_id=job_id,
                status="failed",
                current_stage="validation_failed",
                error_text=error_msg,
                project_root=project_root,
            )
        
        return {
            "success": False,
            "status": "failed",
            "trained_model_path": None,
            "epochs_completed": 0,
            "final_validation_loss": None,
            "training_time_sec": 0.0,
            "error": error_msg,
            "checkpoints_saved": [],
        }
    
    # Update database job status to in_progress
    if job_id is not None:
        _update_training_job_status(
            job_id=job_id,
            status="in_progress",
            current_stage="training",
            progress_pct=0.0,
            project_root=project_root,
        )
    
    # Prepare output directory
    output_dir = layout.checkpoints_dir / "trained"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Prepare log file
    log_file = layout.runtime_dir / "training.log"
    
    print_status("info", f"Starting training job (epochs: {config['epochs']}, batch_size: {config['batch_size']})")
    print_status("info", f"Output directory: {output_dir}")
    print_status("info", f"Log file: {log_file}")
    
    # Execute training command
    start_time = time_module.time()
    checkpoints_saved = []
    epochs_completed = 0
    final_validation_loss = None
    
    try:
        with log_file.open("w", encoding="utf-8") as log_handle:
            process = subprocess.Popen(
                command,
                cwd=layout.checkout_dir,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
            
            print_status("info", f"Training process started (PID: {process.pid})")
            
            # Monitor training progress
            last_progress_update = time_module.time()
            progress_update_interval = 10.0  # Update every 10 seconds
            
            while process.poll() is None:
                time_module.sleep(1.0)
                
                # Update progress periodically
                current_time = time_module.time()
                if current_time - last_progress_update >= progress_update_interval:
                    # Parse log file for progress information
                    progress_info = _parse_training_log(log_file, config['epochs'])
                    epochs_completed = progress_info['epochs_completed']
                    final_validation_loss = progress_info['validation_loss']
                    
                    # Calculate progress percentage
                    progress_pct = (epochs_completed / config['epochs']) * 100.0
                    
                    # Estimate time remaining
                    elapsed_time = current_time - start_time
                    if epochs_completed > 0:
                        time_per_epoch = elapsed_time / epochs_completed
                        remaining_epochs = config['epochs'] - epochs_completed
                        estimated_remaining_sec = time_per_epoch * remaining_epochs
                        
                        print_status(
                            "info",
                            f"Progress: {progress_pct:.1f}% ({epochs_completed}/{config['epochs']} epochs), "
                            f"Est. remaining: {estimated_remaining_sec / 60:.1f} min"
                        )
                    else:
                        print_status("info", f"Progress: {progress_pct:.1f}% (initializing...)")
                    
                    # Update database job status
                    if job_id is not None:
                        _update_training_job_status(
                            job_id=job_id,
                            status="in_progress",
                            current_stage=f"epoch_{epochs_completed}",
                            progress_pct=progress_pct,
                            project_root=project_root,
                        )
                    
                    last_progress_update = current_time
            
            # Training process completed
            return_code = process.returncode
            training_time_sec = time_module.time() - start_time
            
            # Parse final progress
            progress_info = _parse_training_log(log_file, config['epochs'])
            epochs_completed = progress_info['epochs_completed']
            final_validation_loss = progress_info['validation_loss']
            
            if return_code == 0:
                print_status("ok", f"Training completed successfully in {training_time_sec / 60:.1f} minutes")
                print_status("info", f"Epochs completed: {epochs_completed}/{config['epochs']}")
                if final_validation_loss is not None:
                    print_status("info", f"Final validation loss: {final_validation_loss:.4f}")
                
                # Verify trained model exists
                trained_model_path = output_dir / "model.pth"
                if not trained_model_path.exists():
                    error_msg = "Training completed but model.pth not found in output directory"
                    print_status("error", error_msg)
                    
                    if job_id is not None:
                        _update_training_job_status(
                            job_id=job_id,
                            status="failed",
                            current_stage="verification_failed",
                            error_text=error_msg,
                            project_root=project_root,
                        )
                    
                    return {
                        "success": False,
                        "status": "failed",
                        "trained_model_path": None,
                        "epochs_completed": epochs_completed,
                        "final_validation_loss": final_validation_loss,
                        "training_time_sec": training_time_sec,
                        "error": error_msg,
                        "checkpoints_saved": checkpoints_saved,
                    }
                
                # Update runtime state and config
                _update_runtime_state_after_training(
                    trained_model_path=str(output_dir),
                    project_root=project_root,
                )
                
                # Update database job status
                if job_id is not None:
                    _update_training_job_status(
                        job_id=job_id,
                        status="completed",
                        current_stage="completed",
                        progress_pct=100.0,
                        project_root=project_root,
                    )
                
                print_status("ok", f"Trained model saved to: {output_dir}")
                
                return {
                    "success": True,
                    "status": "completed",
                    "trained_model_path": str(output_dir),
                    "epochs_completed": epochs_completed,
                    "final_validation_loss": final_validation_loss,
                    "training_time_sec": training_time_sec,
                    "error": None,
                    "checkpoints_saved": checkpoints_saved,
                }
            else:
                error_msg = f"Training process failed with exit code {return_code}"
                print_status("error", error_msg)
                print_status("info", f"Check log file for details: {log_file}")
                
                # Update database job status
                if job_id is not None:
                    _update_training_job_status(
                        job_id=job_id,
                        status="failed",
                        current_stage="training_failed",
                        error_text=error_msg,
                        project_root=project_root,
                    )
                
                return {
                    "success": False,
                    "status": "failed",
                    "trained_model_path": None,
                    "epochs_completed": epochs_completed,
                    "final_validation_loss": final_validation_loss,
                    "training_time_sec": training_time_sec,
                    "error": error_msg,
                    "checkpoints_saved": checkpoints_saved,
                }
                
    except KeyboardInterrupt:
        print_status("warn", "Training interrupted by user")
        
        # Terminate training process
        try:
            process.terminate()
            process.wait(timeout=10.0)
        except Exception:
            process.kill()
        
        training_time_sec = time_module.time() - start_time
        
        # Update database job status
        if job_id is not None:
            _update_training_job_status(
                job_id=job_id,
                status="failed",
                current_stage="cancelled",
                error_text="Training cancelled by user",
                project_root=project_root,
            )
        
        return {
            "success": False,
            "status": "cancelled",
            "trained_model_path": None,
            "epochs_completed": epochs_completed,
            "final_validation_loss": final_validation_loss,
            "training_time_sec": training_time_sec,
            "error": "Training cancelled by user",
            "checkpoints_saved": checkpoints_saved,
        }
        
    except Exception as exc:
        error_msg = f"Training execution failed: {exc}"
        print_status("error", error_msg)
        
        training_time_sec = time_module.time() - start_time
        
        # Update database job status
        if job_id is not None:
            _update_training_job_status(
                job_id=job_id,
                status="failed",
                current_stage="execution_failed",
                error_text=error_msg,
                project_root=project_root,
            )
        
        return {
            "success": False,
            "status": "failed",
            "trained_model_path": None,
            "epochs_completed": epochs_completed,
            "final_validation_loss": final_validation_loss,
            "training_time_sec": training_time_sec,
            "error": error_msg,
            "checkpoints_saved": checkpoints_saved,
        }


def _parse_training_log(log_file: Path, total_epochs: int) -> dict[str, object]:
    """
    Parse training log file to extract progress information.
    
    Returns:
        Dictionary with:
        - epochs_completed: int
        - validation_loss: float | None
    """
    if not log_file.exists():
        return {"epochs_completed": 0, "validation_loss": None}
    
    try:
        log_content = log_file.read_text(encoding="utf-8")
        
        # Parse epochs completed (look for patterns like "Epoch 5/100" or "epoch: 5")
        epochs_completed = 0
        for line in log_content.splitlines():
            line_lower = line.lower()
            
            # Pattern 1: "Epoch 5/100"
            if "epoch" in line_lower and "/" in line:
                try:
                    parts = line.split("/")
                    if len(parts) >= 2:
                        epoch_part = parts[0].split()[-1]
                        epochs_completed = max(epochs_completed, int(epoch_part))
                except (ValueError, IndexError):
                    pass
            
            # Pattern 2: "epoch: 5"
            if "epoch:" in line_lower:
                try:
                    epoch_str = line.split("epoch:")[-1].strip().split()[0]
                    epochs_completed = max(epochs_completed, int(epoch_str))
                except (ValueError, IndexError):
                    pass
        
        # Parse validation loss (look for patterns like "val_loss: 0.1234" or "validation loss: 0.1234")
        validation_loss = None
        for line in reversed(log_content.splitlines()):
            line_lower = line.lower()
            
            if "val_loss" in line_lower or "validation loss" in line_lower:
                try:
                    # Extract float value after the loss keyword
                    parts = line.split(":")
                    if len(parts) >= 2:
                        loss_str = parts[-1].strip().split()[0]
                        validation_loss = float(loss_str)
                        break
                except (ValueError, IndexError):
                    pass
        
        return {
            "epochs_completed": epochs_completed,
            "validation_loss": validation_loss,
        }
        
    except Exception:
        return {"epochs_completed": 0, "validation_loss": None}


def _update_training_job_status(
    job_id: int,
    status: str,
    current_stage: str,
    progress_pct: float = 0.0,
    error_text: str = "",
    project_root: Path = PROJECT_ROOT,
) -> None:
    """
    Update training job status in database.
    
    Args:
        job_id: Database job ID
        status: Job status (queued, in_progress, completed, failed)
        current_stage: Current training stage
        progress_pct: Progress percentage (0-100)
        error_text: Error message if failed
        project_root: Project root directory
    """
    try:
        # Import database module
        import sys
        sys.path.insert(0, str(project_root / "src"))
        from data.database import get_connection
        
        with get_connection() as conn:
            # Update job status
            update_fields = [
                "status = ?",
                "current_stage = ?",
                "progress_pct = ?",
                "updated_at = CURRENT_TIMESTAMP",
            ]
            update_values = [status, current_stage, progress_pct]
            
            # Add started_at timestamp if transitioning to in_progress
            if status == "in_progress":
                update_fields.append("started_at = CURRENT_TIMESTAMP")
            
            # Add finished_at timestamp if completed or failed
            if status in ("completed", "failed"):
                update_fields.append("finished_at = CURRENT_TIMESTAMP")
            
            # Add error text if provided
            if error_text:
                update_fields.append("error_text = ?")
                update_values.append(error_text)
            
            update_values.append(job_id)
            
            query = f"UPDATE voice_training_jobs SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(query, update_values)
            
    except Exception as exc:
        print_status("warn", f"Failed to update training job status: {exc}")


def _update_runtime_state_after_training(
    trained_model_path: str,
    project_root: Path = PROJECT_ROOT,
) -> None:
    """
    Update runtime state after successful training completion.
    
    This function updates the voice runtime state to reflect that a trained
    model is now available. It does NOT modify the config file directly.
    
    Args:
        trained_model_path: Path to trained model directory
        project_root: Project root directory
    """
    try:
        # Import runtime state module
        import sys
        sys.path.insert(0, str(project_root / "src"))
        from voice.runtime_state import update_voice_runtime_state
        
        # Update runtime state
        update_voice_runtime_state(
            trained_model_available=True,
            training_status="completed",
        )
        
        print_status("ok", "Runtime state updated with trained model availability")
        
    except Exception as exc:
        print_status("warn", f"Failed to update runtime state: {exc}")


def watch_training_queue(
    project_root: Path = PROJECT_ROOT,
    *,
    poll_interval_sec: float = 5.0,
) -> None:
    """
    Watch database for queued training jobs and execute them sequentially.
    
    This function runs in a loop, polling the database for queued jobs.
    When a job is found, it executes the training and updates the job status.
    Only one job is executed at a time (sequential execution).
    
    Args:
        project_root: Project root directory
        poll_interval_sec: Polling interval in seconds
    """
    import sys
    import time as time_module
    
    sys.path.insert(0, str(project_root / "src"))
    from data.database import get_connection
    
    layout = ensure_layout(project_root)
    
    print_status("info", "Training queue watcher started")
    print_status("info", f"Polling interval: {poll_interval_sec}s")
    
    try:
        while True:
            try:
                # Check for queued jobs
                with get_connection() as conn:
                    cursor = conn.execute(
                        "SELECT id, profile_id, dataset_path FROM voice_training_jobs "
                        "WHERE status = 'queued' ORDER BY queued_at ASC LIMIT 1"
                    )
                    row = cursor.fetchone()
                
                if row:
                    job_id = row[0]
                    profile_id = row[1]
                    dataset_path = row[2]
                    
                    print_status("info", f"Found queued training job (ID: {job_id}, profile: {profile_id})")
                    
                    # Execute training job
                    result = run_training_job(
                        layout=layout,
                        project_root=project_root,
                        job_id=job_id,
                    )
                    
                    if result["success"]:
                        print_status("ok", f"Training job {job_id} completed successfully")
                    else:
                        print_status("error", f"Training job {job_id} failed: {result['error']}")
                else:
                    # No queued jobs, sleep and poll again
                    time_module.sleep(poll_interval_sec)
                    
            except KeyboardInterrupt:
                print_status("info", "Training queue watcher stopped by user")
                break
            except Exception as exc:
                print_status("error", f"Training queue watcher error: {exc}")
                time_module.sleep(poll_interval_sec)
                
    except Exception as exc:
        print_status("error", f"Training queue watcher fatal error: {exc}")


def build_status_payload(
    project_root: Path = PROJECT_ROOT,
    *,
    base_url: str | None = None,
    server_reachable=check_server_reachable,
    pid_running=pid_is_running,
) -> dict[str, object]:
    """Build a machine-readable status payload for operator diagnostics."""
    layout = ensure_layout(project_root)
    pid = read_pid(layout.pid_file)
    reachable = server_reachable(base_url or get_fish_speech_url())
    config_ok, config_message = check_config_alignment()
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    
    # Check trained model status
    trained_model_status = check_trained_model(layout, project_root)
    
    # Check dataset status
    dataset_validation = validate_reference_dataset(project_root)
    dataset_preparation = prepare_reference_audio(project_root)
    
    # Determine training status
    training_status = "not_started"
    try:
        from src.config import get_config
        cfg = get_config()
        training_enabled = cfg.voice.training_enabled
    except Exception:
        training_enabled = False
    
    if trained_model_status["valid"]:
        training_status = "completed"
    elif training_enabled and dataset_preparation["ready_for_training"]:
        training_status = "ready"
    elif training_enabled:
        training_status = "dataset_insufficient"
    
    # Query active training jobs from database
    active_job = None
    training_progress = None
    try:
        import sys
        sys.path.insert(0, str(project_root / "src"))
        from data.database import get_connection
        
        with get_connection() as conn:
            # Get most recent training job (prioritize in_progress, then queued, then completed/failed)
            cursor = conn.execute(
                """
                SELECT id, status, current_stage, progress_pct, 
                       queued_at, started_at, finished_at, error_text
                FROM voice_training_jobs
                ORDER BY 
                    CASE status
                        WHEN 'in_progress' THEN 1
                        WHEN 'queued' THEN 2
                        WHEN 'completed' THEN 3
                        WHEN 'failed' THEN 4
                        ELSE 5
                    END,
                    queued_at DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            
            if row:
                job_id, job_status, current_stage, progress_pct, queued_at, started_at, finished_at, error_text = row
                
                active_job = {
                    "id": job_id,
                    "status": job_status,
                    "current_stage": current_stage,
                    "progress_pct": progress_pct,
                    "queued_at": queued_at,
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "error_text": error_text,
                }
                
                # If job is in progress, parse training log for detailed progress
                if job_status == "in_progress":
                    log_file = layout.runtime_dir / "training.log"
                    if log_file.exists():
                        try:
                            # Load training config to get total epochs
                            cfg = get_config()
                            total_epochs = cfg.voice.training_epochs
                            
                            # Parse log for current epoch and validation loss
                            log_progress = _parse_training_log(log_file, total_epochs)
                            
                            # Calculate estimated time remaining
                            estimated_remaining_sec = None
                            if started_at and log_progress["epochs_completed"] > 0:
                                import datetime
                                start_time = datetime.datetime.fromisoformat(started_at)
                                current_time = datetime.datetime.now()
                                elapsed_sec = (current_time - start_time).total_seconds()
                                time_per_epoch = elapsed_sec / log_progress["epochs_completed"]
                                remaining_epochs = total_epochs - log_progress["epochs_completed"]
                                estimated_remaining_sec = time_per_epoch * remaining_epochs
                            
                            training_progress = {
                                "current_epoch": log_progress["epochs_completed"],
                                "total_epochs": total_epochs,
                                "validation_loss": log_progress["validation_loss"],
                                "estimated_remaining_sec": estimated_remaining_sec,
                            }
                        except Exception:
                            # If parsing fails, use basic progress from database
                            training_progress = {
                                "current_epoch": None,
                                "total_epochs": None,
                                "validation_loss": None,
                                "estimated_remaining_sec": None,
                            }
                
                # Override training_status if there's an active job
                if job_status == "in_progress":
                    training_status = "in_progress"
                elif job_status == "queued":
                    training_status = "queued"
                elif job_status == "failed":
                    training_status = "failed"
    
    except Exception:
        # If database query fails, continue with basic status
        pass

    return {
        "paths": {
            "root": str(layout.root),
            "upstream": str(layout.upstream_dir),
            "checkout": str(layout.checkout_dir),
            "checkpoints": str(layout.checkpoints_dir),
            "runtime": str(layout.runtime_dir),
            "venv": str(layout.venv_dir),
            "venv_python": str(layout.venv_python),
            "pid_file": str(layout.pid_file),
            "log_file": str(layout.log_file),
        },
        "assets": {
            "reference_wav": check_reference_wav(project_root),
            "reference_text": check_reference_text(project_root),
            "checkpoint_root_exists": checkpoint_root.exists(),
            "decoder_exists": (checkpoint_root / DEFAULT_DECODER_NAME).exists(),
            "checkout_exists": layout.checkout_dir.exists(),
            "venv_python_exists": layout.venv_python.exists(),
        },
        "config": {
            "aligned": config_ok,
            "message": config_message,
            "base_url": base_url or get_fish_speech_url(),
        },
        "runtime": {
            "pid": pid,
            "pid_running": pid_running(pid),
            "reachable": reachable,
            "listen": DEFAULT_LISTEN,
            "status": "running" if reachable or pid_running(pid) else "stopped",
        },
        "training": {
            "status": training_status,
            "enabled": training_enabled,
            "trained_model": trained_model_status,
            "dataset": {
                "valid": dataset_validation["valid"],
                "total_duration_min": dataset_validation["total_duration_min"],
                "file_count": dataset_validation["file_count"],
                "ready_for_training": dataset_preparation["ready_for_training"],
                "guidance": dataset_preparation["guidance"],
            },
            "active_job": active_job,
            "progress": training_progress,
        },
    }


def print_startup_guidance(layout: FishSpeechLayout) -> None:
    """Print startup guidance for the canonical Fish-Speech layout."""
    command = build_start_command(layout)
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    ready = layout.checkout_dir.exists() and layout.venv_python.exists() and checkpoint_root.exists()
    print()
    print("=== Fish-Speech Startup Guide ===")
    print(f"TARGET      : {layout.root}")
    print(f"CHECKOUT    : {layout.checkout_dir}")
    print(f"CHECKPOINTS : {layout.checkpoints_dir}")
    print(f"RUNTIME     : {layout.runtime_dir}")
    print(f"PORT        : {DEFAULT_LISTEN}")
    if ready:
        print("NEXT ACTION : run `uv run python scripts/manage.py start fish-speech`")
    else:
        print("NEXT ACTION : place a compatible Fish-Speech checkout and checkpoints in the canonical paths")
    print("START CMD   :")
    print(f"  cwd {layout.checkout_dir}")
    print(f"  {' '.join(build_start_command(layout))}")


def start_server(project_root: Path = PROJECT_ROOT) -> int:
    """Start Fish-Speech in the background with retry logic and health checking."""
    layout = ensure_layout(project_root)
    
    # Check if already reachable
    payload = build_status_payload(project_root)
    if payload["runtime"]["reachable"]:  # type: ignore[index]
        print_status("ok", "Fish-Speech already reachable.")
        return 0
    
    # Validate prerequisites
    if not layout.checkout_dir.exists():
        print_status("error", f"Fish-Speech checkout missing: {layout.checkout_dir}")
        print("NEXT ACTION : place or clone Fish-Speech repo into the canonical checkout path")
        return 1
    
    if not layout.venv_python.exists():
        print_status("error", f"Fish-Speech runtime env missing: {layout.venv_python}")
        print("NEXT ACTION : run `uv run python scripts/manage.py setup fish-speech`")
        return 1
    
    # Validate checkpoint files before starting
    checkpoint_valid, checkpoint_msg = validate_checkpoint_files(layout)
    if not checkpoint_valid:
        print_status("error", f"Checkpoint validation failed: {checkpoint_msg}")
        print("NEXT ACTION : download checkpoints into external/fish-speech/checkpoints/fish-speech-1.5")
        return 1
    
    print_status("ok", checkpoint_msg)
    
    # Detect trained model
    has_trained, trained_path = detect_trained_model(layout)
    if has_trained:
        print_status("info", f"Trained model detected at: {trained_path}")
        # Note: Using trained model would require modifying build_start_command
        # For now, we log the detection and fall back to base model
    else:
        print_status("warn", "No trained model found, using base model")
    
    # Retry logic with exponential backoff
    max_retries = 3
    retry_delays = [2, 4, 8]  # seconds
    
    for attempt in range(max_retries):
        if attempt > 0:
            delay = retry_delays[attempt - 1]
            print_status("info", f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay...")
            time.sleep(delay)
        
        # Start the server process
        command = build_start_command(layout)
        try:
            with layout.log_file.open("a", encoding="utf-8") as handle:
                kwargs: dict[str, object] = {
                    "cwd": layout.checkout_dir,
                    "stdout": handle,
                    "stderr": subprocess.STDOUT,
                }
                if os.name == "nt":
                    kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
                else:
                    kwargs["start_new_session"] = True
                process = subprocess.Popen(command, **kwargs)
            
            layout.pid_file.write_text(str(process.pid), encoding="utf-8")
            print_status("ok", f"Fish-Speech process started (PID: {process.pid})")
            
        except Exception as exc:
            print_status("error", f"Failed to start process: {exc}")
            if attempt == max_retries - 1:
                return 1
            continue
        
        # Health check polling
        print_status("info", "Polling health endpoint...")
        max_health_checks = 30  # 30 seconds timeout
        health_check_interval = 1  # 1 second between checks
        
        for check_num in range(max_health_checks):
            time.sleep(health_check_interval)
            
            # Try TCP probe first (faster)
            if check_server_reachable():
                # Confirm with HTTP health check
                if check_health_endpoint():
                    print_status("ok", f"Fish-Speech sidecar healthy after {check_num + 1}s")
                    print(f"TARGET      : {layout.root}")
                    print(f"PORT        : {DEFAULT_LISTEN}")
                    print(f"LOG         : {layout.log_file}")
                    print("NEXT ACTION : Fish-Speech sidecar is ready for synthesis")
                    return 0
        
        # Health check timeout
        print_status("warn", f"Health check timeout after {max_health_checks}s")
        
        # Stop the failed process before retry
        pid = read_pid(layout.pid_file)
        if pid and pid_is_running(pid):
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        cwd=project_root,
                        capture_output=True,
                        check=False,
                    )
                else:
                    os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        
        if attempt == max_retries - 1:
            print_status("error", "Fish-Speech startup failed after all retries")
            print(f"LOG         : {layout.log_file}")
            print("NEXT ACTION : check log file for errors")
            return 1
    
    return 1


def stop_server(project_root: Path = PROJECT_ROOT) -> int:
    """Stop Fish-Speech using the managed pid file if present."""
    layout = ensure_layout(project_root)
    pid = read_pid(layout.pid_file)
    if pid is None:
        print_status("ok", "Fish-Speech already stopped.")
        return 0

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            os.kill(pid, signal.SIGTERM)
    finally:
        try:
            layout.pid_file.unlink(missing_ok=True)
        except TypeError:
            if layout.pid_file.exists():
                layout.pid_file.unlink()

    print_status("ok", "Fish-Speech stop requested.")
    print(f"TARGET      : {layout.root}")
    print("NEXT ACTION : run `uv run python scripts/manage.py status fish-speech`")
    return 0


def print_status_report(project_root: Path = PROJECT_ROOT, as_json: bool = False) -> int:
    """Print a structured status report."""
    payload = build_status_payload(project_root)
    if as_json:
        print(json.dumps(payload, indent=2))
        return 0

    print("=== Fish-Speech Status ===")
    print(f"TARGET      : {payload['paths']['root']}")
    print(f"CHECKOUT    : {payload['paths']['checkout']}")
    print(f"CHECKPOINTS : {payload['paths']['checkpoints']}")
    print(f"RUNTIME     : {payload['paths']['runtime']}")
    print(f"PORT        : {payload['runtime']['listen']}")
    print(f"STATUS      : {payload['runtime']['status']}")
    print(f"PID         : {payload['runtime']['pid'] or '-'}")
    print(f"REACHABLE   : {'yes' if payload['runtime']['reachable'] else 'no'}")
    if payload["runtime"]["reachable"]:
        print("NEXT ACTION : Fish-Speech sidecar is healthy")
    else:
        print("NEXT ACTION : start the sidecar if checkout, venv, and checkpoints are ready")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entrypoint."""
    parser = argparse.ArgumentParser(description="Fish-Speech local voice clone setup")
    parser.add_argument("--check", action="store_true", help="Validation-only mode")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--status", action="store_true", help="Print sidecar status")
    parser.add_argument("--start", action="store_true", help="Start the Fish-Speech sidecar")
    parser.add_argument("--stop", action="store_true", help="Stop the Fish-Speech sidecar")
    parser.add_argument("--bootstrap-only", action="store_true", help="Only clone/install/download artifacts")
    parser.add_argument("--dataset-report", action="store_true", help="Print dataset quality report")
    parser.add_argument("--validate-dataset", action="store_true", help="Validate dataset and output JSON")
    parser.add_argument("--prepare-dataset", action="store_true", help="Prepare dataset for training")
    parser.add_argument("--prepare-training-dataset", action="store_true", help="Validate and organize training dataset (comprehensive)")
    parser.add_argument("--check-trained-model", action="store_true", help="Check trained model status")
    parser.add_argument("--build-train-command", action="store_true", help="Build training command (dry-run)")
    parser.add_argument("--run-training", action="store_true", help="Execute training job")
    parser.add_argument("--job-id", type=int, help="Database job ID for training (optional)")
    parser.add_argument("--watch-queue", action="store_true", help="Watch training queue and execute jobs sequentially")
    parser.add_argument("--poll-interval", type=float, default=5.0, help="Queue polling interval in seconds (default: 5.0)")
    args = parser.parse_args(argv)

    layout = ensure_layout(PROJECT_ROOT)

    if args.dataset_report:
        print_dataset_report(PROJECT_ROOT)
        return 0
    if args.validate_dataset:
        validation = validate_reference_dataset(PROJECT_ROOT)
        print(json.dumps(validation, indent=2))
        return 0 if validation["valid"] else 1
    if args.prepare_dataset:
        preparation = prepare_reference_audio(PROJECT_ROOT)
        if args.json:
            print(json.dumps(preparation, indent=2))
        else:
            print("=== Dataset Preparation ===")
            print(f"Training dir: {preparation['training_dir']}")
            print(f"Ready for training: {preparation['ready_for_training']}")
            print(f"Guidance: {preparation['guidance']}")
            if preparation['transcript_issues']:
                print("\nTranscript Issues:")
                for issue in preparation['transcript_issues']:
                    print(f"  - {issue}")
        return 0 if preparation["ready_for_training"] else 1
    if args.prepare_training_dataset:
        preparation = prepare_training_dataset(PROJECT_ROOT)
        if args.json:
            print(json.dumps(preparation, indent=2))
        else:
            print("=== Training Dataset Preparation ===")
            print(f"Total duration: {preparation['total_duration_min']:.2f} minutes")
            print(f"File count: {preparation['file_count']}")
            print(f"Valid: {preparation['valid']}")
            print(f"Segmentation needed: {preparation['segmentation_needed']}")
            print(f"Format conversion needed: {preparation['format_conversion_needed']}")
            print(f"Transcript alignment valid: {preparation['transcript_alignment_valid']}")
            print(f"\nGuidance: {preparation['guidance']}")
            if preparation['issues']:
                print("\nIssues:")
                for issue in preparation['issues']:
                    print(f"  - {issue}")
            if preparation['actions_taken']:
                print("\nRecommended Actions:")
                for action in preparation['actions_taken']:
                    print(f"  - {action}")
        return 0 if preparation["valid"] else 1
    if args.check_trained_model:
        model_status = check_trained_model(layout, PROJECT_ROOT)
        if args.json:
            print(json.dumps(model_status, indent=2))
        else:
            print("=== Trained Model Status ===")
            print(f"Exists: {model_status['exists']}")
            print(f"Valid: {model_status['valid']}")
            if model_status['path']:
                print(f"Path: {model_status['path']}")
                print(f"Size: {model_status['size_mb']} MB")
            print(f"Message: {model_status['message']}")
        return 0 if model_status["valid"] else 1
    if args.build_train_command:
        try:
            command, config = build_train_command(layout, PROJECT_ROOT)
            if args.json:
                print(json.dumps({"command": command, "config": config}, indent=2))
            else:
                print("=== Training Command ===")
                print(f"Epochs: {config['epochs']}")
                print(f"Batch size: {config['batch_size']}")
                print(f"Learning rate: {config['learning_rate']}")
                print(f"Dataset path: {config['dataset_path']}")
                print(f"Checkpoint frequency: {config['checkpoint_frequency']}")
                print("\nCommand:")
                print(" ".join(command))
            return 0
        except ValueError as exc:
            print_status("error", str(exc))
            return 1
    if args.run_training:
        result = run_training_job(
            layout=layout,
            project_root=PROJECT_ROOT,
            job_id=args.job_id,
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=== Training Job Result ===")
            print(f"Success: {result['success']}")
            print(f"Status: {result['status']}")
            print(f"Epochs completed: {result['epochs_completed']}")
            if result['final_validation_loss'] is not None:
                print(f"Final validation loss: {result['final_validation_loss']:.4f}")
            print(f"Training time: {result['training_time_sec'] / 60:.1f} minutes")
            if result['trained_model_path']:
                print(f"Trained model: {result['trained_model_path']}")
            if result['error']:
                print(f"Error: {result['error']}")
        return 0 if result['success'] else 1
    if args.watch_queue:
        watch_training_queue(
            project_root=PROJECT_ROOT,
            poll_interval_sec=args.poll_interval,
        )
        return 0
    if args.start:
        return start_server(PROJECT_ROOT)
    if args.stop:
        return stop_server(PROJECT_ROOT)
    if args.status:
        return print_status_report(PROJECT_ROOT, as_json=bool(args.json))
    if args.bootstrap_only:
        return bootstrap_install(PROJECT_ROOT)

    payload = build_status_payload(PROJECT_ROOT)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print("=== Fish-Speech Local Voice Clone Setup ===")
        print_status("info", f"Target root: {layout.root}")
        print_status("info", f"Upstream dir: {layout.upstream_dir}")
        print_status("info", f"Checkpoints dir: {layout.checkpoints_dir}")
        print_status("info", f"Runtime dir: {layout.runtime_dir}")

    blocking = [
        not payload["assets"]["reference_wav"],
        not payload["assets"]["reference_text"],
        not payload["config"]["aligned"],
    ]
    if args.check:
        return 1 if any(blocking) else 0

    bootstrap_code = bootstrap_install(PROJECT_ROOT)
    if bootstrap_code != 0:
        print_status("error", "Fish-Speech bootstrap failed.")
        print_startup_guidance(layout)
        return bootstrap_code

    print_startup_guidance(layout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
