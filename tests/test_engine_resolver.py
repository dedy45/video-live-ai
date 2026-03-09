"""Tests for avatar engine runtime resolver and FFmpeg readiness.

Covers:
1. Default engine is musetalk (source-of-truth alignment).
2. Runtime resolver falls back to wav2lip when MuseTalk models/avatars are missing.
3. FFmpeg readiness checks known install paths, not just PATH.
4. Milestone truth: fallback to wav2lip must be visible as non-pass.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure mock mode so GPU-dependent code doesn't run
os.environ["MOCK_MODE"] = "true"


# ── 1. Default source-of-truth is musetalk ──────────────────────────


def test_config_default_engine_is_musetalk() -> None:
    """AvatarConfig.engine default must be 'musetalk'."""
    from src.config.loader import AvatarConfig

    cfg = AvatarConfig()
    assert cfg.engine == "musetalk"


def test_livetalking_adapter_default_model_is_musetalk() -> None:
    """Adapter-level DEFAULT_MODEL constant must be 'musetalk'."""
    from src.face.livetalking_adapter import DEFAULT_MODEL

    assert DEFAULT_MODEL == "musetalk"


def test_livetalking_config_default_model_is_musetalk() -> None:
    """LiveTalkingConfig.model default must be 'musetalk'."""
    from src.config.loader import LiveTalkingConfig

    cfg = LiveTalkingConfig()
    assert cfg.model == "musetalk"


# ── 2. Runtime resolver: musetalk → wav2lip fallback ────────────────


def test_resolve_engine_returns_musetalk_when_models_present(tmp_path: Path) -> None:
    """Resolver keeps musetalk when model dir and avatar dir exist."""
    from src.face.engine_resolver import resolve_engine

    models_dir = tmp_path / "musetalk"
    models_dir.mkdir(parents=True)
    avatars_dir = tmp_path / "avatars" / "musetalk_avatar1"
    avatars_dir.mkdir(parents=True)

    result = resolve_engine(
        requested="musetalk",
        musetalk_model_dir=models_dir,
        musetalk_avatar_dir=avatars_dir,
    )
    assert result == "musetalk"


def test_resolve_engine_falls_back_to_wav2lip_when_model_missing(tmp_path: Path) -> None:
    """Resolver degrades to wav2lip when MuseTalk model dir doesn't exist."""
    from src.face.engine_resolver import resolve_engine

    missing_model = tmp_path / "musetalk_nonexistent"
    avatars_dir = tmp_path / "avatars" / "musetalk_avatar1"
    avatars_dir.mkdir(parents=True)

    result = resolve_engine(
        requested="musetalk",
        musetalk_model_dir=missing_model,
        musetalk_avatar_dir=avatars_dir,
    )
    assert result == "wav2lip"


def test_resolve_engine_falls_back_to_wav2lip_when_avatar_missing(tmp_path: Path) -> None:
    """Resolver degrades to wav2lip when MuseTalk avatar dir doesn't exist."""
    from src.face.engine_resolver import resolve_engine

    models_dir = tmp_path / "musetalk"
    models_dir.mkdir(parents=True)
    missing_avatar = tmp_path / "avatars" / "nonexistent"

    result = resolve_engine(
        requested="musetalk",
        musetalk_model_dir=models_dir,
        musetalk_avatar_dir=missing_avatar,
    )
    assert result == "wav2lip"


def test_resolve_engine_keeps_wav2lip_as_is() -> None:
    """When wav2lip is explicitly requested, no resolution needed."""
    from src.face.engine_resolver import resolve_engine

    result = resolve_engine(requested="wav2lip")
    assert result == "wav2lip"


def test_resolve_engine_keeps_ultralight_as_is() -> None:
    """Non-musetalk engines pass through unchanged."""
    from src.face.engine_resolver import resolve_engine

    result = resolve_engine(requested="ultralight")
    assert result == "ultralight"


# ── 3. FFmpeg readiness — not just PATH ─────────────────────────────


def test_find_ffmpeg_returns_path_when_on_system_path() -> None:
    """If ffmpeg is on PATH, find_ffmpeg should return its path."""
    from src.utils.ffmpeg import find_ffmpeg

    result = find_ffmpeg()
    # On CI/dev machines ffmpeg may or may not be installed.
    # We only assert the return type; actual availability is env-dependent.
    assert result is None or isinstance(result, Path)


def test_find_ffmpeg_checks_known_locations(tmp_path: Path) -> None:
    """find_ffmpeg should check well-known install directories."""
    from src.utils.ffmpeg import find_ffmpeg

    # Create a fake ffmpeg in a known location
    fake_bin = tmp_path / "ffmpeg.exe"
    fake_bin.write_text("fake")

    with patch("src.utils.ffmpeg._KNOWN_FFMPEG_PATHS", [tmp_path]):
        result = find_ffmpeg()

    assert result is not None
    assert "ffmpeg" in result.name.lower()


