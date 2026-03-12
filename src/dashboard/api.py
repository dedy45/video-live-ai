"""Dashboard REST API — Control and monitoring endpoints.

Provides full system control: status, metrics, products, stream, LLM brain,
emergency stop, and interactive pipeline workflow.
Requirements: 11.1, 11.2, 11.3, 11.4, 11.5

Error handling strategy:
  - Every endpoint wrapped in try/except
  - Errors logged via structlog with full context
  - User receives JSON error (never raw 500 crash)
  - WebSocket errors logged and connection closed gracefully
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.brain.prompt_registry import get_prompt_registry
from src.commerce.analytics import get_analytics
from src.commerce.manager import AffiliateTracker, Product, ProductManager
from src.config import get_config, get_env, is_mock_mode
from src.utils.health import get_health_manager
from src.dashboard.incidents import get_incident_registry
from src.dashboard.ops_state import get_ops_state
from src.dashboard.resources import get_resource_metrics, get_restart_counters
from src.dashboard.truth import get_runtime_truth_snapshot
from src.dashboard.validation_history import record_validation, get_history as get_validation_history
from src.orchestrator.show_director import get_show_director
from src.utils.ffmpeg import check_ffmpeg_ready
from src.utils.logging import get_logger

logger = get_logger("dashboard.api")

router = APIRouter(prefix="/api", tags=["dashboard"])


# ── Response Models ──────────────────────────────────────────────

class SystemStatus(BaseModel):
    state: str
    mock_mode: bool
    uptime_sec: float
    viewer_count: int
    current_product: dict[str, Any] | None
    stream_status: str
    llm_budget_remaining: float
    safety_incidents: int


class MetricsResponse(BaseModel):
    latency: dict[str, dict[str, float]]
    revenue: dict[str, float]
    counters: dict[str, int]
    gauges: dict[str, float]


class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
    price_formatted: str
    category: str
    is_active: bool


class ChatEventResponse(BaseModel):
    platform: str
    username: str
    message: str
    intent: str
    priority: int
    timestamp: float


class BrainTestRequest(BaseModel):
    """Request to test LLM Brain with a prompt."""
    system_prompt: str = ""
    user_prompt: str = "Halo, perkenalkan produk ini!"
    task_type: str = "chat_reply"
    provider: str | None = None


class BrainTestResponse(BaseModel):
    """Response from LLM Brain test."""
    text: str
    provider: str
    model: str
    task_type: str
    latency_ms: float
    cost_usd: float
    success: bool
    error: str = ""
    input_tokens: int = 0
    output_tokens: int = 0


# ── Shared state (initialized by main.py) ────────────────────────

_product_manager: ProductManager | None = None
_affiliate_tracker: AffiliateTracker | None = None
_system_start_time = time.time()

# Shared LLM Router instance
_llm_router = None

# Recent chat events buffer
_recent_chats: list[dict[str, Any]] = []
MAX_RECENT_CHATS = 50

# Brain health cache (to avoid slow health checks on every request)
_brain_health_cache: dict[str, Any] | None = None
_brain_health_cache_time: float = 0.0
BRAIN_HEALTH_CACHE_TTL = 30.0  # Cache for 30 seconds


def init_dashboard_state(
    product_manager: ProductManager | None = None,
    affiliate_tracker: AffiliateTracker | None = None,
) -> None:
    """Initialize dashboard shared state from main app."""
    global _product_manager, _affiliate_tracker
    _product_manager = product_manager or ProductManager()
    _affiliate_tracker = affiliate_tracker or AffiliateTracker()


def get_llm_router():
    """Get or create the shared LLM Router instance."""
    global _llm_router
    if _llm_router is None:
        try:
            from src.brain.router import LLMRouter
            logger.info("llm_router_initializing")
            _llm_router = LLMRouter()
            logger.info("llm_router_initialized", adapters=list(_llm_router.adapters.keys()))
        except Exception as e:
            logger.error("llm_router_init_failed", error=str(e), exc_info=True)
            return None
    return _llm_router


def record_chat_event(event: dict[str, Any]) -> None:
    """Record a chat event for the dashboard. Thread-safe via GIL."""
    _recent_chats.append(event)
    if len(_recent_chats) > MAX_RECENT_CHATS:
        _recent_chats.pop(0)


def _get_director_runtime_contract() -> dict[str, Any]:
    """Build the aggregated director + brain + prompt runtime contract."""
    director = get_show_director().get_runtime_snapshot()
    prompt = get_prompt_registry().get_active_revision()
    router_instance = get_llm_router()
    routing_table: dict[str, list[str]] = {}
    adapter_count = 0

    if router_instance is not None:
        adapter_count = len(router_instance.adapters)
        for task_type, providers in router_instance.routing_table.items():
            routing_table[task_type.value] = providers

    return {
        "director": director,
        "brain": {
            "active_provider": director["active_provider"],
            "active_model": director["active_model"],
            "routing_table": routing_table,
            "adapter_count": adapter_count,
            "daily_budget_usd": get_config().llm_providers.daily_budget_usd,
        },
        "prompt": {
            "active_revision": f'{prompt["slug"]}:v{prompt["version"]}',
            "slug": prompt["slug"],
            "version": prompt["version"],
            "status": prompt["status"],
            "updated_at": prompt["updated_at"],
        },
        "persona": prompt["persona"],
        "script": {
            "current_phase": director["current_phase"],
            "phase_sequence": director["phase_sequence"],
        },
    }


# ── System Endpoints ─────────────────────────────────────────────

@router.get("/status")
async def get_status() -> dict[str, Any]:
    """Get full system status (no auth required)."""
    try:
        analytics = get_analytics()
        pm = _product_manager or ProductManager()
        current = pm.get_current_product()
        gauges = analytics.get_gauges()
        counters = analytics.get_counters()
        director = get_show_director().get_runtime_snapshot()
        return {
            "state": director["state"],
            "mock_mode": is_mock_mode(),
            "uptime_sec": round(time.time() - _system_start_time, 0),
            "viewer_count": int(gauges.get("viewers", 0)),
            "current_product": {
                "id": current.id,
                "name": current.name,
                "price": current.price_formatted,
            } if current else None,
            "stream_status": "stopped" if director["emergency_stopped"] else ("live" if director["stream_running"] else "idle"),
            "stream_running": director["stream_running"],
            "emergency_stopped": director["emergency_stopped"],
            "llm_budget_remaining": gauges.get("llm_budget_remaining", 5.0),
            "safety_incidents": counters.get("safety_incident", 0),
        }
    except Exception as e:
        logger.error("status_endpoint_error", error=str(e), exc_info=True)
        director = get_show_director().get_runtime_snapshot()
        return {
            "state": "ERROR", "mock_mode": is_mock_mode(),
            "uptime_sec": round(time.time() - _system_start_time, 0),
            "error": str(e), "stream_running": director["stream_running"],
            "emergency_stopped": director["emergency_stopped"],
        }


@router.get("/metrics")
async def get_metrics(window: int = 60) -> dict[str, Any]:
    """Get aggregated metrics with configurable time window."""
    try:
        analytics = get_analytics()
        return {
            "latency": analytics.get_all_latency_stats(float(window)),
            "revenue": analytics.get_revenue_summary(float(window)),
            "counters": analytics.get_counters(),
            "gauges": analytics.get_gauges(),
            "window_sec": window,
        }
    except Exception as e:
        logger.error("metrics_endpoint_error", error=str(e), exc_info=True)
        return {"error": str(e), "latency": {}, "revenue": {}, "counters": {}, "gauges": {}}


# ── Product Endpoints ────────────────────────────────────────────

@router.get("/products")
async def list_products() -> list[dict[str, Any]]:
    """List all active products."""
    try:
        pm = _product_manager or ProductManager()
        return [
            {
                "id": p.id, "name": p.name, "price": p.price,
                "price_formatted": p.price_formatted,
                "category": p.category, "is_active": p.is_active,
                "affiliate_links": p.affiliate_links,
                "selling_points": p.selling_points,
                "commission_rate": p.commission_rate,
                "objection_handling": p.objection_handling,
                "compliance_notes": p.compliance_notes,
            }
            for p in pm.get_all_active()
        ]
    except Exception as e:
        logger.error("list_products_error", error=str(e), exc_info=True)
        return []


@router.post("/products/{product_id}/switch")
async def switch_product(product_id: int) -> dict[str, Any]:
    """Manually switch to a specific product."""
    try:
        pm = _product_manager or ProductManager()
        products = pm.get_all_active()
        target = next((p for p in products if p.id == product_id), None)
        if not target:
            raise HTTPException(404, f"Product {product_id} not found")
        for i, p in enumerate(pm._products):
            if p.id == product_id:
                pm._current_index = i
                break
        logger.info("product_switched", product_id=product_id, name=target.name)
        return {"status": "switched", "product": target.name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("switch_product_error", product_id=product_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to switch product: {e}")


# ── Chat Endpoints ───────────────────────────────────────────────

@router.get("/chat/recent", response_model=list[ChatEventResponse])
async def get_recent_chats(limit: int = 20) -> list[ChatEventResponse]:
    """Get recent chat events."""
    chats = _recent_chats[-limit:]
    return [
        ChatEventResponse(
            platform=c.get("platform", "unknown"),
            username=c.get("username", ""),
            message=c.get("message", ""),
            intent=c.get("intent", "general"),
            priority=c.get("priority", 4),
            timestamp=c.get("timestamp", 0),
        )
        for c in reversed(chats)
    ]


# ── Stream Control Endpoints ────────────────────────────────────

@router.post("/stream/start")
async def start_stream() -> dict[str, str]:
    """Start RTMP streaming."""
    director = get_show_director()
    try:
        director.start_stream()
    except RuntimeError as e:
        raise HTTPException(400, str(e)) from e
    logger.info("stream_start_api")
    return {"status": "started"}


@router.post("/stream/stop")
async def stop_stream() -> dict[str, str]:
    """Stop RTMP streaming gracefully."""
    get_show_director().stop_stream()
    logger.info("stream_stop_api")
    return {"status": "stopped"}


@router.post("/emergency-stop")
async def emergency_stop() -> dict[str, str]:
    """Emergency stop — halts all operations immediately."""
    get_show_director().emergency_stop()
    logger.critical("EMERGENCY_STOP")
    return {"status": "emergency_stopped", "message": "All operations halted. Use /api/emergency-reset to recover."}


@router.post("/emergency-reset")
async def emergency_reset() -> dict[str, str]:
    """Reset after emergency stop."""
    get_show_director().reset_emergency()
    logger.info("emergency_reset")
    return {"status": "reset", "message": "System ready to restart."}


# ── Pipeline State Machine ──────────────────────────────────────

@router.get("/pipeline/state")
async def get_pipeline_state() -> dict[str, Any]:
    """Get current pipeline state machine status."""
    director = get_show_director().get_runtime_snapshot()
    return {
        "state": director["state"],
        "stream_running": director["stream_running"],
        "emergency_stopped": director["emergency_stopped"],
        "history": director["history"],
        "valid_transitions": director["valid_transitions"],
    }


class TransitionRequest(BaseModel):
    target_state: str


@router.post("/pipeline/transition")
async def pipeline_transition(request: TransitionRequest) -> dict[str, Any]:
    """Transition pipeline to a new state."""
    director = get_show_director()
    previous = director.get_runtime_snapshot()["state"]
    try:
        updated = director.transition(request.target_state)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e

    logger.info("pipeline_transition", old=previous, new=updated["state"])
    return {"status": "transitioned", "from": previous, "to": updated["state"]}


def _get_valid_transitions() -> list[str]:
    """Return valid next states from current state."""
    return get_show_director().get_valid_transitions()


# ── LLM Brain Endpoints ─────────────────────────────────────────

@router.get("/brain/stats")
async def brain_stats() -> dict[str, Any]:
    """Get LLM Brain usage statistics."""
    try:
        router_instance = get_llm_router()
        if router_instance is None:
            logger.error("brain_stats_no_router", msg="LLM Router initialization failed - check logs")
            return {
                "error": "LLM Router not initialized - check server logs for details",
                "providers": {},
                "adapters": {},
                "routing_table": {},
                "hint": "Check if .env file exists and contains valid API keys"
            }

        stats = router_instance.get_usage_stats()

        from src.brain.adapters.base import TaskType
        routing_info: dict[str, Any] = {}
        for task_type, providers in router_instance.routing_table.items():
            routing_info[task_type.value] = providers

        adapters_info: dict[str, Any] = {}
        for name, adapter in router_instance.adapters.items():
            try:
                adapters_info[name] = {
                    "model": getattr(adapter, "_litellm_model", adapter.model),
                    "available": adapter.is_available,
                    "timeout_ms": adapter.timeout_ms,
                    "max_tokens": adapter.max_tokens,
                    "api_base": getattr(adapter, "_api_base", ""),
                }
            except Exception as ae:
                adapters_info[name] = {"error": str(ae)}

        logger.info("brain_stats_ok", adapter_count=len(adapters_info))
        return {
            "providers": stats,
            "routing_table": routing_info,
            "adapters": adapters_info,
        }
    except Exception as e:
        logger.error("brain_stats_error", error=str(e), exc_info=True)
        return {"error": str(e), "providers": {}, "adapters": {}, "routing_table": {}}


@router.get("/brain/health")
async def brain_health() -> dict[str, Any]:
    """Check health of all LLM providers (quick ping with caching)."""
    global _brain_health_cache, _brain_health_cache_time
    
    # Return cached result if still fresh
    now = time.time()
    if _brain_health_cache is not None and (now - _brain_health_cache_time) < BRAIN_HEALTH_CACHE_TTL:
        logger.debug("brain_health_cache_hit", age_sec=round(now - _brain_health_cache_time, 1))
        return _brain_health_cache
    
    try:
        router_instance = get_llm_router()
        if router_instance is None:
            logger.warning("brain_health_no_router")
            result = {"error": "LLM Router not initialized", "providers": {}}
            _brain_health_cache = result
            _brain_health_cache_time = now
            return result

        # Reduced timeout from 30s to 10s
        health = await asyncio.wait_for(
            router_instance.health_check_all(),
            timeout=10.0,
        )
        healthy_count = sum(1 for v in health.values() if v)
        logger.info("brain_health_ok", healthy=healthy_count, total=len(health))
        
        # Get current active provider
        current_provider = getattr(router_instance, 'current_provider', 'groq')
        
        result = {
            "providers": health,
            "mock_mode": is_mock_mode(),
            "healthy_count": healthy_count,
            "total_count": len(health),
            "current_provider": current_provider,  # Tambahkan current provider
        }
        
        # Cache the result
        _brain_health_cache = result
        _brain_health_cache_time = now
        return result
        
    except asyncio.TimeoutError:
        logger.error("brain_health_timeout")
        result = {"error": "Health check timed out", "providers": {}}
        # Cache error result too (shorter TTL via same mechanism)
        _brain_health_cache = result
        _brain_health_cache_time = now
        return result
    except Exception as e:
        logger.error("brain_health_error", error=str(e), exc_info=True)
        result = {"error": str(e), "providers": {}}
        _brain_health_cache = result
        _brain_health_cache_time = now
        return result


@router.post("/brain/test")
async def brain_test(request: BrainTestRequest) -> dict[str, Any]:
    """Send a test prompt through the LLM Brain router.

    Fully wrapped in try/except — never returns raw 500 error.
    All failures return success=False with error details in JSON.
    """
    logger.info(
        "brain_test_request",
        task_type=request.task_type,
        provider=request.provider or "auto",
        prompt_len=len(request.user_prompt),
    )

    router_instance = get_llm_router()
    if router_instance is None:
        logger.error("brain_test_no_router")
        return {
            "text": "", "provider": "none", "model": "none",
            "task_type": request.task_type, "latency_ms": 0.0,
            "cost_usd": 0.0, "success": False,
            "error": "LLM Router not initialized — check server logs",
            "input_tokens": 0, "output_tokens": 0,
        }

    try:
        from src.brain.adapters.base import TaskType
        from src.brain.persona import PersonaEngine
        try:
            task = TaskType(request.task_type)
        except ValueError:
            logger.warning("brain_test_invalid_task", task=request.task_type)
            task = TaskType.CHAT_REPLY

        logger.info(
            "brain_test_routing",
            task=task.value,
            preferred_provider=request.provider or "auto",
        )

        system_prompt = request.system_prompt or PersonaEngine().build_system_prompt(state="SELLING")

        response = await asyncio.wait_for(
            router_instance.route(
                system_prompt=system_prompt,
                user_prompt=request.user_prompt,
                task_type=task,
                preferred_provider=request.provider or None,
            ),
            timeout=90.0,  # Max 90s — pro models can be slow
        )

        get_show_director().update_brain_runtime(
            provider=response.provider,
            model=response.model,
            prompt_revision=_get_director_runtime_contract()["prompt"]["active_revision"],
        )

        logger.info(
            "brain_test_result",
            success=response.success,
            provider=response.provider,
            model=response.model,
            latency_ms=round(response.latency_ms, 1),
            tokens=response.input_tokens + response.output_tokens,
            error=response.error[:100] if response.error else "",
        )

        return {
            "text": response.text,
            "provider": response.provider,
            "model": response.model,
            "task_type": response.task_type.value,
            "latency_ms": round(response.latency_ms, 1),
            "cost_usd": round(response.cost_usd, 6),
            "success": response.success,
            "error": response.error or "",
            "input_tokens": response.input_tokens,
            "output_tokens": response.output_tokens,
        }

    except asyncio.TimeoutError:
        logger.error("brain_test_timeout", timeout_sec=90)
        return {
            "text": "", "provider": request.provider or "auto",
            "model": "unknown", "task_type": request.task_type,
            "latency_ms": 90000.0, "cost_usd": 0.0, "success": False,
            "error": "Request timed out after 90 seconds",
            "input_tokens": 0, "output_tokens": 0,
        }
    except Exception as e:
        logger.error("brain_test_exception", error=str(e), exc_info=True)
        return {
            "text": "", "provider": request.provider or "auto",
            "model": "unknown", "task_type": request.task_type,
            "latency_ms": 0.0, "cost_usd": 0.0, "success": False,
            "error": f"Internal error: {str(e)[:200]}",
            "input_tokens": 0, "output_tokens": 0,
        }


@router.get("/brain/config")
async def brain_config() -> dict[str, Any]:
    """Get LLM Brain configuration and routing table."""
    import os
    from src.brain.adapters.base import TaskType as TT
    try:
        config = get_config()
        llm_cfg = config.llm_providers

        # Get routing table from router instance if available
        router_instance = get_llm_router()
        routing_table: dict[str, list[str]] = {}
        if router_instance:
            for task_type, providers in router_instance.routing_table.items():
                routing_table[task_type.value] = providers

        prompt = get_prompt_registry().get_active_revision()

        return {
            "daily_budget_usd": llm_cfg.daily_budget_usd,
            "fallback_order": llm_cfg.fallback_order,
            "routing_table": routing_table,
            "prompt": {
                "active_revision": f'{prompt["slug"]}:v{prompt["version"]}',
                "slug": prompt["slug"],
                "version": prompt["version"],
                "status": prompt["status"],
            },
            "providers": {
                "gemini": {
                    "model": f"gemini/{llm_cfg.gemini.model}",
                    "timeout_ms": llm_cfg.gemini.timeout_ms,
                    "backend": "litellm",
                },
                "claude": {
                    "model": f"anthropic/{llm_cfg.claude.model}",
                    "timeout_ms": llm_cfg.claude.timeout_ms,
                    "backend": "litellm",
                },
                "gpt4o": {
                    "model": f"openai/{llm_cfg.gpt4o.model}",
                    "timeout_ms": llm_cfg.gpt4o.timeout_ms,
                    "backend": "litellm",
                },
                "groq": {
                    "model": "groq/llama-3.3-70b-versatile",
                    "timeout_ms": 8000,
                    "backend": "litellm",
                },
                "chutes": {
                    "model": "openai/MiniMaxAI/MiniMax-M2.5",
                    "api_base": "https://llm.chutes.ai/v1",
                    "timeout_ms": 30000,
                    "backend": "litellm",
                },
                "gemini_local_pro": {
                    "model": "openai/gemini-3.1-pro-high",
                    "api_base": os.getenv("LOCAL_GEMINI_URL", "http://127.0.0.1:8091/v1"),
                    "timeout_ms": 15000,
                    "backend": "litellm",
                    "cost": "free",
                },
                "gemini_local_flash": {
                    "model": "openai/gemini-3-flash",
                    "api_base": os.getenv("LOCAL_GEMINI_URL", "http://127.0.0.1:8091/v1"),
                    "timeout_ms": 8000,
                    "backend": "litellm",
                    "cost": "free",
                },
                "local": {
                    "model": f"openai/{llm_cfg.qwen.model}",
                    "api_base": os.getenv("LOCAL_LLM_URL", "http://localhost:11434/v1"),
                    "timeout_ms": llm_cfg.qwen.timeout_ms,
                    "backend": "litellm",
                    "cost": "free",
                },
            },
            "task_types": [t.value for t in TT],
        }
    except Exception as e:
        logger.error("brain_config_error", error=str(e))
        return {"error": str(e)}


@router.get("/director/runtime")
async def get_director_runtime() -> dict[str, Any]:
    """Return aggregated director, brain, prompt, and script runtime state."""
    try:
        return _get_director_runtime_contract()
    except Exception as e:
        logger.error("director_runtime_error", error=str(e), exc_info=True)
        return {
            "director": get_show_director().get_runtime_snapshot(),
            "brain": {"active_provider": "unknown", "active_model": "unknown", "routing_table": {}},
            "prompt": {"active_revision": "unknown", "slug": "unknown", "version": 0, "status": "error"},
            "persona": {},
            "script": {"current_phase": "unknown", "phase_sequence": []},
            "error": str(e),
        }


# ── Prompt Registry CRUD Endpoints ──────────────────────────────

@router.get("/brain/prompts")
async def list_prompt_revisions() -> list[dict[str, Any]]:
    """List all prompt revisions."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            rows = conn.execute(
                """
                SELECT id, slug, version, status, created_at, updated_at
                FROM prompt_revisions
                ORDER BY updated_at DESC
                """
            ).fetchall()
        return [
            {
                "id": row["id"],
                "slug": row["slug"],
                "version": row["version"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    except Exception as e:
        logger.error("list_prompts_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to list prompts: {e}")


@router.get("/brain/prompts/{revision_id}")
async def get_prompt_revision(revision_id: int) -> dict[str, Any]:
    """Get a specific prompt revision by ID."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            row = conn.execute(
                """
                SELECT id, slug, version, status, templates_json, persona_json, created_at, updated_at
                FROM prompt_revisions
                WHERE id = ?
                """,
                (revision_id,)
            ).fetchone()
        
        if row is None:
            raise HTTPException(404, f"Prompt revision {revision_id} not found")
        
        return {
            "id": row["id"],
            "slug": row["slug"],
            "version": row["version"],
            "status": row["status"],
            "templates": json.loads(row["templates_json"]),
            "persona": json.loads(row["persona_json"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to get prompt: {e}")


class CreatePromptRequest(BaseModel):
    slug: str
    templates: dict[str, str]
    persona: dict[str, Any]


@router.post("/brain/prompts")
async def create_prompt_revision(request: CreatePromptRequest) -> dict[str, Any]:
    """Create a new prompt revision (always starts as draft)."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            # Get next version for this slug
            max_version = conn.execute(
                "SELECT MAX(version) as max_v FROM prompt_revisions WHERE slug = ?",
                (request.slug,)
            ).fetchone()
            next_version = (max_version["max_v"] or 0) + 1
            
            # Insert new revision
            cursor = conn.execute(
                """
                INSERT INTO prompt_revisions (slug, version, status, templates_json, persona_json)
                VALUES (?, ?, 'draft', ?, ?)
                """,
                (
                    request.slug,
                    next_version,
                    json.dumps(request.templates, ensure_ascii=False),
                    json.dumps(request.persona, ensure_ascii=False),
                )
            )
            new_id = cursor.lastrowid
        
        logger.info("prompt_created", id=new_id, slug=request.slug, version=next_version)
        return {"id": new_id, "slug": request.slug, "version": next_version, "status": "draft"}
    except Exception as e:
        logger.error("create_prompt_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to create prompt: {e}")


class UpdatePromptRequest(BaseModel):
    templates: dict[str, str]
    persona: dict[str, Any]


@router.put("/brain/prompts/{revision_id}")
async def update_prompt_revision(revision_id: int, request: UpdatePromptRequest) -> dict[str, Any]:
    """Update a draft prompt revision (only drafts can be edited)."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            # Check if exists and is draft
            row = conn.execute(
                "SELECT status FROM prompt_revisions WHERE id = ?",
                (revision_id,)
            ).fetchone()
            
            if row is None:
                raise HTTPException(404, f"Prompt revision {revision_id} not found")
            
            if row["status"] != "draft":
                raise HTTPException(400, f"Cannot edit {row['status']} revision (only drafts can be edited)")
            
            # Update
            conn.execute(
                """
                UPDATE prompt_revisions
                SET templates_json = ?, persona_json = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    json.dumps(request.templates, ensure_ascii=False),
                    json.dumps(request.persona, ensure_ascii=False),
                    revision_id,
                )
            )
        
        logger.info("prompt_updated", id=revision_id)
        return {"id": revision_id, "status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to update prompt: {e}")


@router.post("/brain/prompts/{revision_id}/publish")
async def publish_prompt_revision(revision_id: int) -> dict[str, Any]:
    """Publish a draft revision (deactivates current active, activates this one)."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            # Check if exists and is draft
            row = conn.execute(
                "SELECT status, slug FROM prompt_revisions WHERE id = ?",
                (revision_id,)
            ).fetchone()
            
            if row is None:
                raise HTTPException(404, f"Prompt revision {revision_id} not found")
            
            if row["status"] != "draft":
                raise HTTPException(400, f"Cannot publish {row['status']} revision (only drafts can be published)")
            
            # Deactivate current active for this slug
            conn.execute(
                "UPDATE prompt_revisions SET status = 'inactive' WHERE slug = ? AND status = 'active'",
                (row["slug"],)
            )
            
            # Activate this revision
            conn.execute(
                "UPDATE prompt_revisions SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (revision_id,)
            )
        
        logger.info("prompt_published", id=revision_id, slug=row["slug"])
        return {"id": revision_id, "status": "active", "slug": row["slug"]}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("publish_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to publish prompt: {e}")


@router.delete("/brain/prompts/{revision_id}")
async def delete_prompt_revision(revision_id: int) -> dict[str, Any]:
    """Delete a draft prompt revision (only drafts can be deleted)."""
    try:
        registry = get_prompt_registry()
        with registry._connect() as conn:
            # Check if exists and is draft
            row = conn.execute(
                "SELECT status FROM prompt_revisions WHERE id = ?",
                (revision_id,)
            ).fetchone()
            
            if row is None:
                raise HTTPException(404, f"Prompt revision {revision_id} not found")
            
            if row["status"] != "draft":
                raise HTTPException(400, f"Cannot delete {row['status']} revision (only drafts can be deleted)")
            
            # Delete
            conn.execute("DELETE FROM prompt_revisions WHERE id = ?", (revision_id,))
        
        logger.info("prompt_deleted", id=revision_id)
        return {"id": revision_id, "status": "deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to delete prompt: {e}")


class GeneratePromptRequest(BaseModel):
    """Request to generate prompt templates using LLM."""
    product_context: str = "Produk fashion dan lifestyle"
    persona_name: str = "Sari"
    persona_traits: str = "friendly, energetic, knowledgeable"
    language: str = "Indonesian casual"
    provider: str | None = None  # Optional: specify LLM provider


@router.post("/brain/prompts/generate")
async def generate_prompt_templates(request: GeneratePromptRequest) -> dict[str, Any]:
    """Generate prompt templates using LLM based on product context and persona."""
    try:
        router_instance = get_llm_router()
        if router_instance is None:
            raise HTTPException(500, "LLM Router not initialized")
        
        from src.brain.adapters.base import TaskType
        
        # Build generation prompt
        system_prompt = """Kamu adalah AI assistant yang ahli dalam membuat prompt templates untuk live commerce host.
Tugasmu adalah menghasilkan prompt templates yang natural, engaging, dan efektif untuk host live streaming."""
        
        user_prompt = f"""Buatkan prompt templates untuk host live commerce dengan karakteristik berikut:

Nama Host: {request.persona_name}
Kepribadian: {request.persona_traits}
Bahasa: {request.language}
Konteks Produk: {request.product_context}

Hasilkan dalam format JSON dengan struktur berikut:
{{
  "persona": {{
    "name": "{request.persona_name}",
    "personality": "{request.persona_traits}",
    "language": "{request.language}",
    "tone": "...",
    "expertise": "...",
    "catchphrases": ["...", "...", "..."],
    "forbidden_topics": ["politik", "agama", "SARA"]
  }},
  "templates": {{
    "system_base": "...",
    "selling_mode": "...",
    "reacting_mode": "...",
    "engaging_mode": "...",
    "filler": "...",
    "selling_script": "..."
  }}
}}

Pastikan:
1. Catchphrases natural dan sesuai karakter
2. Templates menggunakan placeholder {{variable}} untuk dynamic content
3. Tone konsisten dengan personality
4. Selling script template mencakup 7 fase (HOOK, PROBLEM, SOLUTION, FEATURES, SOCIAL PROOF, URGENCY, CTA)
"""
        
        logger.info("generating_prompt_templates", provider=request.provider or "auto")
        
        response = await asyncio.wait_for(
            router_instance.route(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                task_type=TaskType.SELLING_SCRIPT,
                preferred_provider=request.provider,
            ),
            timeout=60.0,
        )
        
        if not response.success:
            raise HTTPException(500, f"LLM generation failed: {response.error}")
        
        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            text = response.text.strip()
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            generated = json.loads(text)
            
            logger.info(
                "prompt_templates_generated",
                provider=response.provider,
                model=response.model,
                latency_ms=response.latency_ms,
            )
            
            return {
                "success": True,
                "persona": generated.get("persona", {}),
                "templates": generated.get("templates", {}),
                "provider": response.provider,
                "model": response.model,
                "latency_ms": round(response.latency_ms, 1),
            }
        except json.JSONDecodeError as je:
            logger.error("prompt_generation_json_parse_error", error=str(je), text=response.text[:500])
            raise HTTPException(500, f"Failed to parse LLM response as JSON: {je}")
        
    except asyncio.TimeoutError:
        logger.error("prompt_generation_timeout")
        raise HTTPException(504, "Prompt generation timed out after 60 seconds")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_prompt_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to generate prompt: {e}")


# ── Health Endpoints ─────────────────────────────────────────────

@router.get("/health/summary")
async def health_summary() -> dict[str, Any]:
    """Public health summary (no auth required for monitoring)."""
    try:
        hm = get_health_manager()
        results = await asyncio.wait_for(hm.check_all(), timeout=10.0)
        return {
            "status": hm.overall_status,
            "components": {r.name: r.status for r in results},
            "mock_mode": is_mock_mode(),
        }
    except asyncio.TimeoutError:
        logger.error("health_summary_timeout")
        return {"status": "degraded", "components": {}, "error": "Health check timed out", "mock_mode": is_mock_mode()}
    except Exception as e:
        logger.error("health_summary_error", error=str(e), exc_info=True)
        return {"status": "failed", "components": {}, "error": str(e), "mock_mode": is_mock_mode()}


@router.get("/analytics/revenue")
async def revenue_report(hours: int = 1) -> dict[str, Any]:
    """Get revenue analytics."""
    try:
        analytics = get_analytics()
        return analytics.get_revenue_summary(hours * 3600.0)
    except Exception as e:
        logger.error("revenue_report_error", error=str(e), exc_info=True)
        return {"error": str(e), "total": 0.0}


# ── WebSocket ────────────────────────────────────────────────────

_ws_clients: list[WebSocket] = []


@router.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket) -> None:
    """WebSocket for real-time dashboard updates (every 1s)."""
    await websocket.accept()
    _ws_clients.append(websocket)
    logger.info("ws_client_connected", total=len(_ws_clients))

    try:
        import asyncio
        while True:
            analytics = get_analytics()
            snapshot = analytics.get_dashboard_snapshot()
            director = get_show_director().get_runtime_snapshot()
            snapshot["stream_running"] = director["stream_running"]
            snapshot["emergency_stopped"] = director["emergency_stopped"]
            snapshot["mock_mode"] = is_mock_mode()
            snapshot["pipeline_state"] = director["state"]
            snapshot["director"] = director

            pm = _product_manager or ProductManager()
            current = pm.get_current_product()
            snapshot["current_product"] = {
                "name": current.name, "price": current.price_formatted
            } if current else None

            # Add LLM stats if available
            router_instance = get_llm_router()
            if router_instance:
                try:
                    usage = router_instance.get_usage_stats()
                    snapshot["llm_stats"] = usage
                except Exception:
                    pass

            # Add runtime truth fields for realtime dashboard
            try:
                truth = get_runtime_truth_snapshot()
                snapshot["truth"] = truth
            except Exception:
                pass

            await websocket.send_json(snapshot)
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        _ws_clients.remove(websocket)
        logger.info("ws_client_disconnected", total=len(_ws_clients))
    except Exception as e:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)
        logger.error("ws_error", error=str(e))


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket) -> None:
    """WebSocket for real-time chat events."""
    await websocket.accept()
    last_idx = len(_recent_chats)

    try:
        import asyncio
        while True:
            # Send new chats since last check
            if len(_recent_chats) > last_idx:
                new_chats = _recent_chats[last_idx:]
                for chat in new_chats:
                    await websocket.send_json(chat)
                last_idx = len(_recent_chats)
            await asyncio.sleep(0.2)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error("ws_chat_error", error=str(e))


# ── LiveTalking Engine Control Endpoints ───────────────────


def _build_engine_action_result(
    *,
    action: str,
    status: str,
    message: str,
    reason_code: str,
    next_step: str,
    payload: dict[str, Any],
    details: list[str] | None = None,
) -> dict[str, Any]:
    """Attach operator-facing receipt fields without dropping engine payload."""
    return {
        "status": status,
        "action": action,
        "message": message,
        "reason_code": reason_code,
        "details": details or [],
        "next_step": next_step,
        **payload,
    }


def _normalize_probe_url(url: str) -> str:
    """Resolve localhost probe URLs to loopback explicitly for faster local checks."""
    if not url:
        return url

    parts = urlsplit(url)
    if parts.hostname != "localhost":
        return url

    netloc = parts.netloc.replace("localhost", "127.0.0.1", 1)
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


async def _probe_debug_target_async(url: str) -> dict[str, Any]:
    """Probe a preview/debug URL without blocking the event loop."""
    if not url:
        return {
            "url": "",
            "reachable": False,
            "http_status": None,
            "error": "URL tidak tersedia",
        }

    normalized_url = _normalize_probe_url(url)

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(connect=0.35, read=0.85, write=0.35, pool=0.35),
        ) as client:
            response = await client.get(normalized_url)
            reachable = response.status_code < 400
            return {
                "url": url,
                "reachable": reachable,
                "http_status": response.status_code,
                "error": None if reachable else f"HTTP {response.status_code}",
            }
    except httpx.HTTPError as exc:
        return {
            "url": url,
            "reachable": False,
            "http_status": None,
            "error": str(exc),
        }


@router.get("/engine/livetalking/status")
async def engine_livetalking_status() -> dict[str, Any]:
    """Get LiveTalking engine status."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        return mgr.get_status().to_dict()
    except Exception as e:
        logger.error("engine_status_error", error=str(e), exc_info=True)
        return {"state": "error", "last_error": str(e)}


@router.post("/engine/livetalking/start")
async def engine_livetalking_start() -> dict[str, Any]:
    """Start LiveTalking engine."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        status = mgr.start()
        logger.info("engine_livetalking_start_api", state=status.state.value)
        payload = status.to_dict()
        state = payload.get("state", "unknown")
        receipt_status = "success" if state == "running" else "blocked"
        return _build_engine_action_result(
            action="engine.start",
            status=receipt_status,
            message=(
                "Avatar menerima perintah jalan."
                if receipt_status == "success"
                else "Perintah jalan sudah dikirim, tetapi avatar belum melapor berjalan."
            ),
            reason_code="engine_start_requested" if receipt_status == "success" else "engine_start_not_confirmed",
            next_step=(
                "Tunggu status avatar berubah menjadi berjalan."
                if receipt_status == "success"
                else "Periksa tab Teknis atau muat ulang status avatar."
            ),
            payload=payload,
            details=[
                f"state {state}",
                f"transport {payload.get('transport', 'unknown')}",
                f"port {payload.get('port', 'unknown')}",
            ],
        )
    except Exception as e:
        logger.error("engine_start_error", error=str(e), exc_info=True)
        return _build_engine_action_result(
            action="engine.start",
            status="error",
            message="Avatar gagal dijalankan.",
            reason_code="engine_start_failed",
            next_step="Periksa tab Teknis dan log engine sebelum mencoba lagi.",
            payload={"state": "error", "last_error": str(e)},
            details=[str(e)],
        )


@router.post("/engine/livetalking/stop")
async def engine_livetalking_stop() -> dict[str, Any]:
    """Stop LiveTalking engine."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        status = mgr.stop()
        logger.info("engine_livetalking_stop_api", state=status.state.value)
        payload = status.to_dict()
        state = payload.get("state", "unknown")
        receipt_status = "success" if state == "stopped" else "blocked"
        return _build_engine_action_result(
            action="engine.stop",
            status=receipt_status,
            message=(
                "Avatar menerima perintah berhenti."
                if receipt_status == "success"
                else "Perintah berhenti sudah dikirim, tetapi avatar belum melapor berhenti."
            ),
            reason_code="engine_stop_requested" if receipt_status == "success" else "engine_stop_not_confirmed",
            next_step=(
                "Tunggu status avatar berubah menjadi berhenti."
                if receipt_status == "success"
                else "Periksa tab Teknis dan pastikan proses avatar benar-benar berhenti."
            ),
            payload=payload,
            details=[
                f"state {state}",
                f"transport {payload.get('transport', 'unknown')}",
                f"port {payload.get('port', 'unknown')}",
            ],
        )
    except Exception as e:
        logger.error("engine_stop_error", error=str(e), exc_info=True)
        return _build_engine_action_result(
            action="engine.stop",
            status="error",
            message="Avatar gagal dihentikan.",
            reason_code="engine_stop_failed",
            next_step="Periksa tab Teknis dan log engine sebelum mencoba lagi.",
            payload={"state": "error", "last_error": str(e)},
            details=[str(e)],
        )


@router.get("/engine/livetalking/logs")
async def engine_livetalking_logs(tail: int = 100) -> dict[str, Any]:
    """Get LiveTalking engine logs."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        logs = mgr.get_logs(tail=tail)
        return {"lines": logs, "count": len(logs)}
    except Exception as e:
        logger.error("engine_logs_error", error=str(e), exc_info=True)
        return {"lines": [], "count": 0, "error": str(e)}


@router.get("/engine/livetalking/config")
async def engine_livetalking_config() -> dict[str, Any]:
    """Get LiveTalking engine configuration."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        config = mgr.get_config_dict()
        # Add vendor debug URLs
        port = config.get("port", 8010)
        config["debug_urls"] = {
            "webrtcapi": f"http://localhost:{port}/webrtcapi.html",
            "rtcpushapi": f"http://localhost:{port}/rtcpushapi.html",
            "dashboard_vendor": f"http://localhost:{port}/dashboard.html",
            "echoapi": f"http://localhost:{port}/echoapi.html",
        }
        config["operator_dashboard"] = "/dashboard"
        return config
    except Exception as e:
        logger.error("engine_config_error", error=str(e), exc_info=True)
        return {"error": str(e)}


@router.get("/engine/livetalking/debug-targets")
async def engine_livetalking_debug_targets() -> dict[str, Any]:
    """Probe preview/debug URLs so the UI can disable dead links with context."""
    try:
        config = await engine_livetalking_config()
        debug_urls = config.get("debug_urls", {})
        webrtcapi, dashboard_vendor, rtcpushapi = await asyncio.gather(
            _probe_debug_target_async(debug_urls.get("webrtcapi", "")),
            _probe_debug_target_async(debug_urls.get("dashboard_vendor", "")),
            _probe_debug_target_async(debug_urls.get("rtcpushapi", "")),
        )
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "targets": {
                "webrtcapi": webrtcapi,
                "dashboard_vendor": dashboard_vendor,
                "rtcpushapi": rtcpushapi,
            },
        }
    except Exception as e:
        logger.error("engine_debug_targets_error", error=str(e), exc_info=True)
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "targets": {
                "webrtcapi": {"url": "", "reachable": False, "http_status": None, "error": str(e)},
                "dashboard_vendor": {"url": "", "reachable": False, "http_status": None, "error": str(e)},
                "rtcpushapi": {"url": "", "reachable": False, "http_status": None, "error": str(e)},
            },
        }


