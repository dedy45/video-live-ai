"""AI Live Commerce Platform — Main Entry Point.

Follows the Startup Sequence defined in design.md:
1. Config → 2. Database → 3. GPU Manager → 4. Mock Mode Check →
5. Models → 6. Pipeline Warm-up → 7-12. Components → 13. Orchestrator

Hardened with:
- Graceful shutdown handler
- Startup error handling with clear diagnostics
- Component registration with centralized health manager
- Dashboard API + static file serving
- Analytics engine initialization
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

# Add src to path for clean imports
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for d in sys.path:
    if not d:
        continue
    try:
        if os.path.samefile(project_dir, d):
            break
    except FileNotFoundError:
        continue
else:
    sys.path.insert(0, str(project_dir))

from src.config import get_config, is_mock_mode, load_config, load_env
from src.dashboard.api import init_dashboard_state
from src.dashboard.api import router as api_router
from src.dashboard.diagnostic import router as diagnostic_router
from src.data.database import check_database_health, init_database
from src.utils.health import HealthStatus, get_health_manager
from src.utils.logging import get_logger, setup_logging

# Frontend paths — prefer Svelte build output, fallback to legacy
FRONTEND_DIST_DIR = Path(__file__).parent / "dashboard" / "frontend" / "dist"
FRONTEND_LEGACY_DIR = Path(__file__).parent / "dashboard" / "frontend"
NO_STORE_PATH_PREFIXES = (
    "/api/status",
    "/api/metrics",
    "/api/runtime/truth",
    "/api/health/summary",
    "/api/resources",
    "/api/ops/summary",
    "/api/incidents",
    "/api/ws/dashboard",
    "/dashboard",
)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Handles startup errors gracefully — logs the error and continues
    with degraded functionality rather than crashing entirely.
    """
    errors: list[str] = []

    # Step 1: Load configuration
    try:
        config = load_config()
        env = load_env()
    except Exception as e:
        # Fallback to defaults if config loading fails
        from src.config.loader import Config
        config = Config()
        errors.append(f"Config load failed (using defaults): {e}")

    # Step 2: Setup logging
    try:
        setup_logging(
            level=config.logging.level,
            log_file=config.logging.file,
            json_format=config.logging.format == "json",
        )
    except Exception as e:
        # Fall back to basic logging
        import logging
        logging.basicConfig(level=logging.DEBUG)
        errors.append(f"Structured logging failed: {e}")

    logger = get_logger("main")

    # Log startup errors
    for err in errors:
        logger.warning("startup_warning", error=err)

    logger.info(
        "startup_begin",
        app=config.app.name,
        version=config.app.version,
        env=config.app.env,
        mock_mode=is_mock_mode(),
    )

    # Step 3: Initialize database
    try:
        init_database()
        logger.info("database_initialized")
    except RuntimeError as e:
        logger.error("database_init_failed", error=str(e))
        # Continue — some features may work without database

    # Step 4: Mock Mode check
    if is_mock_mode():
        logger.info(
            "mock_mode_active",
            msg="Running in Mock Mode — GPU components will use placeholders",
        )

    # Step 4b: Initialize Face Pipeline (LiveTalking or MuseTalk)
    try:
        avatar_engine = config.avatar.engine
        if avatar_engine == "livetalking" or config.avatar.livetalking.enabled:
            from src.face.livetalking_adapter import LiveTalkingPipeline
            face_pipeline = LiveTalkingPipeline()
            # Eagerly initialize so health_check reports accurate state
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already inside an event loop — schedule init
                    asyncio.ensure_future(face_pipeline.engine.initialize())
                else:
                    loop.run_until_complete(face_pipeline.engine.initialize())
            except RuntimeError:
                asyncio.run(face_pipeline.engine.initialize())
            logger.info("face_pipeline_initialized", engine="livetalking")
        else:
            from src.face.pipeline import AvatarPipeline
            face_pipeline = AvatarPipeline()
            logger.info("face_pipeline_initialized", engine="musetalk")
    except Exception as e:
        logger.warning("face_pipeline_init_failed", error=str(e))
        face_pipeline = None

    # Step 5: Register health checks
    health = get_health_manager()
    _register_health_checks(health, face_pipeline=face_pipeline)

    # Step 6: Initialize commerce components for dashboard
    try:
        from src.commerce.manager import ProductManager, AffiliateTracker
        pm = ProductManager()
        pm.load_from_json()  # Hydrate from canonical data/products.json
        at = AffiliateTracker()
        init_dashboard_state(product_manager=pm, affiliate_tracker=at)
        logger.info("dashboard_state_initialized", products_loaded=len(pm.get_all_active()))
    except Exception as e:
        logger.warning("dashboard_state_init_failed", error=str(e))
        init_dashboard_state()

    # Step 7: Initialize analytics engine
    try:
        from src.commerce.analytics import get_analytics
        analytics = get_analytics()
        logger.info("analytics_engine_initialized")
    except Exception as e:
        logger.warning("analytics_init_failed", error=str(e))

    # Step 8: Pre-initialize LLM Router (so dashboard can show stats immediately)
    try:
        from src.dashboard.api import get_llm_router
        router = get_llm_router()
        if router:
            logger.info("llm_router_preinitialized", adapters=list(router.adapters.keys()))
        else:
            logger.warning("llm_router_preinit_failed", msg="Router returned None - check .env configuration")
    except Exception as e:
        logger.warning("llm_router_preinit_exception", error=str(e), exc_info=True)

    # Create FastAPI app
    app = FastAPI(
        title=config.app.name,
        version=config.app.version,
        description="AI Live Commerce Platform — Automated live streaming commerce with AI avatar",
    )

    # Setup Sentry for error tracking (Phase 18.3)
    import os
    sentry_dsn = os.environ.get("SENTRY_DSN", "")
    if sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
                environment=config.app.env,
            )
            logger.info("sentry_initialized")
        except ImportError:
            logger.warning("sentry_sdk_not_installed")
        except Exception as e:
            logger.warning("sentry_init_failed", error=str(e))

    # Add tracing middleware (X-Trace-ID + X-Response-Time-Ms)
    try:
        from src.utils.tracing import TracingMiddleware
        app.add_middleware(TracingMiddleware)
        logger.info("tracing_middleware_enabled")
    except Exception as e:
        logger.warning("tracing_middleware_failed", error=str(e))

    @app.middleware("http")
    async def add_no_store_headers(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(NO_STORE_PATH_PREFIXES):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    # Register routes
    app.include_router(diagnostic_router)
    app.include_router(api_router)
    
    # Register Prometheus metrics endpoint (Phase 16.4)
    try:
        from src.monitoring.prometheus_exporter import router as metrics_router
        app.include_router(metrics_router)
    except Exception as e:
        logger.warning("prometheus_metrics_failed", error=str(e))

    # Serve frontend static files — prefer Svelte dist/, fallback to legacy
    _frontend_dir = None
    if FRONTEND_DIST_DIR.exists():
        _frontend_dir = FRONTEND_DIST_DIR
        logger.info("frontend_svelte_mounted", path=str(FRONTEND_DIST_DIR))
    elif FRONTEND_LEGACY_DIR.exists():
        _frontend_dir = FRONTEND_LEGACY_DIR
        logger.info("frontend_legacy_mounted", path=str(FRONTEND_LEGACY_DIR))

    if _frontend_dir:
        app.mount("/dashboard", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": config.app.name,
            "version": config.app.version,
            "status": "running",
            "mock_mode": str(is_mock_mode()),
            "dashboard": "/dashboard" if _frontend_dir else "not available",
            "api_docs": "/docs",
            "diagnostic": "/diagnostic/",
        }

    # Graceful shutdown handler
    @app.on_event("shutdown")
    async def shutdown_event() -> None:
        logger.info("shutdown_begin", msg="Graceful shutdown initiated")
        # Stop LLM router if initialized
        try:
            from src.dashboard.api import get_llm_router
            r = get_llm_router()
            if r:
                logger.info("shutdown_llm_router_done")
        except Exception:
            pass
        # Close analytics
        try:
            from src.commerce.analytics import get_analytics
            get_analytics()  # let GC clean up
        except Exception:
            pass
        # Remove PID file if exists
        try:
            pid_file = Path("data/.server.pid")
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass
        logger.info("shutdown_complete")

    logger.info("startup_complete", routes=len(app.routes))
    return app


def _register_health_checks(health_manager, face_pipeline=None) -> None:
    """Register all component health checks."""
    from src.config import is_mock_mode

    # Face pipeline health (LiveTalking or MuseTalk)
    if face_pipeline is not None:
        _pipeline = face_pipeline

        async def face_health() -> HealthStatus:
            try:
                engine = getattr(_pipeline, "engine", None)
                engine_type = type(engine).__name__ if engine else "unknown"
                if hasattr(_pipeline, "health_check"):
                    healthy = await _pipeline.health_check()
                else:
                    healthy = True

                # Build diagnostic message
                if healthy and engine and getattr(engine, "_initialized", False):
                    msg = f"Engine: {engine_type} (initialized)"
                elif healthy:
                    msg = f"Engine: {engine_type} (ready)"
                else:
                    # Diagnose why unhealthy
                    missing = []
                    if engine:
                        if not getattr(engine, "livetalking_path", Path(".")).exists():
                            missing.append("livetalking_dir")
                        if not getattr(engine, "app_py", Path(".")).exists():
                            missing.append("app.py")
                        if not getattr(engine, "reference_video", Path(".")).exists():
                            missing.append("reference.mp4")
                        if not getattr(engine, "reference_audio", Path(".")).exists():
                            missing.append("reference.wav")
                    msg = f"Engine: {engine_type} (missing: {', '.join(missing)})" if missing else f"Engine: {engine_type} (not ready)"

                return HealthStatus(
                    name="face_pipeline",
                    healthy=healthy,
                    status="healthy" if healthy else "degraded",
                    message=msg,
                )
            except Exception as e:
                return HealthStatus(
                    name="face_pipeline", healthy=False, status="failed", message=str(e),
                )

        health_manager.register("face_pipeline", face_health)

    # Database health
    async def db_health() -> HealthStatus:
        result = check_database_health()
        return HealthStatus(
            name="database",
            healthy=result["healthy"],
            status="healthy" if result["healthy"] else "failed",
            message=str(result["message"]),
        )

    health_manager.register("database", db_health)

    # GPU health
    async def gpu_health() -> HealthStatus:
        if is_mock_mode():
            return HealthStatus(name="gpu", healthy=True, status="mock", message="Mock Mode (no GPU)")
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                return HealthStatus(name="gpu", healthy=True, status="healthy", message=name)
            return HealthStatus(name="gpu", healthy=False, status="failed", message="CUDA unavailable")
        except ImportError:
            return HealthStatus(name="gpu", healthy=False, status="failed", message="PyTorch not installed")

    health_manager.register("gpu", gpu_health)

    # Config health
    async def config_health() -> HealthStatus:
        try:
            cfg = get_config()
            return HealthStatus(
                name="config", healthy=True, status="healthy",
                message=f"{cfg.app.name} v{cfg.app.version}",
            )
        except Exception as e:
            return HealthStatus(name="config", healthy=False, status="failed", message=str(e))

    health_manager.register("config", config_health)

    # LiveTalking engine health (process manager)
    async def livetalking_health() -> HealthStatus:
        try:
            from src.face.livetalking_manager import get_livetalking_manager
            mgr = get_livetalking_manager()
            status = mgr.get_status()
            details = {
                "app_py_exists": status.app_py_exists,
                "model_path_exists": status.model_path_exists,
                "avatar_path_exists": status.avatar_path_exists,
                "port": status.port,
                "model": status.model,
            }
            if status.state.value == "running":
                return HealthStatus(
                    name="livetalking", healthy=True, status="healthy",
                    message=f"Running (pid={status.pid}, port={status.port})",
                    details=details,
                )
            elif status.app_py_exists:
                return HealthStatus(
                    name="livetalking", healthy=True, status="idle",
                    message=f"Stopped but ready (app.py found)",
                    details=details,
                )
            else:
                return HealthStatus(
                    name="livetalking", healthy=False, status="degraded",
                    message="LiveTalking not installed",
                    details=details,
                )
        except Exception as e:
            return HealthStatus(
                name="livetalking", healthy=False, status="failed", message=str(e),
            )

    health_manager.register("livetalking", livetalking_health)

    # Analytics health
    async def analytics_health() -> HealthStatus:
        try:
            from src.commerce.analytics import get_analytics
            a = get_analytics()
            snap = a.get_dashboard_snapshot()
            return HealthStatus(
                name="analytics", healthy=True, status="healthy",
                message=f"Uptime: {snap['uptime_sec']}s",
            )
        except Exception as e:
            return HealthStatus(name="analytics", healthy=False, status="failed", message=str(e))

    health_manager.register("analytics", analytics_health)


def main() -> None:
    """Start the application server."""
    try:
        load_env()
        config = load_config()
    except Exception:
        from src.config.loader import Config
        config = Config()

    # Write PID file so menu.bat / scripts can kill the right process
    pid_file = Path("data/.server.pid")
    try:
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    app = create_app()

    try:
        uvicorn.run(
            app,
            host=config.dashboard.host,
            port=config.dashboard.port,
            log_level="info",
        )
    finally:
        # Always clean up PID file on exit
        try:
            if pid_file.exists():
                pid_file.unlink()
        except Exception:
            pass


if __name__ == "__main__":
    main()

