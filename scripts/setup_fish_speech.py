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
    """Start Fish-Speech in the background when checkout and checkpoints are ready."""
    layout = ensure_layout(project_root)
    payload = build_status_payload(project_root)
    if payload["runtime"]["reachable"]:  # type: ignore[index]
        print_status("ok", "Fish-Speech already reachable.")
        return 0
    if not layout.checkout_dir.exists():
        print_status("error", f"Fish-Speech checkout missing: {layout.checkout_dir}")
        print("NEXT ACTION : place or clone Fish-Speech repo into the canonical checkout path")
        return 1
    if not layout.venv_python.exists():
        print_status("error", f"Fish-Speech runtime env missing: {layout.venv_python}")
        print("NEXT ACTION : run `uv run python scripts/manage.py setup fish-speech`")
        return 1
    checkpoint_root = layout.checkpoints_dir / DEFAULT_CHECKPOINT_NAME
    decoder_path = checkpoint_root / DEFAULT_DECODER_NAME
    if not checkpoint_root.exists() or not decoder_path.exists():
        print_status("error", f"Fish-Speech checkpoints incomplete: {checkpoint_root}")
        print("NEXT ACTION : download checkpoints into external/fish-speech/checkpoints/fish-speech-1.5")
        return 1

    command = build_start_command(layout)
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
    print_status("ok", "Fish-Speech start requested.")
    print(f"TARGET      : {layout.root}")
    print(f"PORT        : {DEFAULT_LISTEN}")
    print(f"LOG         : {layout.log_file}")
    print("NEXT ACTION : run `uv run python scripts/manage.py status fish-speech`")
    return 0


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
    args = parser.parse_args(argv)

    layout = ensure_layout(PROJECT_ROOT)

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