# ── Readiness Endpoints ────────────────────────────────────

@router.get("/readiness")
async def get_readiness() -> dict[str, Any]:
    """Get consolidated system readiness check."""
    try:
        from src.dashboard.readiness import run_readiness_checks
        result = run_readiness_checks()
        return result.to_dict()
    except Exception as e:
        logger.error("readiness_error", error=str(e), exc_info=True)
        return {
            "overall_status": "error",
            "checks": [],
            "blocking_issues": [str(e)],
            "recommended_next_action": "Fix readiness check error",
        }


# ── Runtime Truth Endpoint ─────────────────────────────────

@router.get("/runtime/truth")
async def get_runtime_truth() -> dict[str, Any]:
    """Get consolidated runtime truth snapshot for operator dashboard."""
    try:
        truth = get_runtime_truth_snapshot(force_refresh=True)
        ops_state = get_ops_state()
        incident_summary = get_incident_registry().summary()
        truth["director"] = get_show_director().get_runtime_snapshot()
        truth["deployment_mode"] = ops_state.deployment_mode
        truth["session_id"] = ops_state.session_id
        truth["host"]["role"] = ops_state.host_role
        truth["incident_summary"] = incident_summary
        return truth
    except Exception as e:
        logger.error("runtime_truth_error", error=str(e), exc_info=True)
        return {
            "mock_mode": is_mock_mode(),
            "error": str(e),
            "timestamp": None,
        }


