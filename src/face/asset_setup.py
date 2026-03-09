"""Helpers for normalizing MuseTalk runtime assets."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AVATAR_ID = "musetalk_avatar1"
_REQUIRED_MODEL_FILES = {
    "musetalk": ("musetalk.json", "pytorch_model.bin"),
    "musetalkV15": ("musetalk.json", "unet.pth"),
    "sd-vae": ("config.json",),
    "whisper": ("config.json", "preprocessor_config.json", "pytorch_model.bin"),
    "dwpose": ("dw-ll_ucoco_384.pth",),
    "face-parse-bisent": ("79999_iter.pth", "resnet18-5c106cde.pth"),
}
_REQUIRED_MODEL_ALTERNATIVES = {
    ("sd-vae",): (("diffusion_pytorch_model.bin",), ("diffusion_pytorch_model.safetensors",)),
}


@dataclass
class MuseTalkAssetReport:
    models_ready: bool
    avatar_ready: bool
    reference_media_exists: bool
    can_generate_avatar: bool
    model_dir: Path
    avatar_dir: Path
    reference_media_path: Path


def _copy_tree_if_present(source: Path, destination: Path) -> bool:
    if not source.exists():
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)
    return True


def _copy_contents_if_present(source: Path, destination: Path) -> bool:
    if not source.exists() or not source.is_dir():
        return False

    destination.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        target = destination / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
    return True


def _normalize_repo_snapshot(model_root: Path) -> None:
    repo_root = model_root / "musetalk"
    _copy_contents_if_present(repo_root / "musetalk", model_root / "musetalk")
    _copy_contents_if_present(repo_root / "musetalkV15", model_root / "musetalkV15")


def _has_required_model_contract(model_root: Path) -> bool:
    for directory_name, required_files in _REQUIRED_MODEL_FILES.items():
        directory = model_root / directory_name
        if not directory.exists():
            return False
        for filename in required_files:
            if not (directory / filename).exists():
                return False

    for directory_parts, alternatives in _REQUIRED_MODEL_ALTERNATIVES.items():
        directory = model_root.joinpath(*directory_parts)
        if not any(all((directory / filename).exists() for filename in option) for option in alternatives):
            return False

    return True


def sync_musetalk_assets(project_root: Path, avatar_id: str = DEFAULT_AVATAR_ID) -> MuseTalkAssetReport:
    """Sync legacy MuseTalk assets into the canonical vendor path."""
    vendor_models_root = project_root / "external" / "livetalking" / "models"
    vendor_model_dir = project_root / "external" / "livetalking" / "models" / "musetalk"
    vendor_avatar_dir = project_root / "external" / "livetalking" / "data" / "avatars" / avatar_id

    legacy_model_dir = project_root / "models" / "musetalk"
    legacy_avatar_dir = project_root / "data" / "avatars" / avatar_id
    generated_vendor_avatar_dir = (
        project_root / "external" / "livetalking" / "musetalk" / "data" / "avatars" / avatar_id
    )

    _copy_tree_if_present(legacy_model_dir, vendor_model_dir)
    _copy_tree_if_present(legacy_avatar_dir, vendor_avatar_dir)
    _copy_tree_if_present(generated_vendor_avatar_dir, vendor_avatar_dir)
    _normalize_repo_snapshot(vendor_models_root)

    reference_media_path = project_root / "assets" / "avatar" / "reference.mp4"
    models_ready = _has_required_model_contract(vendor_models_root)

    return MuseTalkAssetReport(
        models_ready=models_ready,
        avatar_ready=vendor_avatar_dir.exists() and any(vendor_avatar_dir.iterdir()),
        reference_media_exists=reference_media_path.exists(),
        can_generate_avatar=reference_media_path.exists() and models_ready,
        model_dir=vendor_model_dir,
        avatar_dir=vendor_avatar_dir,
        reference_media_path=reference_media_path,
    )
