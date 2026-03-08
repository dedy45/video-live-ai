"""Avatar engine runtime resolver.

Resolves the requested engine to the best available one at runtime.
If musetalk is requested but its model/avatar dirs are missing,
automatically degrades to wav2lip.
"""

from __future__ import annotations

from pathlib import Path

from src.utils.logging import get_logger

logger = get_logger("engine_resolver")

# Default paths relative to external/livetalking
_DEFAULT_MUSETALK_MODEL_DIR = Path("external/livetalking/models/musetalk")
_DEFAULT_MUSETALK_AVATAR_DIR = Path("external/livetalking/data/avatars")
_DEFAULT_AVATARS = {
    "musetalk": "musetalk_avatar1",
    "wav2lip": "wav2lip256_avatar1",
}


def resolve_engine(
    requested: str,
    *,
    musetalk_model_dir: Path | None = None,
    musetalk_avatar_dir: Path | None = None,
) -> str:
    """Resolve the requested avatar engine to the best available one.

    Args:
        requested: Engine name from config (e.g. "musetalk", "wav2lip").
        musetalk_model_dir: Path to MuseTalk model weights directory.
        musetalk_avatar_dir: Path to MuseTalk avatar data directory.

    Returns:
        The engine to actually use. Falls back to "wav2lip" when
        MuseTalk prerequisites are missing.
    """
    if requested != "musetalk":
        return requested

    model_dir = musetalk_model_dir or _DEFAULT_MUSETALK_MODEL_DIR
    avatar_dir = musetalk_avatar_dir or _DEFAULT_MUSETALK_AVATAR_DIR

    if not model_dir.exists():
        logger.warning(
            "musetalk_model_missing",
            path=str(model_dir),
            msg="MuseTalk model not found — falling back to wav2lip",
        )
        return "wav2lip"

    if not avatar_dir.exists():
        logger.warning(
            "musetalk_avatar_missing",
            path=str(avatar_dir),
            msg="MuseTalk avatar data not found — falling back to wav2lip",
        )
        return "wav2lip"

    logger.info("engine_resolved", engine="musetalk")
    return "musetalk"


def resolve_avatar_id(
    requested_avatar_id: str,
    resolved_model: str,
    *,
    avatars_dir: Path | None = None,
) -> str:
    """Resolve the avatar ID for the resolved engine.

    When the requested avatar does not exist for the resolved engine, fall back
    to a known-good default avatar for that engine.
    """
    avatar_root = avatars_dir or _DEFAULT_MUSETALK_AVATAR_DIR
    requested_path = avatar_root / requested_avatar_id
    if requested_path.exists():
        return requested_avatar_id

    fallback_avatar = _DEFAULT_AVATARS.get(resolved_model, requested_avatar_id)
    if fallback_avatar != requested_avatar_id:
        logger.warning(
            "avatar_fallback_selected",
            requested_avatar_id=requested_avatar_id,
            resolved_model=resolved_model,
            fallback_avatar_id=fallback_avatar,
        )
    return fallback_avatar