@router.get("/incidents")
async def get_incidents(limit: int = 50) -> list[dict[str, Any]]:
    """Return recent incidents from the in-process registry."""
    return get_incident_registry().list_recent(limit=limit)


@router.post("/incidents/{incident_id}/ack")
async def acknowledge_incident(incident_id: str) -> dict[str, Any]:
    """Acknowledge an incident in the in-process registry."""
    registry = get_incident_registry()
    registry.acknowledge(incident_id)
    return {
        "status": "success",
        "message": f"Incident {incident_id} acknowledged",
        "incident_id": incident_id,
    }


@router.get("/resources")
async def get_resources() -> dict[str, Any]:
    """Return lightweight server resource metrics."""
    return get_resource_metrics()


@router.get("/ops/summary")
async def get_ops_summary() -> dict[str, Any]:
    """Return top-level ops controller summary."""
    truth = await get_runtime_truth()
    return {
        "overall_status": truth["deployment_mode"],
        "deployment_mode": truth["deployment_mode"],
        "voice_status": truth["voice_runtime_mode"],
        "face_status": truth["face_runtime_mode"],
        "stream_status": truth["stream_runtime_mode"],
        "incident_summary": truth["incident_summary"],
        "resource_metrics": get_resource_metrics(),
        "restart_counters": get_restart_counters(),
    }


