"""Regression tests for MuseTalk asset setup script."""

from __future__ import annotations

import importlib.util
import sys
import tomllib
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_musetalk_assets.py"
PYPROJECT_PATH = PROJECT_ROOT / "pyproject.toml"


def load_setup_module():
    """Load scripts/setup_musetalk_assets.py as a module for focused tests."""
    spec = importlib.util.spec_from_file_location("setup_musetalk_assets", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_generate_avatar_uses_vendor_module_entrypoint() -> None:
    """Generator must run from the vendor root so musetalk imports resolve."""
    setup = load_setup_module()
    captured: dict[str, object] = {}

    def fake_run(command, cwd=None, check=None):  # type: ignore[no-untyped-def]
        captured["command"] = command
        captured["cwd"] = cwd
        captured["check"] = check

    setup.subprocess.run = fake_run

    reference = PROJECT_ROOT / "assets" / "avatar" / "reference.mp4"
    setup.generate_avatar(reference, "musetalk_avatar1")

    vendor_root = PROJECT_ROOT / "external" / "livetalking"
    assert captured["command"] == [
        sys.executable,
        "-m",
        "musetalk.genavatar",
        "--file",
        str(reference),
        "--avatar_id",
        "musetalk_avatar1",
        "--version",
        "v15",
    ]
    assert captured["cwd"] == vendor_root
    assert captured["check"] is True


def test_livetalking_extra_declares_openmmlab_generation_dependencies() -> None:
    """MuseTalk generation deps must be part of the UV-managed livetalking extra."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    livetalking = pyproject["project"]["optional-dependencies"]["livetalking"]
    normalized = " ".join(livetalking).lower()

    for package_name in ("mmpose", "mmengine", "mmdet", "mmcv-lite"):
        assert package_name in normalized


def test_livetalking_extra_pins_vendor_compatible_diffusers() -> None:
    """Vendor MuseTalk generation is not compatible with the newest diffusers releases."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    livetalking = pyproject["project"]["optional-dependencies"]["livetalking"]
    diffusers_entries = [entry for entry in livetalking if entry.startswith("diffusers")]

    assert diffusers_entries == ["diffusers==0.27.2"]


def test_uv_declares_extra_build_overrides_for_openmmlab_sdists() -> None:
    """Known broken sdists must have UV build overrides for reproducible sync."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    overrides = pyproject["tool"]["uv"]["extra-build-dependencies"]

    assert overrides["chumpy"] == ["pip"]
    assert overrides["xtcocotools"] == ["numpy"]


def test_uv_pins_pytorch_packages_to_cuda_index_on_windows_and_linux() -> None:
    """uv run/sync must not silently fall back to CPU-only PyTorch wheels on Windows/Linux."""
    pyproject = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    sources = pyproject["tool"]["uv"]["sources"]
    indexes = {entry["name"]: entry for entry in pyproject["tool"]["uv"]["index"]}

    expected = {"index": "pytorch-cu126", "marker": "sys_platform == 'linux' or sys_platform == 'win32'"}
    assert sources["torch"] == [expected]
    assert sources["torchvision"] == [expected]
    assert sources["torchaudio"] == [expected]
    assert indexes["pytorch-cu126"]["url"] == "https://download.pytorch.org/whl/cu126"
    assert indexes["pytorch-cu126"]["explicit"] is True


def test_main_refuses_avatar_generation_until_model_contract_is_ready() -> None:
    """Generator should stop on the strict models_ready contract, not on a non-empty folder."""
    setup = load_setup_module()
    reference = PROJECT_ROOT / "assets" / "avatar" / "reference.mp4"

    class FakeReport:
        models_ready = False
        avatar_ready = False
        reference_media_exists = True
        can_generate_avatar = False
        model_dir = PROJECT_ROOT
        avatar_dir = PROJECT_ROOT / "external" / "livetalking" / "data" / "avatars" / "musetalk_avatar1"
        reference_media_path = reference

    called = {"generate": False}

    def fake_generate_avatar(reference_file: Path, avatar_id: str) -> None:
        called["generate"] = True

    setup.sync_musetalk_assets = lambda *_args, **_kwargs: FakeReport()
    setup.generate_avatar = fake_generate_avatar

    original_argv = sys.argv[:]
    sys.argv = ["setup_musetalk_assets.py", "--generate-avatar"]
    try:
        with pytest.raises(RuntimeError, match="MuseTalk models not ready"):
            setup.main()
    finally:
        sys.argv = original_argv

    assert called["generate"] is False
