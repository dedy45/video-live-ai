"""FFmpeg discovery and readiness check.

Finds ffmpeg by checking PATH first, then well-known install locations
on Windows and Linux. This avoids failing silently when ffmpeg is
installed but not on the system PATH.
"""

from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger("ffmpeg")
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Well-known install directories per platform
_KNOWN_FFMPEG_PATHS: list[Path] = []
_PROJECT_LOCAL_FFMPEG_DIRS: list[Path] = [
    PROJECT_ROOT / "tools" / "ffmpeg" / "bin",
]

if platform.system() == "Windows":
    _KNOWN_FFMPEG_PATHS = [
        Path(r"C:\ffmpeg\bin"),
        Path(r"C:\Program Files\ffmpeg\bin"),
        Path(r"C:\Program Files (x86)\ffmpeg\bin"),
        Path(r"C:\tools\ffmpeg\bin"),
        Path.home() / "scoop" / "shims",
        Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages",
    ]
else:
    _KNOWN_FFMPEG_PATHS = [
        Path("/usr/bin"),
        Path("/usr/local/bin"),
        Path("/snap/bin"),
        Path("/opt/homebrew/bin"),
    ]

# Binary name differs by platform
_FFMPEG_NAMES = ("ffmpeg.exe",) if platform.system() == "Windows" else ("ffmpeg",)


def _find_in_directory(directory: Path) -> Path | None:
    """Find an ffmpeg binary inside a specific directory."""
    for name in _FFMPEG_NAMES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def _find_from_env() -> Path | None:
    """Resolve explicit FFmpeg environment overrides."""
    ffmpeg_bin = Path(os.environ["FFMPEG_BIN"]) if os.getenv("FFMPEG_BIN") else None
    if ffmpeg_bin and not ffmpeg_bin.is_absolute():
        ffmpeg_bin = PROJECT_ROOT / ffmpeg_bin
    if ffmpeg_bin and ffmpeg_bin.is_file():
        logger.info("ffmpeg_found_env_bin", path=str(ffmpeg_bin))
        return ffmpeg_bin

    ffmpeg_dir_value = os.getenv("FFMPEG_DIR")
    if not ffmpeg_dir_value:
        return None

    ffmpeg_dir = Path(ffmpeg_dir_value)
    if not ffmpeg_dir.is_absolute():
        ffmpeg_dir = PROJECT_ROOT / ffmpeg_dir
    candidates = [ffmpeg_dir, ffmpeg_dir / "bin"]
    for directory in candidates:
        binary = _find_in_directory(directory)
        if binary is not None:
            logger.info("ffmpeg_found_env_dir", path=str(binary))
            return binary
    return None


def find_ffmpeg() -> Path | None:
    """Locate the ffmpeg binary.

    Checks:
    1. System PATH (via shutil.which)
    2. Well-known install directories (_KNOWN_FFMPEG_PATHS)

    Returns:
        Path to the ffmpeg binary, or None if not found.
    """
    # 1. Explicit env vars
    env_path = _find_from_env()
    if env_path is not None:
        return env_path

    # 2. Project-local install
    for directory in _PROJECT_LOCAL_FFMPEG_DIRS:
        binary = _find_in_directory(directory)
        if binary is not None:
            logger.info("ffmpeg_found_project_local", path=str(binary))
            return binary

    # 3. Try PATH
    on_path = shutil.which("ffmpeg")
    if on_path:
        logger.debug("ffmpeg_found_on_path", path=on_path)
        return Path(on_path)

    # 4. Scan known install locations
    for directory in _KNOWN_FFMPEG_PATHS:
        if not directory.is_dir():
            continue
        binary = _find_in_directory(directory)
        if binary is not None:
            logger.info("ffmpeg_found_known_path", path=str(binary))
            return binary

    logger.warning("ffmpeg_not_found", msg="ffmpeg not on PATH or known locations")
    return None


def check_ffmpeg_ready() -> dict[str, Any]:
    """Check FFmpeg readiness and return a status dict.

    Returns:
        Dict with keys:
        - available (bool): whether ffmpeg was found
        - path (str | None): absolute path to binary, or None
    """
    path = find_ffmpeg()
    return {
        "available": path is not None,
        "path": str(path) if path else None,
    }
