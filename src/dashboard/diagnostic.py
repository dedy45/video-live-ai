"""Diagnostic API endpoint for early pipeline testing.

Provides system health checks, component status, and pipeline verification.
Uses centralized HealthManager for actual component checks.
Requirements: 28.1, 20.6
"""

from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel

from src.config import get_config, is_mock_mode
from src.data.database import check_database_health
from src.utils.health import get_health_manager
from src.utils.logging import get_logger

logger = get_logger("diagnostic")

router = APIRouter(prefix="/diagnostic", tags=["diagnostic"])


class ComponentStatus(BaseModel):
    """Status of a single system component."""

    name: str
    status: str  # healthy | degraded | failed | mock
    message: str = ""
    latency_ms: float = 0.0


class DiagnosticReport(BaseModel):
    """Full system diagnostic report."""

    timestamp: float
    system: dict[str, str]
    mock_mode: bool
    config_loaded: bool
    database: dict[str, Any]
    components: list[ComponentStatus]
    overall_status: str  # healthy | degraded | failed


@router.get("/", response_model=DiagnosticReport)
async def run_diagnostic() -> DiagnosticReport:
    """Run full system diagnostic and return health report.

    Uses centralized HealthManager for actual component checks,
    with timeout protection per component.
    """
    start = time.time()
    components: list[ComponentStatus] = []

    # 1. System Info
    system_info = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "machine": platform.machine(),
        "pid": str(os.getpid()),
    }

    # 2. Config Check
    config_ok = False
    try:
        config = get_config()
        config_ok = True
        components.append(
            ComponentStatus(name="config", status="healthy", message=f"v{config.app.version}")
        )
    except Exception as e:
        components.append(
            ComponentStatus(name="config", status="failed", message=str(e)[:200])
        )

    # 3. Run all registered health checks
    health = get_health_manager()
    health_results = await health.check_all()
    for hs in health_results:
        components.append(
            ComponentStatus(
                name=hs.name,
                status=hs.status,
                message=hs.message,
                latency_ms=round(hs.latency_ms, 2),
            )
        )

    # 4. Database detailed status
    db_status = check_database_health()

    # 5. Mock Mode indicator
    mock = is_mock_mode()
    if mock:
        components.append(
            ComponentStatus(name="mock_mode", status="mock", message="Mock Mode active (GPU-less)")
        )

    # 6. Layer checks — check if modules are importable
    layer_modules = {
        "brain": "src.brain",
        "voice": "src.voice",
        "face": "src.face",
        "composition": "src.composition",
        "stream": "src.stream",
        "chat": "src.chat",
        "commerce": "src.commerce",
        "orchestrator": "src.orchestrator",
    }
    for layer_name, module_path in layer_modules.items():
        # Skip if already checked by health manager
        if any(c.name == layer_name for c in components):
            continue
        try:
            __import__(module_path)
            components.append(
                ComponentStatus(
                    name=layer_name,
                    status="mock" if mock else "healthy",
                    message="Module loaded" if not mock else "Mock Mode",
                )
            )
        except ImportError as e:
            components.append(
                ComponentStatus(name=layer_name, status="failed", message=f"Import error: {e}")
            )

    # Overall status
    failed = sum(1 for c in components if c.status == "failed")
    overall = "healthy" if failed == 0 else ("degraded" if failed <= 2 else "failed")

    elapsed_ms = (time.time() - start) * 1000
    logger.info("diagnostic_complete", overall=overall, elapsed_ms=round(elapsed_ms, 2))

    return DiagnosticReport(
        timestamp=time.time(),
        system=system_info,
        mock_mode=mock,
        config_loaded=config_ok,
        database=db_status,
        components=components,
        overall_status=overall,
    )


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Simple health check for monitoring tools (Prometheus, etc.)."""
    return {"status": "ok", "mock_mode": str(is_mock_mode())}


@router.get("/health/detailed")
async def detailed_health() -> dict[str, Any]:
    """Detailed health check using centralized HealthManager."""
    health = get_health_manager()
    results = await health.check_all()
    return {
        "overall": health.overall_status,
        "components": {
            r.name: {"healthy": r.healthy, "status": r.status, "message": r.message, "latency_ms": round(r.latency_ms, 2)}
            for r in results
        },
    }


def create_diagnostic_app() -> FastAPI:
    """Create a standalone diagnostic FastAPI app for testing."""
    app = FastAPI(title="AI Live Commerce — Diagnostic", version="0.1.0")
    app.include_router(router)
    return app
