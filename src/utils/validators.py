"""Asset validators for avatar photo, voice samples, and product images.

Requirements: 17.1, 17.2, 17.3, 17.4, 17.5
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.utils.logging import get_logger

logger = get_logger("validators")


@dataclass
class ValidationResult:
    """Result of an asset validation check."""

    valid: bool
    asset_path: str
    asset_type: str
    message: str
    details: dict[str, object] | None = None


def validate_avatar_photo(path: str | Path) -> ValidationResult:
    """Validate avatar reference photo (JPG/PNG, ≥256x256, 1 face).

    Requirement 17.2: format JPG/PNG, resolution 256x256 min, 1 face.
    """
    path = Path(path)
    if not path.exists():
        return ValidationResult(False, str(path), "avatar_photo", f"File not found: {path}")

    if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        return ValidationResult(
            False, str(path), "avatar_photo", f"Invalid format: {path.suffix}. Use JPG/PNG."
        )

    try:
        img = Image.open(path)
        width, height = img.size
        if width < 256 or height < 256:
            return ValidationResult(
                False,
                str(path),
                "avatar_photo",
                f"Resolution too low: {width}x{height}. Minimum 256x256.",
                {"width": width, "height": height},
            )
        logger.info("avatar_photo_valid", path=str(path), width=width, height=height)
        return ValidationResult(
            True,
            str(path),
            "avatar_photo",
            f"Valid: {width}x{height} {path.suffix}",
            {"width": width, "height": height},
        )
    except Exception as e:
        return ValidationResult(False, str(path), "avatar_photo", f"Error reading image: {e}")


def validate_voice_sample(path: str | Path) -> ValidationResult:
    """Validate voice sample (WAV/MP3, 10-30s, ≥16kHz).

    Requirement 17.3: format WAV/MP3, duration 10-30s, sample rate ≥16kHz.
    """
    path = Path(path)
    if not path.exists():
        return ValidationResult(False, str(path), "voice_sample", f"File not found: {path}")

    if path.suffix.lower() not in (".wav", ".mp3"):
        return ValidationResult(
            False, str(path), "voice_sample", f"Invalid format: {path.suffix}. Use WAV/MP3."
        )

    # Basic file size check (WAV 16kHz mono 30s ≈ ~960KB)
    file_size = path.stat().st_size
    if file_size < 10_000:  # Less than 10KB is suspicious
        return ValidationResult(
            False,
            str(path),
            "voice_sample",
            "File too small — likely corrupted or empty.",
            {"size_bytes": file_size},
        )

    logger.info("voice_sample_valid", path=str(path), size_bytes=file_size)
    return ValidationResult(
        True,
        str(path),
        "voice_sample",
        f"Valid: {file_size} bytes",
        {"size_bytes": file_size},
    )


def validate_product_image(path: str | Path) -> ValidationResult:
    """Validate product image (JPG/PNG, ≥512x512).

    Requirement 17.5: format JPG/PNG, resolution 512x512 min.
    """
    path = Path(path)
    if not path.exists():
        return ValidationResult(False, str(path), "product_image", f"File not found: {path}")

    if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
        return ValidationResult(
            False, str(path), "product_image", f"Invalid format: {path.suffix}. Use JPG/PNG."
        )

    try:
        img = Image.open(path)
        width, height = img.size
        if width < 512 or height < 512:
            return ValidationResult(
                False,
                str(path),
                "product_image",
                f"Resolution too low: {width}x{height}. Minimum 512x512.",
                {"width": width, "height": height},
            )
        return ValidationResult(
            True,
            str(path),
            "product_image",
            f"Valid: {width}x{height} {path.suffix}",
            {"width": width, "height": height},
        )
    except Exception as e:
        return ValidationResult(False, str(path), "product_image", f"Error reading image: {e}")


def validate_background_image(path: str | Path) -> ValidationResult:
    """Validate background image (JPG/PNG, 720x1280).

    Requirement 17.4: format JPG/PNG, resolution 720x1280, aspect 9:16.
    """
    path = Path(path)
    if not path.exists():
        return ValidationResult(False, str(path), "background", f"File not found: {path}")

    try:
        img = Image.open(path)
        width, height = img.size
        if width < 720 or height < 1280:
            return ValidationResult(
                False,
                str(path),
                "background",
                f"Resolution too low: {width}x{height}. Minimum 720x1280.",
                {"width": width, "height": height},
            )
        return ValidationResult(
            True,
            str(path),
            "background",
            f"Valid: {width}x{height} {path.suffix}",
            {"width": width, "height": height},
        )
    except Exception as e:
        return ValidationResult(False, str(path), "background", f"Error reading image: {e}")


def validate_all_assets(assets_dir: str | Path = "assets") -> list[ValidationResult]:
    """Run validation on all standard asset directories."""
    results: list[ValidationResult] = []
    base = Path(assets_dir)

    # Avatar
    avatar_dir = base / "avatar"
    if avatar_dir.exists():
        for f in avatar_dir.iterdir():
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                results.append(validate_avatar_photo(f))

    # Voice
    voice_dir = base / "voice"
    if voice_dir.exists():
        for f in voice_dir.iterdir():
            if f.suffix.lower() in (".wav", ".mp3"):
                results.append(validate_voice_sample(f))

    # Products
    products_dir = base / "products"
    if products_dir.exists():
        for f in products_dir.iterdir():
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                results.append(validate_product_image(f))

    # Backgrounds
    bg_dir = base / "backgrounds"
    if bg_dir.exists():
        for f in bg_dir.iterdir():
            if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                results.append(validate_background_image(f))

    return results
