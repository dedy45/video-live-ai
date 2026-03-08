"""Helpers for normalizing MuseTalk runtime assets."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AVATAR_ID = "musetalk_avatar1"


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


def sync_musetalk_assets(project_root: Path, avatar_id: str = DEFAULT_AVATAR_ID) -> MuseTalkAssetReport:
    """Sync legacy MuseTalk assets into the canonical vendor path."""
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

    reference_media_path = project_root / "assets" / "avatar" / "reference.mp4"

    return MuseTalkAssetReport(
        models_ready=vendor_model_dir.exists() and any(vendor_model_dir.iterdir()),
        avatar_ready=vendor_avatar_dir.exists() and any(vendor_avatar_dir.iterdir()),
        reference_media_exists=reference_media_path.exists(),
        can_generate_avatar=reference_media_path.exists() and vendor_model_dir.exists(),
        model_dir=vendor_model_dir,
        avatar_dir=vendor_avatar_dir,
        reference_media_path=reference_media_path,
    )
