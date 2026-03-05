"""Circuit Breaker — Prevents cascading failures.

Requirements: 14.3, 14.4
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.utils.logging import get_logger

logger = get_logger("circuit_breaker")


class CircuitState(Enum):
    CLOSED = "closed"      # Normal — requests flow through
    OPEN = "open"          # Tripped — requests rejected immediately
    HALF_OPEN = "half_open"  # Testing — one probe request allowed


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5        # Failures before opening
    recovery_timeout_sec: float = 30  # Time before trying half-open
    success_threshold: int = 2        # Successes in half-open to close


class CircuitOpenError(Exception):
    """Raised when circuit is open and request is rejected."""

    def __init__(self, name: str, retry_after_sec: float) -> None:
        self.name = name
        self.retry_after_sec = retry_after_sec
        super().__init__(
            f"Circuit '{name}' is OPEN. Retry after {retry_after_sec:.1f}s"
        )


class CircuitBreaker:
    """Circuit breaker for external service calls.

    States:
    - CLOSED: Normal operation. Counts failures.
    - OPEN: All calls rejected. Waits for recovery timeout.
    - HALF_OPEN: Allows one probe. Success → CLOSED, Failure → OPEN.
    """

    def __init__(self, name: str, config: CircuitBreakerConfig | None = None) -> None:
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        self._total_trips = 0

        logger.info("circuit_breaker_init", name=name)

    def record_success(self) -> None:
        """Record a successful call."""
        if self.state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._close()
        elif self.state == CircuitState.CLOSED:
            self._failure_count = 0

    def record_failure(self) -> None:
        """Record a failed call."""
        self._last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                self._open()

    def can_execute(self) -> bool:
        """Check if a request is allowed through the circuit.

        Raises:
            CircuitOpenError: If circuit is open.
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.config.recovery_timeout_sec:
                self._half_open()
                return True
            raise CircuitOpenError(
                self.name,
                self.config.recovery_timeout_sec - elapsed,
            )

        # HALF_OPEN — allow one probe
        return True

    async def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute function through circuit breaker.

        Args:
            func: Async callable to execute.

        Returns:
            Result of func.

        Raises:
            CircuitOpenError: If circuit is open.
        """
        self.can_execute()

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure()
            raise

    def _open(self) -> None:
        self.state = CircuitState.OPEN
        self._total_trips += 1
        logger.warning(
            "circuit_opened",
            name=self.name,
            failures=self._failure_count,
            total_trips=self._total_trips,
        )

    def _close(self) -> None:
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        logger.info("circuit_closed", name=self.name)

    def _half_open(self) -> None:
        self.state = CircuitState.HALF_OPEN
        self._success_count = 0
        logger.info("circuit_half_open", name=self.name)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "total_trips": self._total_trips,
        }
