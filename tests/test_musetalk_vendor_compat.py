"""Regression tests for vendor MuseTalk import compatibility."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENDOR_ROOT = PROJECT_ROOT / "external" / "livetalking"


def _load_module(name: str, path: Path):
    sys.path.insert(0, str(VENDOR_ROOT))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        if sys.path and sys.path[0] == str(VENDOR_ROOT):
            sys.path.pop(0)


def test_vendor_musetalk_vae_module_imports() -> None:
    """Vendor VAE helper should import cleanly in the managed UV env."""
    pytest.importorskip("diffusers", reason="requires uv extra 'livetalking'", exc_type=ImportError)
    module = _load_module(
        "vendor_musetalk_vae",
        PROJECT_ROOT / "external" / "livetalking" / "musetalk" / "models" / "vae.py",
    )

    assert hasattr(module, "VAE")


def test_vendor_musetalk_unet_module_imports() -> None:
    """Vendor UNet helper should import cleanly in the managed UV env."""
    pytest.importorskip("torch", reason="requires uv extra 'livetalking'", exc_type=ImportError)
    module = _load_module(
        "vendor_musetalk_unet",
        PROJECT_ROOT / "external" / "livetalking" / "musetalk" / "models" / "unet.py",
    )

    assert hasattr(module, "UNet")


def test_vendor_face_parsing_loaders_opt_out_of_pytorch_weights_only_default() -> None:
    """Legacy checkpoint loaders must set weights_only=False under modern PyTorch."""
    paths = [
        PROJECT_ROOT
        / "external"
        / "livetalking"
        / "musetalk"
        / "utils"
        / "face_parsing"
        / "__init__.py",
        PROJECT_ROOT
        / "external"
        / "livetalking"
        / "musetalk"
        / "utils"
        / "face_parsing"
        / "resnet.py",
    ]

    for path in paths:
        assert "weights_only=False" in path.read_text(encoding="utf-8")


def test_vendor_preprocessing_uses_ascii_only_console_messages() -> None:
    """Windows cp1252 consoles should not crash on vendor preprocessing status prints."""
    source = (
        PROJECT_ROOT
        / "external"
        / "livetalking"
        / "musetalk"
        / "utils"
        / "preprocessing.py"
    ).read_text(encoding="utf-8")

    assert "「" not in source
    assert "」" not in source
