"""Tests for MuseTalk asset normalization helpers."""

from __future__ import annotations

from pathlib import Path


def test_sync_musetalk_assets_copies_legacy_models(tmp_path: Path) -> None:
    """Legacy root models should be copied into canonical vendor path."""
    from src.face.asset_setup import sync_musetalk_assets

    legacy_models = tmp_path / "models" / "musetalk"
    legacy_models.mkdir(parents=True)
    (legacy_models / "weights.pth").write_text("fake")

    report = sync_musetalk_assets(tmp_path)

    assert report.models_ready is True
    assert (tmp_path / "external" / "livetalking" / "models" / "musetalk" / "weights.pth").exists()


def test_sync_musetalk_assets_copies_legacy_avatar(tmp_path: Path) -> None:
    """Legacy root avatar assets should be copied into canonical vendor path."""
    from src.face.asset_setup import sync_musetalk_assets

    legacy_avatar = tmp_path / "data" / "avatars" / "musetalk_avatar1"
    legacy_avatar.mkdir(parents=True)
    (legacy_avatar / "coords.pkl").write_text("fake")

    report = sync_musetalk_assets(tmp_path)

    assert report.avatar_ready is True
    assert (tmp_path / "external" / "livetalking" / "data" / "avatars" / "musetalk_avatar1" / "coords.pkl").exists()


def test_sync_musetalk_assets_reports_missing_reference_media(tmp_path: Path) -> None:
    """Sync report should explain when avatar generation cannot run yet."""
    from src.face.asset_setup import sync_musetalk_assets

    report = sync_musetalk_assets(tmp_path)

    assert report.reference_media_exists is False
    assert report.can_generate_avatar is False
    assert report.reference_media_path == tmp_path / "assets" / "avatar" / "reference.mp4"


def test_sync_musetalk_assets_copies_generated_vendor_avatar(tmp_path: Path) -> None:
    """Vendor MuseTalk generator output should be normalized into runtime avatar path."""
    from src.face.asset_setup import sync_musetalk_assets

    generated_avatar = (
        tmp_path
        / "external"
        / "livetalking"
        / "musetalk"
        / "data"
        / "avatars"
        / "musetalk_avatar1"
    )
    generated_avatar.mkdir(parents=True)
    (generated_avatar / "coords.pkl").write_text("fake")

    report = sync_musetalk_assets(tmp_path)

    assert report.avatar_ready is True
    assert (
        tmp_path / "external" / "livetalking" / "data" / "avatars" / "musetalk_avatar1" / "coords.pkl"
    ).exists()
