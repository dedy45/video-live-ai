#!/usr/bin/env python3
"""Normalize MuseTalk assets into canonical LiveTalking vendor paths."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_AVATAR_ID = "musetalk_avatar1"

sys.path.insert(0, str(PROJECT_ROOT))

from src.face.asset_setup import sync_musetalk_assets  # noqa: E402


def download_musetalk_models(model_dir: Path) -> None:
    """Download MuseTalk weights into canonical vendor path."""
    from huggingface_hub import snapshot_download

    model_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id="TMElyralab/MuseTalk",
        local_dir=str(model_dir),
    )


def generate_avatar(reference_file: Path, avatar_id: str) -> None:
    """Generate a MuseTalk avatar using vendor generator."""
    gen_script = PROJECT_ROOT / "external" / "livetalking" / "musetalk" / "genavatar.py"
    if not gen_script.exists():
        raise FileNotFoundError(f"genavatar.py not found: {gen_script}")

    subprocess.run(
        [
            sys.executable,
            str(gen_script),
            "--file",
            str(reference_file),
            "--avatar_id",
            avatar_id,
            "--version",
            "v15",
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup MuseTalk runtime assets")
    parser.add_argument("--sync-only", action="store_true", help="Only normalize existing local assets")
    parser.add_argument("--download-models", action="store_true", help="Download MuseTalk models into vendor path")
    parser.add_argument("--generate-avatar", action="store_true", help="Generate avatar from reference media")
    parser.add_argument("--reference-file", type=str, default="assets/avatar/reference.mp4")
    parser.add_argument("--avatar-id", type=str, default=DEFAULT_AVATAR_ID)
    args = parser.parse_args()

    report = sync_musetalk_assets(PROJECT_ROOT, avatar_id=args.avatar_id)

    if args.download_models:
        print(f"Downloading MuseTalk models to {report.model_dir}")
        download_musetalk_models(report.model_dir)
        report = sync_musetalk_assets(PROJECT_ROOT, avatar_id=args.avatar_id)

    if args.generate_avatar:
        reference_file = (PROJECT_ROOT / args.reference_file).resolve()
        if not reference_file.exists():
            raise FileNotFoundError(f"Reference file not found: {reference_file}")
        if not report.model_dir.exists() or not any(report.model_dir.iterdir()):
            raise RuntimeError(f"MuseTalk models not ready: {report.model_dir}")
        print(f"Generating avatar {args.avatar_id} from {reference_file}")
        generate_avatar(reference_file, args.avatar_id)
        report = sync_musetalk_assets(PROJECT_ROOT, avatar_id=args.avatar_id)

    print("=" * 60)
    print("  MuseTalk Asset Status")
    print("=" * 60)
    print(f"Model dir:        {report.model_dir}")
    print(f"Models ready:     {report.models_ready}")
    print(f"Avatar dir:       {report.avatar_dir}")
    print(f"Avatar ready:     {report.avatar_ready}")
    print(f"Reference media:  {report.reference_media_path}")
    print(f"Reference exists: {report.reference_media_exists}")
    print(f"Can generate:     {report.can_generate_avatar}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
