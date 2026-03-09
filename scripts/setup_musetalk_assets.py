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
    import urllib.request

    from huggingface_hub import hf_hub_download, snapshot_download

    model_dir.mkdir(parents=True, exist_ok=True)
    models_root = model_dir.parent

    snapshot_download(
        repo_id="TMElyralab/MuseTalk",
        local_dir=str(model_dir),
    )
    snapshot_download(
        repo_id="stabilityai/sd-vae-ft-mse",
        local_dir=str(models_root / "sd-vae"),
        allow_patterns=["config.json", "diffusion_pytorch_model.bin", "diffusion_pytorch_model.safetensors"],
    )
    snapshot_download(
        repo_id="openai/whisper-tiny",
        local_dir=str(models_root / "whisper"),
        allow_patterns=["config.json", "preprocessor_config.json", "pytorch_model.bin"],
    )
    hf_hub_download(
        repo_id="yzd-v/DWPose",
        filename="dw-ll_ucoco_384.pth",
        local_dir=str(models_root / "dwpose"),
    )
    hf_hub_download(
        repo_id="AI2lab/face-parsing.PyTorch",
        filename="79999_iter.pth",
        local_dir=str(models_root / "face-parse-bisent"),
    )
    resnet_path = models_root / "face-parse-bisent" / "resnet18-5c106cde.pth"
    if not resnet_path.exists():
        resnet_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(
            "https://download.pytorch.org/models/resnet18-5c106cde.pth",
            str(resnet_path),
        )


def generate_avatar(reference_file: Path, avatar_id: str) -> None:
    """Generate a MuseTalk avatar using vendor generator."""
    vendor_root = PROJECT_ROOT / "external" / "livetalking"
    gen_script = vendor_root / "musetalk" / "genavatar.py"
    if not gen_script.exists():
        raise FileNotFoundError(f"genavatar.py not found: {gen_script}")

    subprocess.run(
        [
            sys.executable,
            "-m",
            "musetalk.genavatar",
            "--file",
            str(reference_file),
            "--avatar_id",
            avatar_id,
            "--version",
            "v15",
        ],
        cwd=vendor_root,
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
        if not report.models_ready:
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