# ── Validation Workflow Endpoints ──────────────────────────

@router.post("/validate/mock-stack")
async def validate_mock_stack() -> dict[str, Any]:
    """Validate mock stack is functional."""
    try:
        results: list[dict[str, Any]] = []

        # Check config
        from src.config import get_config, is_mock_mode
        config = get_config()
        results.append({"check": "config", "passed": True, "message": f"{config.app.name}"})
        results.append({"check": "mock_mode", "passed": is_mock_mode(), "message": f"MOCK_MODE={is_mock_mode()}"})

        # Check database
        from src.data.database import check_database_health
        db = check_database_health()
        results.append({"check": "database", "passed": db.get("healthy", False), "message": str(db.get("message", ""))})

        all_pass = all(r["passed"] for r in results)
        return {"status": "pass" if all_pass else "fail", "checks": results}
    except Exception as e:
        logger.error("validate_mock_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/livetalking-engine")
async def validate_livetalking_engine() -> dict[str, Any]:
    """Validate LiveTalking engine readiness."""
    try:
        from src.face.livetalking_manager import get_livetalking_manager
        mgr = get_livetalking_manager()
        status = mgr.get_status()

        checks = [
            {"check": "app_py_exists", "passed": status.app_py_exists, "message": str(mgr.app_py)},
            {"check": "model_path_exists", "passed": status.model_path_exists, "message": str(mgr.models_dir)},
            {"check": "avatar_path_exists", "passed": status.avatar_path_exists, "message": f"{mgr.avatars_dir / mgr.avatar_id}"},
            {"check": "engine_state", "passed": status.state.value in ("running", "stopped"), "message": status.state.value},
        ]
        all_pass = all(c["passed"] for c in checks)
        return {"status": "pass" if all_pass else "fail", "checks": checks}
    except Exception as e:
        logger.error("validate_lt_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/rtmp-target")
