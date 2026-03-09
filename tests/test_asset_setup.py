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


# === Stricter contract tests for LOCAL_VERTICAL_SLICE_REAL_MUSETALK ===


def test_asset_report_not_ready_when_model_dir_empty(tmp_path: Path) -> None:
    """Models dir exists but is empty -> models_ready must be False."""
    from src.face.asset_setup import sync_musetalk_assets

    vendor_models = tmp_path / "external" / "livetalking" / "models" / "musetalk"
    vendor_models.mkdir(parents=True)

    report = sync_musetalk_assets(tmp_path)

    assert report.models_ready is False, "Empty model dir should not count as ready"


def test_asset_report_not_ready_when_avatar_dir_empty(tmp_path: Path) -> None:
    """Avatar dir exists but is empty -> avatar_ready must be False."""
    from src.face.asset_setup import sync_musetalk_assets

    vendor_avatar = tmp_path / "external" / "livetalking" / "data" / "avatars" / "musetalk_avatar1"
    vendor_avatar.mkdir(parents=True)

    report = sync_musetalk_assets(tmp_path)

    assert report.avatar_ready is False, "Empty avatar dir should not count as ready"


def test_asset_report_can_generate_requires_both_reference_and_models(tmp_path: Path) -> None:
    """can_generate_avatar requires both reference media AND model weights."""
    from src.face.asset_setup import sync_musetalk_assets

    # Only reference, no models
    ref = tmp_path / "assets" / "avatar" / "reference.mp4"
    ref.parent.mkdir(parents=True)
    ref.write_text("fake")

    report = sync_musetalk_assets(tmp_path)

    assert report.reference_media_exists is True
    assert report.can_generate_avatar is False, "Can't generate without models"


def test_asset_report_identifies_all_missing_fields(tmp_path: Path) -> None:
    """On a fresh empty project, all asset fields should report not ready."""
    from src.face.asset_setup import sync_musetalk_assets

    report = sync_musetalk_assets(tmp_path)

    assert report.models_ready is False
    assert report.avatar_ready is False
    assert report.reference_media_exists is False
    assert report.can_generate_avatar is False
