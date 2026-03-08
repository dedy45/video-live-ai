#!/usr/bin/env python3
"""Download and normalize a project-local FFmpeg binary."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FFMPEG_DIR = PROJECT_ROOT / "tools" / "ffmpeg"
FFMPEG_BIN_DIR = FFMPEG_DIR / "bin"
FFMPEG_ENV_VALUE = "tools/ffmpeg/bin/ffmpeg.exe"
WINDOWS_FFMPEG_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/"
    "ffmpeg-master-latest-win64-gpl.zip"
)


def upsert_env_var(env_path: Path, key: str, value: str) -> None:
    """Insert or replace an env var in .env."""
    lines: list[str] = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    new_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def download_ffmpeg_windows(force: bool = False) -> Path:
    """Download a portable FFmpeg build for Windows."""
    target_bin = FFMPEG_BIN_DIR / "ffmpeg.exe"
    if target_bin.exists() and not force:
        return target_bin

    temp_zip = FFMPEG_DIR / "ffmpeg.zip"
    extract_dir = FFMPEG_DIR / "_extract"

    FFMPEG_DIR.mkdir(parents=True, exist_ok=True)
    if extract_dir.exists():
        shutil.rmtree(extract_dir)

    print(f"Downloading FFmpeg from: {WINDOWS_FFMPEG_URL}")
    urllib.request.urlretrieve(WINDOWS_FFMPEG_URL, temp_zip)

    print(f"Extracting to: {extract_dir}")
    with zipfile.ZipFile(temp_zip) as archive:
        archive.extractall(extract_dir)

    found_bin = next(extract_dir.rglob("ffmpeg.exe"), None)
    if found_bin is None:
        raise FileNotFoundError("Downloaded archive does not contain ffmpeg.exe")

    source_bin_dir = found_bin.parent
    if FFMPEG_BIN_DIR.exists():
        shutil.rmtree(FFMPEG_BIN_DIR)
    shutil.copytree(source_bin_dir, FFMPEG_BIN_DIR)

    temp_zip.unlink(missing_ok=True)
    shutil.rmtree(extract_dir, ignore_errors=True)
    return target_bin


def verify_ffmpeg(ffmpeg_bin: Path) -> None:
    """Run `ffmpeg -version` to verify installation."""
    result = subprocess.run(
        [str(ffmpeg_bin), "-version"],
        capture_output=True,
        text=True,
        check=True,
    )
    first_line = result.stdout.splitlines()[0] if result.stdout else "ffmpeg verified"
    print(first_line)


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup project-local FFmpeg")
    parser.add_argument("--force", action="store_true", help="Re-download even if FFmpeg already exists")
    args = parser.parse_args()

    if sys.platform != "win32":
        print("setup_ffmpeg.py currently automates Windows portable install only.")
        print("On Ubuntu, install ffmpeg with apt and optionally set FFMPEG_BIN.")
        return 1

    ffmpeg_bin = download_ffmpeg_windows(force=args.force)
    verify_ffmpeg(ffmpeg_bin)

    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        upsert_env_var(env_path, "FFMPEG_BIN", FFMPEG_ENV_VALUE)
        print(f"Updated {env_path} with FFMPEG_BIN={FFMPEG_ENV_VALUE}")
    else:
        print(".env not found; skipped env update")

    print(f"Project-local FFmpeg ready: {ffmpeg_bin}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
