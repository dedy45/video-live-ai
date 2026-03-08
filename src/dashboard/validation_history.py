"""Validation History — persists recent validation results for the dashboard.

Stores validation evidence in a project-local JSON log so the operator
can review past check outcomes from the Validation Console.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.utils.logging import get_logger

logger = get_logger("dashboard.validation_history")

_HISTORY_FILE = Path("data/validation_history.json")
_MAX_ENTRIES = 200


def _ensure_dir() -> None:
    _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict[str, Any]]:
    try:
        if _HISTORY_FILE.exists():
            return json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("validation_history_load_error", error=str(e))
    return []


def _save(entries: list[dict[str, Any]]) -> None:
    _ensure_dir()
    try:
        _HISTORY_FILE.write_text(
            json.dumps(entries[-_MAX_ENTRIES:], indent=2),
            encoding="utf-8",
        )
    except Exception as e:
        logger.error("validation_history_save_error", error=str(e))


def record_validation(
    check_name: str,
    status: str,
    checks: list[dict[str, Any]],
    provenance: str = "real_local",
    context: str = "",
) -> dict[str, Any]:
    """Record a validation result and return the entry."""
    entry = {
        "id": int(time.time() * 1000),
        "check_name": check_name,
        "status": status,
        "checks": checks,
        "provenance": provenance,
        "context": context,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load()
    entries.append(entry)
    _save(entries)
    logger.info("validation_recorded", check=check_name, status=status)
    return entry


def get_history(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent validation history entries."""
    entries = _load()
    return list(reversed(entries[-limit:]))


def clear_history() -> None:
    """Clear all validation history."""
    _save([])
