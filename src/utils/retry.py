"""Retry Strategy — Exponential backoff with jitter.

Requirements: 14.1, 14.2
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass
from typing import Any, Callable, TypeVar

from src.utils.logging import get_logger

logger = get_logger("retry")

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay_sec: float = 1.0
    max_delay_sec: float = 30.0
    exponential_base: float = 2.0
    jitter: bool = True


class RetryExhaustedError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, attempts: int, last_error: Exception) -> None:
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(f"All {attempts} retry attempts exhausted. Last error: {last_error}")


async def retry_async(
    func: Callable[..., Any],
    *args: Any,
    config: RetryConfig | None = None,
    operation_name: str = "operation",
    **kwargs: Any,
) -> Any:
    """Execute an async function with exponential backoff retry.

    Args:
        func: Async callable to retry.
        config: Retry configuration.
        operation_name: Name for logging.
        *args, **kwargs: Arguments passed to func.

    Returns:
        Result of successful function call.

    Raises:
        RetryExhaustedError: If all attempts fail.
    """
    cfg = config or RetryConfig()
    last_error: Exception = Exception("No attempts made")

    for attempt in range(1, cfg.max_attempts + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt == cfg.max_attempts:
                logger.error(
                    "retry_exhausted",
                    operation=operation_name,
                    attempts=attempt,
                    error=str(e),
                )
                raise RetryExhaustedError(attempt, last_error) from e

            delay = min(
                cfg.base_delay_sec * (cfg.exponential_base ** (attempt - 1)),
                cfg.max_delay_sec,
            )
            if cfg.jitter:
                delay *= 0.5 + random.random()

            logger.warning(
                "retry_attempt",
                operation=operation_name,
                attempt=attempt,
                max_attempts=cfg.max_attempts,
                delay_sec=round(delay, 2),
                error=str(e),
            )
            await asyncio.sleep(delay)

    raise RetryExhaustedError(cfg.max_attempts, last_error)
