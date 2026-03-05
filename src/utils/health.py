"""Centralized Health Check System.

Provides a unified health check registry for all system components.
Each layer/component registers its health check function.
Requirements: 28.1, 20.6
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from src.utils.logging import get_logger

logger = get_logger("health")


@dataclass
class HealthStatus:
    """Health status of a single component."""

    name: str
    healthy: bool
    status: str  # healthy | degraded | failed | mock | unknown
    message: str = ""
    latency_ms: float = 0.0
    details: dict[str, Any] | None = None


# Type for health check functions
HealthCheckFn = Callable[[], Awaitable[HealthStatus]]


class HealthManager:
    """Centralized health check manager.

    Components register their health check functions, and the manager
    runs them all (with timeout protection) when requested.
    """

    def __init__(self, timeout_sec: float = 5.0) -> None:
        self._checks: dict[str, HealthCheckFn] = {}
        self._timeout_sec = timeout_sec
        self._last_results: dict[str, HealthStatus] = {}

    def register(self, name: str, check_fn: HealthCheckFn) -> None:
        """Register a health check function for a component."""
        self._checks[name] = check_fn
        logger.debug("health_check_registered", component=name)

    async def check_one(self, name: str) -> HealthStatus:
        """Run a single health check with timeout."""
        check_fn = self._checks.get(name)
        if not check_fn:
            return HealthStatus(name=name, healthy=False, status="unknown", message="Not registered")

        start = time.time()
        try:
            result = await asyncio.wait_for(check_fn(), timeout=self._timeout_sec)
            result.latency_ms = (time.time() - start) * 1000
            self._last_results[name] = result
            return result
        except asyncio.TimeoutError:
            status = HealthStatus(
                name=name, healthy=False, status="failed",
                message=f"Health check timed out ({self._timeout_sec}s)",
                latency_ms=(time.time() - start) * 1000,
            )
            self._last_results[name] = status
            logger.warning("health_check_timeout", component=name)
            return status
        except Exception as e:
            status = HealthStatus(
                name=name, healthy=False, status="failed",
                message=f"Error: {e}",
                latency_ms=(time.time() - start) * 1000,
            )
            self._last_results[name] = status
            logger.error("health_check_error", component=name, error=str(e))
            return status

    async def check_all(self) -> list[HealthStatus]:
        """Run all registered health checks concurrently.

        Returns list of HealthStatus, one per component.
        Each check is individually timeout-protected.
        """
        if not self._checks:
            return []

        tasks = [self.check_one(name) for name in self._checks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        statuses: list[HealthStatus] = []
        for i, result in enumerate(results):
            name = list(self._checks.keys())[i]
            if isinstance(result, Exception):
                statuses.append(HealthStatus(
                    name=name, healthy=False, status="failed",
                    message=f"Gather error: {result}",
                ))
            else:
                statuses.append(result)

        return statuses

    @property
    def overall_healthy(self) -> bool:
        """Check if all components are healthy (from last check)."""
        if not self._last_results:
            return False
        return all(s.healthy for s in self._last_results.values())

    @property
    def overall_status(self) -> str:
        """Get overall system status from last check."""
        if not self._last_results:
            return "unknown"
        failed = sum(1 for s in self._last_results.values() if not s.healthy)
        if failed == 0:
            return "healthy"
        elif failed <= 2:
            return "degraded"
        return "failed"

    def get_summary(self) -> dict[str, Any]:
        """Get summary of last health check results."""
        return {
            "overall": self.overall_status,
            "components": {
                name: {"healthy": s.healthy, "status": s.status, "message": s.message}
                for name, s in self._last_results.items()
            },
            "registered_count": len(self._checks),
        }


# Global singleton
_health_manager: HealthManager | None = None


def get_health_manager() -> HealthManager:
    """Get or create the global health manager."""
    global _health_manager
    if _health_manager is None:
        _health_manager = HealthManager()
    return _health_manager
