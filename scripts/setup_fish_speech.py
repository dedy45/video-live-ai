#!/usr/bin/env python3
"""Setup and validation script for Fish-Speech local voice clone integration.

This script checks all prerequisites for running Fish-Speech as a local sidecar:
1. Voice clone reference files (reference.wav, reference.txt)
2. Fish-Speech server reachability
3. Config alignment

Usage:
    uv run python scripts/setup_fish_speech.py           # Full setup check + guidance
    uv run python scripts/setup_fish_speech.py --check    # Validation-only (exit code reflects status)
    uv run python scripts/manage.py setup-fish-speech     # Via operator CLI
    uv run python scripts/manage.py validate fish-speech  # Via operator CLI (--check mode)
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path
from urllib.parse import urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]


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


def check_reference_wav() -> bool:
    """Check that voice clone reference WAV exists."""
    wav_path = PROJECT_ROOT / "assets" / "voice" / "reference.wav"
    if wav_path.exists() and wav_path.stat().st_size > 0:
        print_status("ok", f"Reference WAV found: {wav_path.relative_to(PROJECT_ROOT)}")
        return True
    print_status("error", f"Reference WAV missing: {wav_path.relative_to(PROJECT_ROOT)}")
    print("       Place your Indonesian voice sample at assets/voice/reference.wav")
    return False


def check_reference_text() -> bool:
    """Check that voice clone reference text exists and is non-empty."""
    txt_path = PROJECT_ROOT / "assets" / "voice" / "reference.txt"
    if not txt_path.exists():
        print_status("error", f"Reference text missing: {txt_path.relative_to(PROJECT_ROOT)}")
        print("       Create assets/voice/reference.txt with the transcript of your reference WAV")
        return False
    content = txt_path.read_text(encoding="utf-8").strip()
    if not content:
        print_status("error", "Reference text is empty")
        return False
    print_status("ok", f"Reference text found: {txt_path.relative_to(PROJECT_ROOT)} ({len(content)} chars)")
    return True


def get_fish_speech_url() -> str:
    """Resolve Fish-Speech base URL from config."""
    try:
        from src.config import get_config
        return get_config().voice.fish_speech_base_url
    except Exception:
        return "http://127.0.0.1:8080"


def check_server_reachable(base_url: str | None = None) -> bool:
    """TCP probe to Fish-Speech server."""
    url = base_url or get_fish_speech_url()
    parsed = urlparse(url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8080

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(2.0)
            result = sock.connect_ex((host, port))
            if result == 0:
                print_status("ok", f"Fish-Speech server reachable at {host}:{port}")
                return True
            print_status("warn", f"Fish-Speech server not reachable at {host}:{port}")
            return False
    except Exception as exc:
        print_status("warn", f"Fish-Speech server probe failed: {exc}")
        return False


def check_config_alignment() -> bool:
    """Verify voice config has Fish-Speech fields."""
    try:
        from src.config import get_config
        cfg = get_config()
        assert hasattr(cfg.voice, "fish_speech_base_url")
        assert hasattr(cfg.voice, "fish_speech_timeout_ms")
        assert hasattr(cfg.voice, "clone_reference_wav")
        assert hasattr(cfg.voice, "clone_reference_text")
        print_status("ok", f"Voice config aligned (base_url={cfg.voice.fish_speech_base_url})")
        return True
    except Exception as exc:
        print_status("error", f"Voice config check failed: {exc}")
        return False


def print_startup_guidance() -> None:
    """Print guidance for starting Fish-Speech sidecar."""
    print()
    print("=== Fish-Speech Local Sidecar Startup Guide ===")
    print()
    print("1. Recommended local path on this Windows workstation: use WSL Ubuntu + NVIDIA passthrough.")
    print()
    print("2. Install a Fish-Speech checkout that is compatible with the Fish-Speech 1.5 checkpoint:")
    print("   git clone https://github.com/fishaudio/fish-speech.git")
    print("   cd fish-speech")
    print("   git fetch --depth=200 origin main")
    print("   git worktree add -f ~/fish-speech-v15 40665e1")
    print()
    print("3. Install runtime deps in the sidecar venv:")
    print("   pip install -e '.[cu126]'")
    print("   pip install funasr==1.1.5 vector_quantize_pytorch==1.14.24 torchcodec")
    print()
    print("4. Download model checkpoints:")
    print("   huggingface-cli download fishaudio/fish-speech-1.5 --local-dir checkpoints/fish-speech-1.5")
    print()
    print("5. Start the verified API server path:")
    print("   python -m tools.api_server --listen 127.0.0.1:8080 \\")
    print("       --llama-checkpoint-path ~/fish-speech/checkpoints/fish-speech-1.5 \\")
    print("       --decoder-checkpoint-path ~/fish-speech/checkpoints/fish-speech-1.5/firefly-gan-vq-fsq-8x1024-21hz-generator.pth \\")
    print("       --decoder-config-name firefly_gan_vq --half")
    print()
    print("6. Verify with:")
    print("   uv run python scripts/manage.py validate fish-speech")
    print("   MOCK_MODE=false uv run python -c \"import asyncio, json; from src.dashboard.api import validate_voice_local_clone; print(json.dumps(asyncio.run(validate_voice_local_clone()), indent=2))\"")
    print()
    print("Note: the official OpenAudio S1 mini path remains a target, but local direct-test verification")
    print("on this workstation was captured against Fish-Speech 1.5 with the compatibility checkout above.")
    print()


def run_checks() -> list[dict]:
    """Run all prerequisite checks and return results."""
    checks = []

    wav_ok = check_reference_wav()
    checks.append({"check": "reference_wav", "passed": wav_ok})

    txt_ok = check_reference_text()
    checks.append({"check": "reference_text", "passed": txt_ok})

    config_ok = check_config_alignment()
    checks.append({"check": "config_alignment", "passed": config_ok})

    server_ok = check_server_reachable()
    checks.append({"check": "server_reachable", "passed": server_ok})

    return checks


def main(argv: list[str] | None = None) -> int:
    """Entrypoint."""
    parser = argparse.ArgumentParser(description="Fish-Speech local voice clone setup")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validation-only mode (non-zero exit if prerequisites not met)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )
    args = parser.parse_args(argv)

    print("=== Fish-Speech Local Voice Clone Setup ===")
    print()

    checks = run_checks()

    all_passed = all(c["passed"] for c in checks)
    blocking = [c for c in checks if not c["passed"] and c["check"] != "server_reachable"]

    if args.json:
        print()
        print(json.dumps({"checks": checks, "all_passed": all_passed}, indent=2))

    print()
    if all_passed:
        print_status("ok", "All Fish-Speech prerequisites are met.")
    elif not blocking:
        print_status("warn", "Reference assets ready but Fish-Speech server is not reachable.")
        print("       Start the Fish-Speech sidecar server to proceed.")
    else:
        print_status("error", f"{len(blocking)} blocking prerequisite(s) not met.")

    if not args.check:
        print_startup_guidance()

    # In --check mode, exit non-zero if blocking issues exist
    if args.check and blocking:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
