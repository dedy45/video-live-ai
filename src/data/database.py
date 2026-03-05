"""Database initialization and connection management.

Requirements: 7.1, 11.9, 22.2
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from src.utils.logging import get_logger

logger = get_logger("database")

DB_PATH = Path("data/commerce.db")
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_database(db_path: Path | None = None) -> None:
    """Initialize database with schema.

    Creates the database file and parent directories if needed.
    Uses IF NOT EXISTS to be idempotent (safe to call multiple times).

    Args:
        db_path: Path to SQLite database file.

    Raises:
        RuntimeError: If database initialization fails.
    """
    path = db_path or DB_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(str(path)) as conn:
            # Enable WAL mode for concurrent reads
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")

            # Read and execute schema
            if SCHEMA_PATH.exists():
                schema = SCHEMA_PATH.read_text(encoding="utf-8")
                conn.executescript(schema)
                logger.info("database_initialized", path=str(path))
            else:
                logger.warning("schema_not_found", path=str(SCHEMA_PATH))

    except sqlite3.Error as e:
        logger.error("database_init_failed", error=str(e), path=str(path))
        raise RuntimeError(f"Database initialization failed: {e}") from e
    except OSError as e:
        logger.error("database_dir_error", error=str(e), path=str(path))
        raise RuntimeError(f"Cannot create database directory: {e}") from e


def check_database_health(db_path: Path | None = None) -> dict[str, str | bool]:
    """Check database health — used by diagnostic endpoint.

    Returns:
        Dict with keys: healthy (bool), message (str), tables (int).
    """
    path = db_path or DB_PATH
    if not path.exists():
        return {"healthy": False, "message": "Database file not found", "tables": 0}

    try:
        conn = sqlite3.connect(str(path))
        conn.execute("PRAGMA integrity_check")

        # Count tables
        cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        conn.close()
        return {"healthy": True, "message": f"OK — {table_count} tables", "tables": table_count}

    except sqlite3.Error as e:
        return {"healthy": False, "message": f"Error: {e}", "tables": 0}


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Get a database connection with row_factory.

    Uses WAL mode for concurrent reads during streaming.
    Auto-commits on success, rolls back on failure.

    Args:
        db_path: Path to SQLite database file.

    Yields:
        SQLite connection.

    Raises:
        sqlite3.Error: On database errors (after rollback).
    """
    path = db_path or DB_PATH
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(str(path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        if conn:
            conn.rollback()
        logger.error("database_error", error=str(e))
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("database_unexpected_error", error=str(e))
        raise
    finally:
        if conn:
            conn.close()
