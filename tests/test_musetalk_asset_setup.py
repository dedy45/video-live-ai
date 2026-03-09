"""Regression tests for MuseTalk asset normalization."""

from __future__ import annotations

from pathlib import Path

from src.face.asset_setup import sync_musetalk_assets


def _touch(path: Path, content: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_sync_musetalk_assets_requires_complete_runtime_model_contract(tmp_path: Path) -> None:
    """A partially populated model tree must not be reported as generator-ready."""
    _touch(tmp_path / "external" / "livetalking" / "models" / "musetalk" / "README.md")
    _touch(tmp_path / "assets" / "avatar" / "reference.mp4")

    report = sync_musetalk_assets(tmp_path)

    assert report.models_ready is False
    assert report.can_generate_avatar is False


def test_sync_musetalk_assets_flattens_repo_snapshot_into_runtime_paths(tmp_path: Path) -> None:
    """Snapshot downloads should be normalized into the exact paths used by vendor runtime."""
    repo_root = tmp_path / "external" / "livetalking" / "models" / "musetalk"
    _touch(repo_root / "musetalk" / "musetalk.json")
    _touch(repo_root / "musetalk" / "pytorch_model.bin")
    _touch(repo_root / "musetalkV15" / "musetalk.json")
    _touch(repo_root / "musetalkV15" / "unet.pth")
    _touch(tmp_path / "external" / "livetalking" / "models" / "sd-vae" / "config.json")
    _touch(tmp_path / "external" / "livetalking" / "models" / "sd-vae" / "diffusion_pytorch_model.bin")
    _touch(tmp_path / "external" / "livetalking" / "models" / "whisper" / "config.json")
    _touch(tmp_path / "external" / "livetalking" / "models" / "whisper" / "preprocessor_config.json")
    _touch(tmp_path / "external" / "livetalking" / "models" / "whisper" / "pytorch_model.bin")
    _touch(tmp_path / "external" / "livetalking" / "models" / "dwpose" / "dw-ll_ucoco_384.pth")
    _touch(
        tmp_path / "external" / "livetalking" / "models" / "face-parse-bisent" / "79999_iter.pth"
    )
    _touch(
        tmp_path
        / "external"
        / "livetalking"
        / "models"
        / "face-parse-bisent"
        / "resnet18-5c106cde.pth"
    )
    _touch(tmp_path / "assets" / "avatar" / "reference.mp4")

    report = sync_musetalk_assets(tmp_path)

    assert (tmp_path / "external" / "livetalking" / "models" / "musetalk" / "musetalk.json").exists()
    assert (tmp_path / "external" / "livetalking" / "models" / "musetalkV15" / "unet.pth").exists()
    assert report.models_ready is True
    assert report.can_generate_avatar is True


def test_sync_musetalk_assets_requires_whisper_preprocessor_config(tmp_path: Path) -> None:
    """Whisper runtime assets are incomplete without the feature extractor config."""
    repo_root = tmp_path / "external" / "livetalking" / "models" / "musetalk"
    _touch(repo_root / "musetalk" / "musetalk.json")
    _touch(repo_root / "musetalk" / "pytorch_model.bin")
    _touch(repo_root / "musetalkV15" / "musetalk.json")
    _touch(repo_root / "musetalkV15" / "unet.pth")
    _touch(tmp_path / "external" / "livetalking" / "models" / "sd-vae" / "config.json")
    _touch(tmp_path / "external" / "livetalking" / "models" / "sd-vae" / "diffusion_pytorch_model.bin")
    _touch(tmp_path / "external" / "livetalking" / "models" / "whisper" / "config.json")
    _touch(tmp_path / "external" / "livetalking" / "models" / "whisper" / "pytorch_model.bin")
    _touch(tmp_path / "external" / "livetalking" / "models" / "dwpose" / "dw-ll_ucoco_384.pth")
    _touch(
        tmp_path / "external" / "livetalking" / "models" / "face-parse-bisent" / "79999_iter.pth"
    )
    _touch(
        tmp_path
        / "external"
        / "livetalking"
        / "models"
        / "face-parse-bisent"
        / "resnet18-5c106cde.pth"
    )
    _touch(tmp_path / "assets" / "avatar" / "reference.mp4")

    report = sync_musetalk_assets(tmp_path)

    assert report.models_ready is False
    assert report.can_generate_avatar is False