async def validate_rtmp_target() -> dict[str, Any]:
    """Validate RTMP target configuration."""
    try:
        checks = []

        ffmpeg_status = check_ffmpeg_ready()
        checks.append({
            "check": "ffmpeg_available",
            "passed": bool(ffmpeg_status["available"]),
            "message": ffmpeg_status["path"] or "not found",
        })

        rtmp_url = os.getenv("TIKTOK_RTMP_URL", "")
        stream_key = os.getenv("TIKTOK_STREAM_KEY", "")
        rtmp_ok = bool(rtmp_url and stream_key)
        checks.append({"check": "rtmp_configured", "passed": rtmp_ok, "message": "configured" if rtmp_ok else "TIKTOK_RTMP_URL or TIKTOK_STREAM_KEY not set"})

        all_pass = all(c["passed"] for c in checks)
        return {"status": "pass" if all_pass else "fail", "checks": checks}
    except Exception as e:
        logger.error("validate_rtmp_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


# ── Validation History Endpoints ─────────────────────────────

@router.get("/validation/history")
async def validation_history(limit: int = 50) -> list[dict[str, Any]]:
    """Get recent validation history entries."""
    return get_validation_history(limit=limit)


@router.post("/validate/runtime-truth")
async def validate_runtime_truth() -> dict[str, Any]:
    """Validate runtime truth snapshot and record evidence."""
    try:
        truth = get_runtime_truth_snapshot()
        checks = [
            {"check": "mock_mode_explicit", "passed": True, "message": f"MOCK_MODE={truth['mock_mode']}"},
            {"check": "face_runtime_mode", "passed": truth["face_runtime_mode"] != "unknown", "message": truth["face_runtime_mode"]},
            {"check": "voice_runtime_mode", "passed": truth["voice_runtime_mode"] != "unknown", "message": truth["voice_runtime_mode"]},
            {"check": "stream_runtime_mode", "passed": truth["stream_runtime_mode"] != "unknown", "message": truth["stream_runtime_mode"]},
            {"check": "provenance_complete", "passed": len(truth.get("provenance", {})) >= 3, "message": f"{len(truth.get('provenance', {}))} surfaces"},
            {"check": "timestamp_present", "passed": truth.get("timestamp") is not None, "message": truth.get("timestamp", "missing")},
        ]
        all_pass = all(c["passed"] for c in checks)
        status = "pass" if all_pass else "fail"
        provenance = "mock" if truth["mock_mode"] else "real_local"
        entry = record_validation("runtime-truth", status, checks, provenance=provenance)
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_truth_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/real-mode-readiness")
async def validate_real_mode_readiness() -> dict[str, Any]:
    """Check if system is ready for real-mode (MOCK_MODE=false) operation."""
    try:
        checks: list[dict[str, Any]] = []

        # 1. MOCK_MODE must be false
        mock = is_mock_mode()
        checks.append({"check": "mock_mode_off", "passed": not mock, "message": f"MOCK_MODE={'true' if mock else 'false'}"})

        # 2. Avatar reference assets (video + audio)
        from pathlib import Path
        ref_video = Path("assets/avatar/reference.mp4")
        ref_audio = Path("assets/avatar/reference.wav")
        checks.append({"check": "avatar_reference_video", "passed": ref_video.exists(), "message": str(ref_video)})
        checks.append({"check": "avatar_reference_audio", "passed": ref_audio.exists(), "message": str(ref_audio) if ref_audio.exists() else "reference.wav missing (run: ffmpeg -i reference.mp4 -vn -ar 16000 -ac 1 reference.wav)"})

        # 3. RTMP target configured
        rtmp_url = os.getenv("TIKTOK_RTMP_URL", "")
        stream_key = os.getenv("TIKTOK_STREAM_KEY", "")
        rtmp_ok = bool(rtmp_url and stream_key)
        checks.append({"check": "rtmp_configured", "passed": rtmp_ok, "message": "configured" if rtmp_ok else "not set"})

        # 4. LiveTalking runtime path resolved
        lt_path = Path("external/livetalking/app.py")
        checks.append({"check": "livetalking_entrypoint", "passed": lt_path.exists(), "message": str(lt_path)})

        # 5. Product data source exists (canonical file check — same as CLI readiness)
        from pathlib import Path as _Path
        p_json = _Path("data/products.json")
        p_db = _Path("data/products.db")
        found_products = [p.name for p in (p_json, p_db) if p.exists()]
        products_file_ok = len(found_products) > 0
        checks.append({
            "check": "product_data_source",
            "passed": products_file_ok,
            "message": f"Found: {', '.join(found_products)}" if found_products else "Neither products.json nor products.db found",
        })

        # 5b. Products hydrated into runtime manager
        pm = _product_manager or ProductManager()
        products = pm.get_all_active()
        checks.append({"check": "products_loaded", "passed": len(products) > 0, "message": f"{len(products)} products"})

        # 6. FFmpeg available
        ffmpeg_status = check_ffmpeg_ready()
        checks.append({"check": "ffmpeg_available", "passed": bool(ffmpeg_status["available"]), "message": ffmpeg_status["path"] or "not found"})

        all_pass = all(c["passed"] for c in checks)
        blockers = [c["check"] for c in checks if not c["passed"]]
        status = "pass" if all_pass else "blocked"
        entry = record_validation("real-mode-readiness", status, checks, provenance="real_local", context=f"blockers: {blockers}")
        return {"status": status, "checks": checks, "blockers": blockers, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_real_mode_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/voice/warmup")
async def voice_warmup() -> dict[str, Any]:
    """Warm the voice subsystem and return an explicit operator receipt."""
    try:
        state = get_runtime_truth_snapshot()["voice_engine"]
        if not state.get("server_reachable", False):
            return {
                "status": "blocked",
                "message": "Voice sidecar is not reachable yet",
                "provenance": "mock" if is_mock_mode() else "real_local",
                "action": "voice.warmup",
            }
        return {
            "status": "success",
            "message": "Voice sidecar is reachable and ready for warmup",
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.warmup",
        }
    except Exception as e:
        logger.error("voice_warmup_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.warmup",
        }


@router.post("/voice/queue/clear")
async def voice_queue_clear() -> dict[str, Any]:
    """Clear in-memory voice queue counters."""
    try:
        from src.voice.runtime_state import get_voice_runtime_state
        state = get_voice_runtime_state()
        state.queue_depth = 0
        return {
            "status": "success",
            "message": "Voice queue cleared",
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.queue.clear",
        }
    except Exception as e:
        logger.error("voice_queue_clear_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.queue.clear",
        }


@router.post("/voice/restart")
async def voice_restart() -> dict[str, Any]:
    """Increment voice restart counter and return a receipt."""
    try:
        from src.dashboard.resources import increment_restart_counter
        increment_restart_counter("voice")
        return {
            "status": "success",
            "message": "Voice worker restart requested",
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.restart",
        }
    except Exception as e:
        logger.error("voice_restart_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.restart",
        }


@router.post("/voice/test/speak")
async def voice_test_speak(text: str = "Halo operator, tes suara") -> dict[str, Any]:
    """Test voice synthesis with custom text and return an explicit operator receipt.

    This endpoint allows operators to test voice synthesis with custom text
    directly from the dashboard without triggering a full pipeline transition.
    """
    try:
        from src.voice.engine import FishSpeechEngine

        engine = FishSpeechEngine()

        if not await engine.health_check():
            return {
                "status": "blocked",
                "message": "Voice sidecar is not reachable yet",
                "provenance": "mock" if is_mock_mode() else "real_local",
                "action": "voice.test.speak",
                "text": text,
            }

        result = await engine.synthesize(text, emotion="neutral")
        audio_data = result.audio_data

        if audio_data:
            return {
                "status": "success",
                "message": f"Synthesized {len(text)} characters successfully",
                "provenance": "mock" if is_mock_mode() else "real_local",
                "action": "voice.test.speak",
                "text": text,
                "audio_length_bytes": len(audio_data),
                "latency_ms": result.latency_ms,
                "duration_ms": result.duration_ms,
            }
        else:
            return {
                "status": "error",
                "message": "Synthesis returned empty audio",
                "provenance": "mock" if is_mock_mode() else "real_local",
                "action": "voice.test.speak",
                "text": text,
            }
    except Exception as e:
        logger.error("voice_test_speak_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "provenance": "mock" if is_mock_mode() else "real_local",
            "action": "voice.test.speak",
            "text": text,
        }


@router.post("/validate/voice-local-clone")
async def validate_voice_local_clone() -> dict[str, Any]:
    """Validate local Fish-Speech voice clone readiness and run synthesis smoke test.

    Checks:
    1. Voice clone reference WAV exists
    2. Voice clone reference text exists and is non-empty
    3. Fish-Speech sidecar is reachable
    4. Indonesian synthesis smoke test succeeds (if sidecar available)
    """
    import time as _time
    from pathlib import Path

    try:
        config = get_config()
        checks: list[dict[str, Any]] = []

        # 1. Reference WAV
        ref_wav = Path(config.voice.clone_reference_wav)
        wav_ok = ref_wav.exists()
        checks.append({"check": "voice_reference_wav", "passed": wav_ok, "message": str(ref_wav) if wav_ok else f"not found: {ref_wav}"})

        # 2. Reference text
        ref_txt = Path(config.voice.clone_reference_text)
        txt_ok = ref_txt.exists()
        txt_nonempty = False
        if txt_ok:
            txt_nonempty = len(ref_txt.read_text(encoding="utf-8").strip()) > 0
        checks.append({
            "check": "voice_reference_text",
            "passed": txt_ok and txt_nonempty,
            "message": str(ref_txt) if (txt_ok and txt_nonempty) else f"missing or empty: {ref_txt}",
        })

        # 3. Fish-Speech server reachable
        from src.voice.fish_speech_client import FishSpeechClient
        client = FishSpeechClient(
            base_url=config.voice.fish_speech_base_url,
            timeout_ms=config.voice.fish_speech_timeout_ms,
        )
        server_reachable = await client.health_check()
        checks.append({
            "check": "fish_speech_server_reachable",
            "passed": server_reachable,
            "message": f"reachable at {config.voice.fish_speech_base_url}" if server_reachable else f"not reachable at {config.voice.fish_speech_base_url}",
        })

        # 4. Indonesian synthesis smoke test
        synthesis_ok = False
        latency_ms = 0.0
        synthesis_message = "skipped (prerequisites not met)"
        if wav_ok and txt_nonempty and server_reachable:
            try:
                ref_audio_b64 = FishSpeechClient.load_reference_audio_b64(config.voice.clone_reference_wav)
                ref_text = FishSpeechClient.load_reference_text(config.voice.clone_reference_text)
                smoke_text = config.voice.indonesian_smoke_text

                start = _time.time()
                audio_bytes = await client.synthesize(
                    text=smoke_text,
                    reference_audio_b64=ref_audio_b64,
                    reference_text=ref_text,
                )
                latency_ms = (_time.time() - start) * 1000
                synthesis_ok = len(audio_bytes) > 0
                synthesis_message = f"synthesized {len(audio_bytes)} bytes in {latency_ms:.0f}ms"

                # Update voice runtime state
                from src.voice.runtime_state import get_voice_runtime_state
                state = get_voice_runtime_state()
                state.update_success("fish_speech", latency_ms)
                state.server_reachable = True
                state.reference_ready = True
            except Exception as synth_err:
                synthesis_message = f"synthesis failed: {synth_err}"

        checks.append({
            "check": "indonesian_synthesis_smoke",
            "passed": synthesis_ok,
            "message": synthesis_message,
        })

        all_pass = all(c["passed"] for c in checks)
        if not (wav_ok and txt_nonempty):
            status = "blocked"
        elif all_pass:
            status = "pass"
        else:
            status = "fail"

        provenance = "mock" if is_mock_mode() else "real_local"
        entry = record_validation("voice-local-clone", status, checks, provenance=provenance)
        return {"status": status, "checks": checks, "evidence_id": entry["id"], "latency_ms": latency_ms}
    except Exception as e:
        logger.error("validate_voice_clone_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/audio-chunking-smoke")
async def validate_audio_chunking_smoke() -> dict[str, Any]:
    """Validate that voice chunking controls are configured for ops mode."""
    try:
        from src.voice.runtime_state import get_voice_runtime_state

        state = get_voice_runtime_state()
        checks = [
            {
                "check": "voice_engine_selected",
                "passed": state.requested_engine != "unknown",
                "message": state.requested_engine,
            },
            {
                "check": "chunk_chars_configured",
                "passed": state.chunk_chars is not None,
                "message": str(state.chunk_chars) if state.chunk_chars is not None else "chunk size not configured",
            },
        ]
        status = "pass" if all(check["passed"] for check in checks) else "blocked"
        entry = record_validation("audio-chunking-smoke", status, checks, provenance="mock" if is_mock_mode() else "real_local")
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_audio_chunking_smoke_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/stream-dry-run")
async def validate_stream_dry_run() -> dict[str, Any]:
    """Validate minimum dry-run stream prerequisites."""
    try:
        checks = [
            {"check": "ffmpeg_available", "passed": bool(check_ffmpeg_ready()["available"]), "message": check_ffmpeg_ready()["path"] or "not found"},
            {"check": "stream_idle_or_live_known", "passed": get_runtime_truth_snapshot()["stream_runtime_mode"] in {"mock", "idle", "live"}, "message": get_runtime_truth_snapshot()["stream_runtime_mode"]},
        ]
        status = "pass" if all(check["passed"] for check in checks) else "fail"
        entry = record_validation("stream-dry-run", status, checks, provenance="mock" if is_mock_mode() else "real_local")
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_stream_dry_run_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/resource-budget")
async def validate_resource_budget() -> dict[str, Any]:
    """Validate lightweight resource budget placeholders."""
    try:
        metrics = get_resource_metrics()
        checks = [
            {"check": "cpu_metric_present", "passed": "cpu_pct" in metrics, "message": str(metrics.get("cpu_pct"))},
            {"check": "ram_metric_present", "passed": "ram_pct" in metrics, "message": str(metrics.get("ram_pct"))},
            {"check": "disk_metric_present", "passed": "disk_pct" in metrics, "message": str(metrics.get("disk_pct"))},
        ]
        status = "pass" if all(check["passed"] for check in checks) else "fail"
        entry = record_validation("resource-budget", status, checks, provenance="mock" if is_mock_mode() else "real_local")
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_resource_budget_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/soak-sanity")
async def validate_soak_sanity() -> dict[str, Any]:
    """Validate minimal long-run sanity indicators for the ops controller."""
    try:
        summary = get_incident_registry().summary()
        restarts = get_restart_counters()
        checks = [
            {"check": "incident_summary_present", "passed": "open_count" in summary, "message": str(summary)},
            {"check": "restart_counters_present", "passed": "voice" in restarts, "message": str(restarts)},
        ]
        status = "pass" if all(check["passed"] for check in checks) else "fail"
        entry = record_validation("soak-sanity", status, checks, provenance="mock" if is_mock_mode() else "real_local")
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_soak_sanity_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/face-sync-smoke")
async def validate_face_sync_smoke() -> dict[str, Any]:
    """Validate minimum face runtime truth presence for ops controller."""
    try:
        truth = get_runtime_truth_snapshot()
        checks = [
            {"check": "face_runtime_known", "passed": truth["face_runtime_mode"] != "unknown", "message": truth["face_runtime_mode"]},
            {"check": "face_engine_present", "passed": "face_engine" in truth, "message": "present"},
        ]
        status = "pass" if all(check["passed"] for check in checks) else "fail"
        entry = record_validation("face-sync-smoke", status, checks, provenance="mock" if is_mock_mode() else "real_local")
        return {"status": status, "checks": checks, "evidence_id": entry["id"]}
    except Exception as e:
        logger.error("validate_face_sync_smoke_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}


@router.post("/validate/rtmp-target")
async def validate_rtmp_target() -> dict[str, Any]:
    """Validate RTMP target configuration."""
    try:
        checks = []

        ffmpeg_status = check_ffmpeg_ready()
        checks.append({
            "check": "ffmpeg_available",
            "passed": bool(ffmpeg_status["available"]),
            "message": ffmpeg_status["path"] or "not found",
        })

        rtmp_url = os.getenv("TIKTOK_RTMP_URL", "")
        stream_key = os.getenv("TIKTOK_STREAM_KEY", "")
        rtmp_ok = bool(rtmp_url and stream_key)
        checks.append({"check": "rtmp_configured", "passed": rtmp_ok, "message": "configured" if rtmp_ok else "TIKTOK_RTMP_URL or TIKTOK_STREAM_KEY not set"})

        all_pass = all(c["passed"] for c in checks)
        return {"status": "pass" if all_pass else "fail", "checks": checks}
    except Exception as e:
        logger.error("validate_rtmp_error", error=str(e), exc_info=True)
        return {"status": "error", "checks": [], "error": str(e)}