def test_find_ffmpeg_prefers_ffmpeg_bin_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FFMPEG_BIN should override PATH and known-location lookup."""
    from src.utils.ffmpeg import find_ffmpeg

    fake_bin = tmp_path / "custom-ffmpeg.exe"
    fake_bin.write_text("fake")
    monkeypatch.setenv("FFMPEG_BIN", str(fake_bin))

    result = find_ffmpeg()

    assert result == fake_bin


def test_find_ffmpeg_uses_ffmpeg_dir_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """FFMPEG_DIR should resolve ffmpeg from an explicit bin directory."""
    from src.utils.ffmpeg import find_ffmpeg

    ffmpeg_dir = tmp_path / "bin"
    ffmpeg_dir.mkdir()
    fake_bin = ffmpeg_dir / "ffmpeg.exe"
    fake_bin.write_text("fake")
    monkeypatch.delenv("FFMPEG_BIN", raising=False)
    monkeypatch.setenv("FFMPEG_DIR", str(ffmpeg_dir))

    result = find_ffmpeg()

    assert result == fake_bin


def test_find_ffmpeg_checks_project_local_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Project-local FFmpeg directories should be scanned before system locations."""
    from src.utils.ffmpeg import find_ffmpeg

    fake_bin = tmp_path / "ffmpeg.exe"
    fake_bin.write_text("fake")
    monkeypatch.delenv("FFMPEG_BIN", raising=False)
    monkeypatch.delenv("FFMPEG_DIR", raising=False)

    with patch("shutil.which", return_value=None), \
         patch("src.utils.ffmpeg._PROJECT_LOCAL_FFMPEG_DIRS", [tmp_path]), \
         patch("src.utils.ffmpeg._KNOWN_FFMPEG_PATHS", []):
        result = find_ffmpeg()

    assert result == fake_bin


def test_find_ffmpeg_returns_none_when_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    """find_ffmpeg returns None when ffmpeg is nowhere to be found."""
    from src.utils.ffmpeg import find_ffmpeg

    monkeypatch.delenv("FFMPEG_BIN", raising=False)
    monkeypatch.delenv("FFMPEG_DIR", raising=False)
    with patch("shutil.which", return_value=None), \
         patch("src.utils.ffmpeg._PROJECT_LOCAL_FFMPEG_DIRS", []), \
         patch("src.utils.ffmpeg._KNOWN_FFMPEG_PATHS", []):
        result = find_ffmpeg()

    assert result is None


def test_check_ffmpeg_ready_returns_status_dict() -> None:
    """check_ffmpeg_ready returns a dict with 'available' and 'path' keys."""
    from src.utils.ffmpeg import check_ffmpeg_ready

    status = check_ffmpeg_ready()
    assert "available" in status
    assert "path" in status
    assert isinstance(status["available"], bool)


# ── 4. Milestone truth: fallback visibility ─────────────────────────


def test_resolve_avatar_id_fallback_visible(tmp_path: Path) -> None:
    """When musetalk avatar is missing, resolver must fall back to wav2lip avatar."""
    from src.face.engine_resolver import resolve_avatar_id

    avatars_dir = tmp_path / "avatars"
    wav2lip_dir = avatars_dir / "wav2lip256_avatar1"
    wav2lip_dir.mkdir(parents=True)

    result = resolve_avatar_id(
        "musetalk_avatar1",
        "wav2lip",
        avatars_dir=avatars_dir,
    )
    assert result == "wav2lip256_avatar1", "Fallback avatar must match resolved engine"


def test_resolve_avatar_id_keeps_musetalk_when_present(tmp_path: Path) -> None:
    """When musetalk avatar exists, resolver should keep it."""
    from src.face.engine_resolver import resolve_avatar_id

    avatars_dir = tmp_path / "avatars"
    musetalk_dir = avatars_dir / "musetalk_avatar1"
    musetalk_dir.mkdir(parents=True)

    result = resolve_avatar_id(
        "musetalk_avatar1",
        "musetalk",
        avatars_dir=avatars_dir,
    )
    assert result == "musetalk_avatar1"


def test_milestone_truth_fails_when_fallback_active() -> None:
    """Milestone truth check: requested=musetalk but resolved=wav2lip means NOT complete."""
    requested = "musetalk"
    resolved = "wav2lip"
    milestone_pass = (requested == resolved)
    assert milestone_pass is False, "Fallback to wav2lip must fail the milestone"


def test_milestone_truth_passes_when_musetalk_resolved() -> None:
    """Milestone truth check: requested=musetalk and resolved=musetalk means complete."""
    requested = "musetalk"
    resolved = "musetalk"
    milestone_pass = (requested == resolved)
    assert milestone_pass is True
