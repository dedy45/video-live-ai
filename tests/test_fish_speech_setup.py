"""Regression tests for Fish-Speech setup/runtime helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_fish_speech.py"


def load_setup_module():
    """Load scripts/setup_fish_speech.py as a module for focused tests."""
    spec = importlib.util.spec_from_file_location("setup_fish_speech", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_layout_uses_canonical_external_paths(tmp_path: Path) -> None:
    """Fish-Speech layout should resolve inside external/fish-speech only."""
    setup = load_setup_module()

    layout = setup.resolve_layout(tmp_path)

    assert layout.root == tmp_path / "external" / "fish-speech"
    assert layout.upstream_dir == layout.root / "upstream"
    assert layout.checkout_dir == layout.upstream_dir / "fish-speech"
    assert layout.checkpoints_dir == layout.root / "checkpoints"
    assert layout.runtime_dir == layout.root / "runtime"
    assert layout.venv_dir == layout.runtime_dir / ".venv"
    assert layout.venv_python == layout.venv_dir / "Scripts" / "python.exe"
    assert layout.pid_file == layout.runtime_dir / "fish-speech.pid"
    assert layout.log_file == layout.runtime_dir / "fish-speech.log"


def test_ensure_layout_creates_expected_directories(tmp_path: Path) -> None:
    """Bootstrap should create upstream, checkpoints, runtime, and scripts dirs."""
    setup = load_setup_module()

    layout = setup.ensure_layout(tmp_path)

    assert layout.upstream_dir.is_dir()
    assert layout.checkpoints_dir.is_dir()
    assert layout.runtime_dir.is_dir()
    assert layout.scripts_dir.is_dir()


def test_build_status_payload_reports_layout_paths(tmp_path: Path) -> None:
    """Status payload should expose canonical layout paths for operator diagnostics."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    payload = setup.build_status_payload(
        project_root=tmp_path,
        server_reachable=lambda *_args, **_kwargs: False,
        pid_running=lambda *_args, **_kwargs: False,
    )

    assert payload["paths"]["root"] == str(layout.root)
    assert payload["paths"]["upstream"] == str(layout.upstream_dir)
    assert payload["paths"]["checkpoints"] == str(layout.checkpoints_dir)
    assert payload["paths"]["runtime"] == str(layout.runtime_dir)
    assert payload["runtime"]["reachable"] is False
    assert payload["runtime"]["pid"] is None


def test_build_start_command_uses_canonical_checkout_and_checkpoint_paths(tmp_path: Path) -> None:
    """Start command should target the managed checkout and canonical checkpoint locations."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_start_command(layout, listen="127.0.0.1:8080")

    assert command[:3] == [str(layout.venv_python), "-m", "tools.api_server"]
    assert "--listen" in command
    assert "127.0.0.1:8080" in command
    assert str(layout.checkpoints_dir / "fish-speech-1.5") in command
    assert str(
        layout.checkpoints_dir / "fish-speech-1.5" / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    ) in command


def test_build_clone_command_uses_official_repo_and_pinned_tag(tmp_path: Path) -> None:
    """Checkout clone command should target the official repo and the pinned v1.5.1 tag."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_clone_command(layout)

    assert command == [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        "v1.5.1",
        "https://github.com/fishaudio/fish-speech.git",
        str(layout.checkout_dir),
    ]


def test_build_venv_command_targets_runtime_sidecar_env(tmp_path: Path) -> None:
    """Dedicated Fish-Speech env should be created under runtime/.venv."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_venv_command(layout)

    assert command == ["uv", "venv", str(layout.venv_dir), "--allow-existing"]


def test_build_torch_install_command_pins_cuda_runtime(tmp_path: Path) -> None:
    """Torch install should explicitly request the CUDA 12.4 wheels for the sidecar env."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_torch_install_command(layout)

    assert command == [
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


def test_build_install_command_uses_uv_pip_editable_stable_extra(tmp_path: Path) -> None:
    """Dependency install should use uv pip editable install with the stable extra in the sidecar env."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_install_command(layout)

    assert command == [
        "uv",
        "pip",
        "install",
        "--python",
        str(layout.venv_python),
        "-e",
        ".[stable]",
    ]


def test_build_checkpoint_download_specs_use_official_repo_files(tmp_path: Path) -> None:
    """Checkpoint downloader should pull the official v1.5 file set into the canonical checkpoint root."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    specs = setup.build_checkpoint_download_specs(layout)

    assert specs[0]["repo_id"] == "fishaudio/fish-speech-1.5"
    assert specs[0]["local_dir"] == layout.checkpoints_dir / "fish-speech-1.5"
    assert "model.pth" in specs[0]["files"]
    assert "firefly-gan-vq-fsq-8x1024-21hz-generator.pth" in specs[0]["files"]


def test_bootstrap_install_runs_clone_install_and_checkpoint_download(tmp_path: Path) -> None:
    """Bootstrap should clone the pinned checkout, install deps, and hydrate checkpoints when missing."""
    setup = load_setup_module()
    calls: list[tuple[str, object]] = []

    def fake_run(command: list[str], cwd: Path | None = None) -> bool:
        calls.append(("run", (command, cwd)))
        return True

    def fake_download(layout, downloader=None) -> bool:  # type: ignore[no-untyped-def]
        calls.append(("download", layout.checkpoints_dir))
        return True

    exit_code = setup.bootstrap_install(
        project_root=tmp_path,
        runner=fake_run,
        checkpoint_downloader=fake_download,
    )

    layout = setup.resolve_layout(tmp_path)
    assert exit_code == 0
    assert calls[0] == ("run", (setup.build_clone_command(layout), None))
    assert calls[1] == ("run", (setup.build_venv_command(layout), None))
    assert calls[2] == ("run", (setup.build_torch_install_command(layout), layout.checkout_dir))
    assert calls[3] == ("run", (setup.build_install_command(layout), layout.checkout_dir))
    assert calls[4] == ("download", layout.checkpoints_dir)
