"""Structured logging setup using structlog.

Provides consistent JSON logging with component context, trace IDs,
and per-component log levels.
Requirements: 16.1, 16.2, 16.3, 16.7, 16.12, 34.1
"""

from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

import structlog


def setup_logging(
    level: str = "DEBUG",
    log_file: str | None = None,
    json_format: bool = True,
) -> None:
    """Initialize structured logging.

    Args:
        level: Default log level.
        log_file: Path to log file (optional).
        json_format: If True, output JSON; otherwise, human-readable.
    """
    # Ensure log directory exists
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure stdlib logging
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, level.upper(), logging.DEBUG),
        handlers=handlers,
        force=True,
    )

    # Configure structlog
    processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(component: str) -> structlog.stdlib.BoundLogger:
    """Get a logger bound to a specific component.

    Args:
        component: Component name (brain, voice, face, etc.)

    Returns:
        Bound structlog logger with component context.
    """
    return structlog.get_logger(component=component)


def generate_trace_id() -> str:
    """Generate a unique trace ID for request correlation.

    Requirement 34.1: UUID trace_id per incoming event.
    """
    return str(uuid.uuid4())
