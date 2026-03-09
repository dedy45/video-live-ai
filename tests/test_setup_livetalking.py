"""Regression tests for the LiveTalking setup script."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tomllib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SETUP_PATH = PROJECT_ROOT / "scripts" / "setup_livetalking.py"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def load_setup_module():
    """Load scripts/setup_livetalking.py as a module for focused tests."""
    spec = importlib.util.spec_from_file_location("setup_livetalking", SETUP_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_install_dependencies_syncs_managed_livetalking_extra_first() -> None:
    """Setup should hydrate the managed UV env before applying vendor overlays."""
    setup = load_setup_module()
    commands: list[tuple[list[str], Path | None]] = []

    def fake_run_command(cmd: list[str], cwd: Path | None = None) -> bool:
        commands.append((cmd, cwd))
        return True

    setup.run_command = fake_run_command

    assert setup.install_dependencies(PROJECT_ROOT) is True

    requirements_file = PROJECT_ROOT / "external" / "livetalking" / "requirements.txt"
    assert commands == [
        (["uv", "sync", "--extra", "dev", "--extra", "livetalking"], PROJECT_ROOT),
        (["uv", "pip", "install", "-r", str(requirements_file)], PROJECT_ROOT),
    ]


def test_livetalking_extra_declares_vendor_web_runtime_dependencies() -> None:
    """Critical vendor runtime deps should live in pyproject's UV-managed extra."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    livetalking = pyproject["project"]["optional-dependencies"]["livetalking"]
    normalized = " ".join(livetalking).lower()

    for package_name in (
        "flask",
        "flask-sockets",
        "aiohttp-cors",
        "transformers",
        "diffusers",
        "accelerate",
        "omegaconf",
    ):
        assert package_name in normalized


def test_setup_status_output_handles_cp1252_stdout() -> None:
    """Setup status printing should not crash on default Windows cp1252 consoles."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from scripts.setup_livetalking import print_status; "
                "print_status('ok', 'Dependencies installed')"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "[OK] Dependencies installed" in result.stdout


def test_run_setup_steps_treats_gpu_check_as_warning() -> None:
    """GPU absence should not hard-fail local setup after dependency hydration."""
    setup = load_setup_module()
    steps = [
        ("Install dependencies", lambda: True),
        ("Check GPU", lambda: False),
    ]

    assert setup.run_setup_steps(steps, non_blocking_steps={"Check GPU"}) == 0
