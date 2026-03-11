"""Regression tests for the Windows operator menu wrapper."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MENU_PATH = PROJECT_ROOT / "scripts" / "menu.bat"


def test_menu_exposes_unified_cli_sections() -> None:
    """Menu should present setup, start/stop, status, validate, and open groups."""
    content = MENU_PATH.read_text(encoding="utf-8")

    assert "SETUP" in content
    assert "START / STOP" in content
    assert "STATUS / HEALTH" in content
    assert "VALIDATE" in content
    assert "OPEN" in content


def test_menu_delegates_to_unified_manage_commands() -> None:
    """Menu should delegate to the new manage.py command surface."""
    content = MENU_PATH.read_text(encoding="utf-8")

    for command in (
        "manage.py setup all",
        "manage.py setup fish-speech",
        "manage.py start fish-speech",
        "manage.py start livetalking --mode musetalk",
        "manage.py status all",
        "manage.py open performer",
        "manage.py open monitor",
    ):
        assert command in content


def test_menu_no_longer_calls_legacy_root_batch_files() -> None:
    """The menu must no longer use the scattered legacy batch scripts as logic sources."""
    content = MENU_PATH.read_text(encoding="utf-8")

    for legacy_name in (
        "install_full_dependencies.bat",
        "install_livetalking_deps.bat",
        "run_livetalking_musetalk.bat",
        "run_livetalking_web.bat",
        "setup_livetalking_verbose.bat",
        "setup_musetalk_model.bat",
    ):
        assert legacy_name not in content
