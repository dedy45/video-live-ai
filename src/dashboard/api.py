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
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.brain.prompt_registry import get_prompt_registry
from src.brain.runtime_config import get_brain_runtime_config
from src.commerce.analytics import get_analytics
from src.commerce.manager import AffiliateTracker, Product, ProductManager
from src.config import get_config, get_env, is_mock_mode
from src.control_plane import ControlPlaneStore
from src.utils.health import get_health_manager
from src.dashboard.incidents import get_incident_registry
from src.dashboard.ops_state import get_ops_state
from src.dashboard.resources import get_resource_metrics, get_restart_counters
from src.dashboard.truth import get_runtime_truth_snapshot
from src.dashboard.validation_history import record_validation, get_history as get_validation_history
from src.orchestrator.show_director import get_show_director
from src.stream import SingleHostStreamRuntime
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


class ChatIngestRequest(BaseModel):
    platform: str
    username: str
    message: str
    trace_id: str = ""
    raw_data: dict[str, Any] = {}


class ProductMutationRequest(BaseModel):
    name: str
    price: float
    category: str = "general"
    stock: int = 0
    margin_percent: float = 0.0
    description: str = ""
    image_path: str = ""
    affiliate_links: dict[str, str] = {}
    selling_points: list[str] = []
    commission_rate: float = 0.0
    objection_handling: dict[str, str] = {}
    compliance_notes: str = ""


class StreamTargetMutationRequest(BaseModel):
    platform: str
    label: str
    rtmp_url: str
    stream_key: str
    enabled: bool = True


class LiveSessionStartRequest(BaseModel):
    platform: str = "tiktok"


class SessionProductsRequest(BaseModel):
    product_ids: list[int]


class FocusProductRequest(BaseModel):
    session_product_id: int


class LiveSessionPauseRequest(BaseModel):
    reason: str
    question: str | None = None


class VoiceProfileMutationRequest(BaseModel):
    name: str
    reference_wav_path: str
    reference_text: str
    language: str = "id"
    supported_languages: list[str] = ["id"]
    profile_type: str = "quick_clone"
    quality_tier: str = "quick"
    guidance: dict[str, Any] = {}
    notes: str = ""
    engine: str = "fish_speech"


class VoiceLabStateRequest(BaseModel):
    mode: str = "standalone"
    active_profile_id: int | None = None
    preview_session_id: str = ""
    selected_avatar_id: str = ""
    selected_language: str = "id"
    selected_profile_type: str = "quick_clone"
    selected_revision_id: int | None = None
    selected_style_preset: str = "natural"
    selected_stability: float = 0.75
    selected_similarity: float = 0.8
    draft_text: str = ""
    last_generation_id: int | None = None


class VoiceGenerationRequest(BaseModel):
    mode: str = "standalone"
    profile_id: int | None = None
    text: str
    language: str = "id"
    emotion: str = "neutral"
    style_preset: str = "natural"
    stability: float = 0.75
    similarity: float = 0.8
    speed: float = 1.0
    attach_to_avatar: bool = False
    avatar_id: str = ""
    preview_session_id: str = ""
    source_type: str = "manual_text"


class VoiceTrainingJobRequest(BaseModel):
    profile_id: int
    job_type: str = "studio_voice_training"
    dataset_path: str = ""


class BrainTestRequest(BaseModel):
    """Request to test LLM Brain with a prompt."""
    system_prompt: str = ""
    user_prompt: str = "Halo, perkenalkan produk ini!"
    task_type: str = "chat_reply"
    provider: str | None = None
    viewer_name: str = ""
    viewer_message: str = ""
    question: str = ""
    product_context: str = ""
    candidate_text: str = ""
    additional_context: str = ""


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
_control_plane_store: ControlPlaneStore | None = None
_stream_runtime_service: SingleHostStreamRuntime | None = None
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
VOICE_RUNTIME_DIR = Path("data/runtime/voice")


def init_dashboard_state(
    product_manager: ProductManager | None = None,
    affiliate_tracker: AffiliateTracker | None = None,
) -> None:
    """Initialize dashboard shared state from main app."""
    global _product_manager, _affiliate_tracker
    _product_manager = product_manager or ProductManager()
    _affiliate_tracker = affiliate_tracker or AffiliateTracker()
    try:
        store = get_control_plane_store()
        seeded = store.seed_products_from_json_if_empty(ProductManager.CANONICAL_PRODUCTS_PATH)
        if seeded == 0 and _product_manager is not None:
            store.seed_products_if_empty(
                [
                    {
                        "name": product.name,
                        "price": product.price,
                        "category": product.category,
                        "stock": product.stock,
                        "margin_percent": product.margin_percent,
                        "description": product.description,
                        "image_path": product.image_path,
                        "affiliate_links": product.affiliate_links,
                        "selling_points": product.selling_points or product.features,
                        "commission_rate": product.commission_rate,
                        "objection_handling": product.objection_handling,
                        "compliance_notes": product.compliance_notes,
                    }
                    for product in _product_manager.get_all_active()
                ]
            )
    except Exception as e:
        logger.warning("control_plane_seed_failed", error=str(e), exc_info=True)


def get_control_plane_store() -> ControlPlaneStore:
    """Get or create the dashboard control-plane store."""
    global _control_plane_store
    if _control_plane_store is None:
        _control_plane_store = ControlPlaneStore()
    return _control_plane_store


def get_stream_runtime_service() -> SingleHostStreamRuntime:
    """Get or create the single-host stream runtime controller."""
    global _stream_runtime_service
    if _stream_runtime_service is None:
        _stream_runtime_service = SingleHostStreamRuntime()
    return _stream_runtime_service


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


def _serialize_chat_event(event: Any) -> dict[str, Any]:
    return {
        "platform": event.platform,
        "username": event.username,
        "message": event.message,
        "intent": event.intent,
        "priority": int(event.priority),
        "trace_id": event.trace_id,
        "timestamp": float(event.timestamp),
        "raw_data": event.raw_data,
    }


def _task_type_names() -> list[str]:
    from src.brain.adapters.base import TaskType

    return [task.value for task in TaskType]


def _get_router_adapters(router_instance: Any | None) -> dict[str, Any]:
    adapters = getattr(router_instance, "adapters", {}) if router_instance is not None else {}
    if not isinstance(adapters, dict):
        return {}
    return adapters


def _build_brain_provider_payload(router_instance: Any | None) -> dict[str, dict[str, Any]]:
    providers: dict[str, dict[str, Any]] = {}
    adapters = _get_router_adapters(router_instance)
    if not adapters:
        return providers

    for provider_name in sorted(adapters.keys()):
        adapter = adapters[provider_name]
        payload = {
            "model": getattr(adapter, "_litellm_model", getattr(adapter, "model", "unknown")),
            "timeout_ms": int(getattr(adapter, "timeout_ms", 0)),
            "backend": "litellm",
        }
        api_base = getattr(adapter, "_api_base", "")
        if api_base:
            payload["api_base"] = api_base
        providers[provider_name] = payload
    return providers


def _build_brain_config_payload(router_instance: Any | None = None) -> dict[str, Any]:
    runtime = get_brain_runtime_config().snapshot(router_instance)
    prompt = get_prompt_registry().get_active_revision()
    providers = _build_brain_provider_payload(router_instance)

    return {
        "daily_budget_usd": runtime["daily_budget_usd"],
        "fallback_order": runtime["fallback_order"],
        "routing_table": runtime["routing_table"],
        "available_providers": runtime["available_providers"],
        "edit_mode": runtime["edit_mode"],
        "persists_across_restart": runtime["persists_across_restart"],
        "prompt": {
            "active_revision": f'{prompt["slug"]}:v{prompt["version"]}',
            "slug": prompt["slug"],
            "version": prompt["version"],
            "status": prompt["status"],
            "updated_at": prompt["updated_at"],
        },
        "providers": providers,
        "task_types": _task_type_names(),
    }


def _get_voice_runtime_dir() -> Path:
    VOICE_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    return VOICE_RUNTIME_DIR


def _get_voice_audio_path() -> Path:
    timestamp_ms = int(time.time() * 1000)
    return _get_voice_runtime_dir() / f"voice-{timestamp_ms}.wav"


def _ensure_default_voice_profile() -> None:
    store = get_control_plane_store()
    if store.list_voice_profiles():
        return
    config = get_config()
    ref_wav = Path(config.voice.clone_reference_wav)
    ref_txt = Path(config.voice.clone_reference_text)
    if not ref_wav.exists() or not ref_txt.exists():
        return
    ref_text = ref_txt.read_text(encoding="utf-8").strip()
    if not ref_text:
        return
    profile = store.create_voice_profile(
        name="Default Fish Clone",
        reference_wav_path=str(ref_wav),
        reference_text=ref_text,
        language="id",
        supported_languages=["id"],
        profile_type="quick_clone",
        quality_tier="quick",
        notes="Seeded from config.voice clone reference",
    )
    store.activate_voice_profile(profile["id"])


def get_voice_lab_engine():
    from src.voice.lab import get_voice_lab_engine as _get_engine

    return _get_engine()


async def _attach_audio_to_livetalking(*, audio_path: Path, session_id: str) -> None:
    from src.face.livetalking_manager import get_livetalking_manager

    manager = get_livetalking_manager()
    status = manager.get_status()
    if status.state.value != "running":
        raise HTTPException(status_code=409, detail="Avatar is not running for attach mode")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            with audio_path.open("rb") as audio_file:
                response = await client.post(
                    f"http://127.0.0.1:{status.port}/humanaudio",
                    data={"sessionid": session_id},
                    files={"file": (audio_path.name, audio_file, "audio/wav")},
                )
        if response.status_code >= 400:
            raise HTTPException(
                status_code=502,
                detail=f"Avatar attach failed: {response.status_code}",
            )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Avatar attach failed: {exc}") from exc


def _sync_show_director_with_live_session(active_live: dict[str, Any] | None = None) -> dict[str, Any]:
    """Align the operator-facing director state with SQLite control-plane truth."""
    director = get_show_director()
    snapshot = director.get_runtime_snapshot()
    if snapshot["emergency_stopped"]:
        return snapshot

    try:
        live = active_live if active_live is not None else get_control_plane_store().get_active_live_session()
    except Exception:
        return snapshot

    session = (live or {}).get("session")
    state = (live or {}).get("state") or {}
    if session is None:
        if snapshot["stream_running"]:
            snapshot = director.stop_stream()
        if snapshot["state"] != "IDLE" and "IDLE" in director.get_valid_transitions():
            snapshot = director.transition("IDLE")
        return snapshot

    if not snapshot["stream_running"]:
        snapshot = director.start_stream()

    desired_state = "PAUSED" if bool(state.get("rotation_paused")) else "SELLING"
    if snapshot["state"] != desired_state and desired_state in director.get_valid_transitions():
        snapshot = director.transition(desired_state)
    return snapshot


def _get_director_runtime_contract() -> dict[str, Any]:
    """Build the aggregated director + brain + prompt runtime contract."""
    director = _sync_show_director_with_live_session()
    prompt = get_prompt_registry().get_active_revision()
    router_instance = get_llm_router()
    runtime = get_brain_runtime_config().snapshot(router_instance)
    adapter_count = len(_get_router_adapters(router_instance))

    return {
        "director": director,
        "brain": {
            "active_provider": director["active_provider"],
            "active_model": director["active_model"],
            "routing_table": runtime["routing_table"],
            "adapter_count": adapter_count,
            "daily_budget_usd": runtime["daily_budget_usd"],
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
        control = get_control_plane_store()
        gauges = analytics.get_gauges()
        counters = analytics.get_counters()
        director = _sync_show_director_with_live_session()
        stream_runtime = get_stream_runtime_service().get_snapshot()
        active_live = control.get_active_live_session()
        current = None
        stream_running = bool(stream_runtime.get("stream_running") or director["stream_running"])
        stream_status = (
            "stopped"
            if director["emergency_stopped"]
            else (stream_runtime.get("stream_status") or ("live" if director["stream_running"] else "idle"))
        )

        if active_live["session"] is not None:
            state = active_live["state"] or {}
            stream_running = bool(stream_runtime.get("stream_running") or director["stream_running"])
            stream_status = state.get("stream_status") or stream_status or "ready"
            focus_product_id = state.get("current_focus_product_id")
            if focus_product_id:
                current = control.get_product(int(focus_product_id))
            elif active_live["products"]:
                current = active_live["products"][0]["product"]

        if current is None:
            pm = _product_manager or ProductManager()
            current_product = pm.get_current_product()
            if current_product is not None:
                current = {
                    "id": current_product.id,
                    "name": current_product.name,
                    "price": current_product.price,
                    "price_formatted": current_product.price_formatted,
                }

        return {
            "state": director["state"],
            "mock_mode": is_mock_mode(),
            "uptime_sec": round(time.time() - _system_start_time, 0),
            "viewer_count": int(gauges.get("viewers", 0)),
            "current_product": {
                "id": current["id"],
                "name": current["name"],
                "price": current.get("price_formatted", current.get("price")),
            } if current else None,
            "stream_status": stream_status,
            "stream_running": stream_running,
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
        return get_control_plane_store().list_products()
    except Exception as e:
        logger.error("list_products_error", error=str(e), exc_info=True)
        return []


@router.post("/products")
async def create_product(payload: ProductMutationRequest) -> dict[str, Any]:
    """Create a product in the SQLite-backed control plane."""
    try:
        return get_control_plane_store().create_product(**payload.model_dump())
    except Exception as e:
        logger.error("create_product_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to create product: {e}") from e


@router.put("/products/{product_id}")
async def update_product(product_id: int, payload: ProductMutationRequest) -> dict[str, Any]:
    """Update a product in the SQLite-backed control plane."""
    try:
        return get_control_plane_store().update_product(product_id, **payload.model_dump())
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("update_product_error", product_id=product_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to update product: {e}") from e


@router.delete("/products/{product_id}")
async def delete_product(product_id: int) -> dict[str, Any]:
    """Soft-delete a product from the control plane."""
    try:
        return get_control_plane_store().delete_product(product_id)
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("delete_product_error", product_id=product_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to delete product: {e}") from e


@router.post("/products/{product_id}/switch")
async def switch_product(product_id: int) -> dict[str, Any]:
    """Manually switch to a specific product."""
    try:
        control = get_control_plane_store()
        active_live = control.get_active_live_session()
        if active_live["session"] is not None:
            session_product = next(
                (
                    item for item in active_live["products"]
                    if int(item["product_id"]) == product_id
                ),
                None,
            )
            if session_product is None:
                raise HTTPException(404, f"Product {product_id} not assigned to active session")
            state = control.set_focus_product(
                session_id=int(active_live["session"]["id"]),
                session_product_id=int(session_product["id"]),
                reason="operator_switch",
            )
            return {
                "status": "switched",
                "product": session_product["product"]["name"],
                "state": state,
            }

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

@router.post("/chat/ingest")
async def ingest_chat_event(payload: ChatIngestRequest) -> dict[str, Any]:
    """Ingest a chat event into dashboard truth and auto-pause live session when needed."""
    try:
        from src.chat.monitor import ChatEvent, EventPriority, IntentDetector

        detector = IntentDetector()
        priority, intent = detector.detect(payload.message)
        event = ChatEvent(
            platform=payload.platform,
            username=payload.username,
            message=payload.message,
            priority=priority,
            intent=intent,
            raw_data=payload.raw_data,
            trace_id=payload.trace_id,
        )
        serialized = _serialize_chat_event(event)
        record_chat_event(serialized)

        auto_paused = False
        state: dict[str, Any] | None = None
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is not None and event.priority <= EventPriority.P2_QUESTION:
            state = store.pause_rotation(
                session_id=int(active["session"]["id"]),
                reason="viewer_question",
                question=event.message,
            )
            pending_question = await _generate_affiliate_answer_draft(
                question=event.message,
                reason="viewer_question",
                active_session=store.get_active_live_session(),
            )
            pending_question["viewer_name"] = event.username
            pending_question["source_platform"] = event.platform
            state = store.update_pending_question(
                session_id=int(active["session"]["id"]),
                pending_question=pending_question,
            )
            _sync_show_director_with_live_session(store.get_active_live_session())
            auto_paused = True

        return {
            "status": "recorded",
            "event": serialized,
            "auto_paused": auto_paused,
            "state": state,
        }
    except Exception as e:
        logger.error("ingest_chat_event_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to ingest chat event: {e}") from e


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


def _build_target_validation_checks(target: dict[str, Any]) -> list[dict[str, Any]]:
    ffmpeg_status = check_ffmpeg_ready()
    checks = [
        {
            "check": "ffmpeg_available",
            "passed": bool(ffmpeg_status["available"]),
            "message": ffmpeg_status["path"] or "not found",
        },
        {
            "check": "platform_supported",
            "passed": target["platform"] in {"tiktok", "shopee"},
            "message": target["platform"],
        },
        {
            "check": "rtmp_url_present",
            "passed": bool(target["rtmp_url"]),
            "message": target["rtmp_url"] or "missing",
        },
        {
            "check": "rtmp_url_scheme",
            "passed": str(target["rtmp_url"]).startswith("rtmp://"),
            "message": target["rtmp_url"],
        },
        {
            "check": "stream_key_present",
            "passed": bool(target.get("stream_key")),
            "message": "configured" if target.get("stream_key") else "missing",
        },
    ]
    return checks


# ── Stream Target + Live Session Endpoints ──────────────────────

@router.get("/stream-targets")
async def list_stream_targets() -> list[dict[str, Any]]:
    """List dashboard-managed stream targets."""
    try:
        return get_control_plane_store().list_stream_targets()
    except Exception as e:
        logger.error("list_stream_targets_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to list stream targets: {e}") from e


@router.post("/stream-targets")
async def create_stream_target(payload: StreamTargetMutationRequest) -> dict[str, Any]:
    """Create a new RTMP target."""
    try:
        return get_control_plane_store().create_stream_target(**payload.model_dump())
    except Exception as e:
        logger.error("create_stream_target_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to create stream target: {e}") from e


@router.put("/stream-targets/{target_id}")
async def update_stream_target(target_id: int, payload: StreamTargetMutationRequest) -> dict[str, Any]:
    """Update an RTMP target."""
    try:
        return get_control_plane_store().update_stream_target(target_id, **payload.model_dump())
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("update_stream_target_error", target_id=target_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to update stream target: {e}") from e


@router.post("/stream-targets/{target_id}/validate")
async def validate_stream_target(target_id: int) -> dict[str, Any]:
    """Validate a persisted stream target."""
    try:
        store = get_control_plane_store()
        target = store.get_stream_target_secret(target_id)
        if target is None:
            raise HTTPException(404, f"Stream target {target_id} not found")
        checks = _build_target_validation_checks(target)
        status = "pass" if all(check["passed"] for check in checks) else "fail"
        persisted = store.save_stream_target_validation(target_id, status=status, checks=checks)
        return {"status": status, "checks": checks, "target": persisted}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("validate_stream_target_error", target_id=target_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to validate stream target: {e}") from e


@router.post("/stream-targets/{target_id}/activate")
async def activate_stream_target(target_id: int) -> dict[str, Any]:
    """Activate one stream target as the current dashboard RTMP destination."""
    try:
        target = get_control_plane_store().activate_stream_target(target_id)
        return {"status": "activated", "target": target}
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("activate_stream_target_error", target_id=target_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to activate stream target: {e}") from e


@router.get("/live-session")
async def get_live_session() -> dict[str, Any]:
    """Get the single active live session summary."""
    try:
        return get_control_plane_store().get_active_live_session()
    except Exception as e:
        logger.error("get_live_session_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to read live session: {e}") from e


@router.post("/live-session/start")
async def start_live_session(payload: LiveSessionStartRequest) -> dict[str, Any]:
    """Start the single active live session using the active RTMP target for the platform."""
    try:
        store = get_control_plane_store()
        if store.get_active_live_session()["session"] is not None:
            raise HTTPException(409, "There is already an active live session")
        target = store.get_active_stream_target(payload.platform)
        if target is None:
            raise HTTPException(400, f"No active {payload.platform} stream target configured")
        secret_target = store.get_stream_target_secret(int(target["id"]))
        if secret_target is None:
            raise HTTPException(404, f"Active stream target {target['id']} could not be loaded")

        runtime = get_stream_runtime_service()
        try:
            runtime_state = await runtime.start_target(secret_target)
        except RuntimeError as e:
            raise HTTPException(502, str(e)) from e

        director = get_show_director()
        try:
            director.start_stream()
            session = store.start_live_session(platform=payload.platform, stream_target_id=int(target["id"]))
            stream_status = str(runtime_state.get("stream_status") or runtime_state.get("status") or "live")
            state = store.set_session_stream_status(session_id=int(session["id"]), stream_status=stream_status)
            _sync_show_director_with_live_session(store.get_active_live_session())
            return {"status": "started", "session": session, "stream_target": target, "state": state}
        except RuntimeError as e:
            await runtime.stop_active()
            if director.get_runtime_snapshot()["stream_running"]:
                director.stop_stream()
            raise HTTPException(409, str(e)) from e
        except Exception:
            await runtime.stop_active()
            if director.get_runtime_snapshot()["stream_running"]:
                director.stop_stream()
            raise
    except HTTPException:
        raise
    except Exception as e:
        logger.error("start_live_session_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to start live session: {e}") from e


@router.post("/live-session/stop")
async def stop_live_session() -> dict[str, Any]:
    """Stop the current live session."""
    try:
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is None:
            raise HTTPException(409, "No active live session")

        runtime_errors: list[str] = []
        runtime = get_stream_runtime_service()
        try:
            await runtime.stop_active()
        except Exception as e:
            runtime_errors.append(f"stream_runtime: {e}")

        director = get_show_director()
        try:
            if director.get_runtime_snapshot()["stream_running"]:
                director.stop_stream()
        except Exception as e:
            runtime_errors.append(f"show_director: {e}")

        result = store.stop_live_session()
        _sync_show_director_with_live_session(store.get_active_live_session())
        if runtime_errors:
            return {"status": "degraded", **result, "errors": runtime_errors}
        return {"status": "stopped", **result}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e
    except Exception as e:
        logger.error("stop_live_session_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to stop live session: {e}") from e


@router.post("/live-session/products")
async def add_live_session_products(payload: SessionProductsRequest) -> dict[str, Any]:
    """Assign products into the active live session pool."""
    try:
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is None:
            raise HTTPException(409, "No active live session")
        items = store.add_session_products(
            session_id=int(active["session"]["id"]),
            product_ids=payload.product_ids,
        )
        return {"status": "updated", "count": len(items), "items": items}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("add_live_session_products_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to add session products: {e}") from e


@router.post("/live-session/focus")
async def set_live_session_focus(payload: FocusProductRequest) -> dict[str, Any]:
    """Set the current focus product for the active session."""
    try:
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is None:
            raise HTTPException(409, "No active live session")
        state = store.set_focus_product(
            session_id=int(active["session"]["id"]),
            session_product_id=payload.session_product_id,
            reason="operator_focus",
        )
        return {"status": "updated", "state": state}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("set_live_session_focus_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to set focus product: {e}") from e


@router.post("/live-session/pause")
async def pause_live_session(payload: LiveSessionPauseRequest) -> dict[str, Any]:
    """Pause operator-assisted rotation for Q&A or manual intervention."""
    try:
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is None:
            raise HTTPException(409, "No active live session")
        state = store.pause_rotation(
            session_id=int(active["session"]["id"]),
            reason=payload.reason,
            question=payload.question,
        )
        if payload.question:
            updated_pending_question = await _generate_affiliate_answer_draft(
                question=payload.question,
                reason=payload.reason,
                active_session=store.get_active_live_session(),
            )
            state = store.update_pending_question(
                session_id=int(active["session"]["id"]),
                pending_question=updated_pending_question,
            )
        _sync_show_director_with_live_session(store.get_active_live_session())
        return {"status": "paused", "state": state}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("pause_live_session_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to pause live session: {e}") from e


@router.post("/live-session/resume")
async def resume_live_session() -> dict[str, Any]:
    """Resume operator-assisted rotation after pause."""
    try:
        store = get_control_plane_store()
        active = store.get_active_live_session()
        if active["session"] is None:
            raise HTTPException(409, "No active live session")
        state = store.resume_rotation(session_id=int(active["session"]["id"]))
        _sync_show_director_with_live_session(store.get_active_live_session())
        return {"status": "resumed", "state": state}
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(404, str(e)) from e
    except Exception as e:
        logger.error("resume_live_session_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to resume live session: {e}") from e


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
    director = _sync_show_director_with_live_session()
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


def _parse_json_payload(raw_text: str) -> dict[str, Any] | list[Any] | None:
    try:
        parsed = json.loads(raw_text.strip())
    except (AttributeError, json.JSONDecodeError):
        return None
    if isinstance(parsed, (dict, list)):
        return parsed
    return None


def _find_focus_session_product(active_session: dict[str, Any]) -> dict[str, Any] | None:
    state = active_session.get("state") or {}
    focus_session_product_id = state.get("current_focus_session_product_id")
    focus_product_id = state.get("current_focus_product_id")
    products = active_session.get("products") or []

    if focus_session_product_id:
        for item in products:
            if int(item.get("id", 0)) == int(focus_session_product_id):
                return item
    if focus_product_id:
        for item in products:
            if int(item.get("product_id", 0)) == int(focus_product_id):
                return item
    return products[0] if products else None


def _build_live_product_context(active_session: dict[str, Any]) -> str:
    focus_item = _find_focus_session_product(active_session)
    if focus_item is None:
        return "Tidak ada produk fokus aktif."

    product = focus_item.get("product", {})
    name = str(product.get("name", "Produk live")).strip() or "Produk live"
    price = str(product.get("price_formatted", product.get("price", "-"))).strip() or "-"
    selling_points = ", ".join(str(point).strip() for point in product.get("selling_points", []) if str(point).strip())
    affiliate_link = str(product.get("affiliate_links", {}).get("tiktok", "")).strip()
    compliance_notes = str(product.get("compliance_notes", "")).strip()

    return ". ".join(
        [
            f"Produk fokus: {name}",
            f"Harga: {price}",
            f"Selling points: {selling_points or '-'}",
            f"Link TikTok: {affiliate_link or '-'}",
            f"Compliance notes: {compliance_notes or '-'}",
        ]
    )


def _build_brain_test_prompts(request: BrainTestRequest, task: Any) -> tuple[str, str]:
    from src.brain.adapters.base import TaskType
    from src.brain.persona import PersonaEngine

    persona = PersonaEngine()
    state = "SELLING" if task == TaskType.SELLING_SCRIPT else "REACTING"
    system_prompt = request.system_prompt.strip() or persona.build_system_prompt(
        state=state,
        product_context=request.product_context.strip(),
        additional_context=request.additional_context.strip(),
    )
    if not request.system_prompt.strip():
        system_prompt += (
            f"\nROLE_META: {persona.persona.role}"
            f"\nPRODUCT_RELATIONSHIP: {persona.persona.product_relationship}"
        )

    user_prompt = request.user_prompt.strip()
    if user_prompt:
        return system_prompt, user_prompt

    if task == TaskType.CHAT_REPLY:
        user_prompt = persona.build_chat_reply_prompt(
            viewer_name=request.viewer_name,
            viewer_message=request.viewer_message or request.question,
            product_context=request.product_context,
            additional_context=request.additional_context,
        )
    elif task == TaskType.PRODUCT_QA:
        user_prompt = persona.build_product_qa_prompt(
            question=request.question or request.viewer_message or "Jelaskan produk ini secara faktual.",
            product_context=request.product_context or "Tidak ada konteks produk.",
            additional_context=request.additional_context,
        )
    elif task == TaskType.SAFETY_CHECK:
        user_prompt = persona.build_safety_check_prompt(
            candidate_text=request.candidate_text or request.user_prompt or "",
            product_context=request.product_context or "Tidak ada konteks produk.",
            additional_context=request.additional_context,
        )
    elif task == TaskType.EMOTION_DETECT:
        user_prompt = persona.build_emotion_prompt(request.viewer_message or request.question or "")
    else:
        user_prompt = "Halo, perkenalkan produk ini!"

    return system_prompt, user_prompt


async def _generate_affiliate_answer_draft(
    *,
    question: str,
    reason: str,
    active_session: dict[str, Any],
) -> dict[str, Any]:
    from src.brain.adapters.base import TaskType
    from src.brain.persona import PersonaEngine

    pending_question: dict[str, Any] = {"text": question, "reason": reason}
    router_instance = get_llm_router()
    if router_instance is None:
        pending_question.update(
            {
                "answer_draft": "Sebentar kak, cek detail resmi produk di link yang tersedia ya.",
                "task_type": TaskType.CHAT_REPLY.value,
                "answer_provider": "fallback",
                "answer_model": "template",
                "safety": {"safe": True, "reason_code": "router_unavailable"},
            }
        )
        return pending_question

    persona = PersonaEngine()
    product_context = _build_live_product_context(active_session)
    additional_context = (
        "Jawab sebagai affiliate host TikTok Live, bukan brand owner. "
        "Jawab natural, singkat, ramah, dan tetap faktual. "
        "Kalau tidak yakin, arahkan cek detail produk atau rating di link."
    )
    system_prompt = persona.build_system_prompt(
        state="REACTING",
        product_context=product_context,
        additional_context=additional_context,
    )
    answer_prompt = persona.build_chat_reply_prompt(
        viewer_name="viewer",
        viewer_message=question,
        product_context=product_context,
        additional_context=additional_context,
    )

    try:
        answer = await asyncio.wait_for(
            router_instance.route(
                system_prompt=system_prompt,
                user_prompt=answer_prompt,
                task_type=TaskType.CHAT_REPLY,
                preferred_provider=None,
            ),
            timeout=45.0,
        )
        answer_draft = answer.text.strip()

        safety_prompt = persona.build_safety_check_prompt(
            candidate_text=answer_draft,
            product_context=product_context,
            additional_context="Evaluasi jawaban affiliate live commerce. Tahan klaim berlebihan dan pastikan tetap realistis.",
        )
        safety_response = await asyncio.wait_for(
            router_instance.route(
                system_prompt=system_prompt,
                user_prompt=safety_prompt,
                task_type=TaskType.SAFETY_CHECK,
                preferred_provider=None,
            ),
            timeout=45.0,
        )
        parsed_safety = _parse_json_payload(safety_response.text)
        if isinstance(parsed_safety, dict):
            rewrite = str(parsed_safety.get("rewrite", "")).strip()
            if rewrite:
                answer_draft = rewrite
            pending_question["safety"] = parsed_safety
            pending_question["safety_provider"] = safety_response.provider
            pending_question["safety_model"] = safety_response.model
        else:
            pending_question["safety"] = {"safe": True, "reason_code": "unparsed_safety_response"}

        pending_question.update(
            {
                "answer_draft": answer_draft,
                "task_type": TaskType.CHAT_REPLY.value,
                "answer_provider": answer.provider,
                "answer_model": answer.model,
            }
        )
        return pending_question
    except Exception as e:
        logger.warning("pause_live_session_answer_draft_failed", error=str(e), exc_info=True)
        pending_question.update(
            {
                "answer_draft": "Sebentar kak, cek detail resmi produk dan ratingnya dulu ya di link yang tersedia.",
                "task_type": TaskType.CHAT_REPLY.value,
                "answer_provider": "fallback",
                "answer_model": "template",
                "safety": {"safe": True, "reason_code": "draft_generation_failed"},
                "draft_error": str(e)[:200],
            }
        )
        return pending_question

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

        system_prompt, user_prompt = _build_brain_test_prompts(request, task)

        response = await asyncio.wait_for(
            router_instance.route(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
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

        result = {
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
        parsed_json = _parse_json_payload(response.text)
        if parsed_json is not None:
            result["parsed_json"] = parsed_json
        return result

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


class UpdateBrainConfigRequest(BaseModel):
    daily_budget_usd: float
    fallback_order: list[str]
    routing_table: dict[str, list[str]]


class GenerateScriptRequest(BaseModel):
    product_name: str
    price: float
    features: list[str]
    target_duration_sec: int = 30
    provider: str | None = None


def _coerce_prompt_registry_error(exc: ValueError) -> HTTPException:
    message = str(exc)
    status_code = 404 if "not found" in message else 400
    return HTTPException(status_code, message)


@router.get("/brain/config")
async def brain_config() -> dict[str, Any]:
    """Get live AI Brain configuration and routing table."""
    try:
        return _build_brain_config_payload(get_llm_router())
    except Exception as e:
        logger.error("brain_config_error", error=str(e), exc_info=True)
        return {"error": str(e)}


@router.put("/brain/config")
async def update_brain_config(request: UpdateBrainConfigRequest) -> dict[str, Any]:
    """Update runtime-only AI Brain config without persisting to disk."""
    try:
        from src.brain.adapters.base import TaskType

        router_instance = get_llm_router()
        if router_instance is None:
            raise HTTPException(500, "LLM Router not initialized")

        if request.daily_budget_usd <= 0:
            raise HTTPException(400, "daily_budget_usd must be greater than zero")

        task_map = {task.value: task for task in TaskType}
        invalid_task_types = sorted(set(request.routing_table.keys()).difference(task_map.keys()))
        if invalid_task_types:
            raise HTTPException(400, f"unknown task types: {', '.join(invalid_task_types)}")

        if any(not providers for providers in request.routing_table.values()):
            raise HTTPException(400, "each routing table entry must include at least one provider")

        available_providers = sorted(router_instance.adapters.keys())
        requested_providers = set(request.fallback_order)
        for providers in request.routing_table.values():
            requested_providers.update(providers)
        unknown_providers = sorted(requested_providers.difference(available_providers))
        if unknown_providers:
            raise HTTPException(400, f"unknown providers: {', '.join(unknown_providers)}")

        runtime_config = get_brain_runtime_config()
        current_snapshot = runtime_config.snapshot(router_instance)
        merged_routing_table = dict(current_snapshot["routing_table"])
        for task_name, providers in request.routing_table.items():
            merged_routing_table[task_name.strip().lower()] = list(providers)

        runtime_config.update(
            router=router_instance,
            daily_budget_usd=request.daily_budget_usd,
            fallback_order=request.fallback_order,
            routing_table=merged_routing_table,
        )

        config_payload = _build_brain_config_payload(router_instance)
        logger.info(
            "brain_config_updated",
            providers=config_payload["available_providers"],
            daily_budget_usd=config_payload["daily_budget_usd"],
        )
        return {
            "status": "updated",
            "message": "Runtime AI Brain configuration updated. Changes reset on restart.",
            "edit_mode": "runtime_only",
            "persists_across_restart": False,
            "config": config_payload,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_brain_config_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to update brain config: {e}") from e


@router.post("/brain/generate-script")
async def generate_brain_script(request: GenerateScriptRequest) -> dict[str, Any]:
    """Generate a selling script using the active persona and LLM router."""
    try:
        from src.brain.adapters.base import TaskType
        from src.brain.persona import PersonaEngine

        router_instance = get_llm_router()
        if router_instance is None:
            raise HTTPException(500, "LLM Router not initialized")

        product_name = request.product_name.strip()
        if not product_name:
            raise HTTPException(400, "product_name is required")
        if request.price <= 0:
            raise HTTPException(400, "price must be greater than zero")

        features = [feature.strip() for feature in request.features if feature.strip()]
        persona = PersonaEngine()
        product_context = f"{product_name} - Rp {request.price:,.0f}"
        if features:
            product_context += f" | Fitur: {', '.join(features)}"

        response = await asyncio.wait_for(
            router_instance.route(
                system_prompt=persona.build_system_prompt(
                    state="SELLING",
                    product_context=product_context,
                ),
                user_prompt=persona.build_selling_script_prompt(
                    product_name=product_name,
                    price=request.price,
                    features=features,
                    target_duration_sec=request.target_duration_sec,
                ),
                task_type=TaskType.SELLING_SCRIPT,
                preferred_provider=request.provider,
            ),
            timeout=90.0,
        )

        if not response.success:
            raise HTTPException(500, f"LLM script generation failed: {response.error}")

        get_show_director().update_brain_runtime(
            provider=response.provider,
            model=response.model,
        )
        return {
            "success": True,
            "script": response.text,
            "provider": response.provider,
            "model": response.model,
            "latency_ms": round(response.latency_ms, 1),
        }
    except asyncio.TimeoutError:
        logger.error("generate_brain_script_timeout")
        raise HTTPException(504, "Script generation timed out after 90 seconds")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("generate_brain_script_error", error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to generate script: {e}") from e


@router.get("/director/runtime")
async def get_director_runtime() -> dict[str, Any]:
    """Return aggregated director, brain, prompt, and script runtime state."""
    try:
        return _get_director_runtime_contract()
    except Exception as e:
        logger.error("director_runtime_error", error=str(e), exc_info=True)
        return {
            "director": _sync_show_director_with_live_session(),
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
        rows = registry.list_revisions()
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
        return get_prompt_registry().get_revision(revision_id)
    except HTTPException:
        raise
    except ValueError as e:
        raise _coerce_prompt_registry_error(e) from e
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
        revision = get_prompt_registry().create_revision(
            slug=request.slug,
            templates=request.templates,
            persona=request.persona,
        )
        logger.info("prompt_created", id=revision["id"], slug=revision["slug"], version=revision["version"])
        return {"id": revision["id"], "slug": revision["slug"], "version": revision["version"], "status": revision["status"]}
    except ValueError as e:
        raise _coerce_prompt_registry_error(e) from e
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
        get_prompt_registry().update_revision(
            revision_id,
            templates=request.templates,
            persona=request.persona,
        )
        logger.info("prompt_updated", id=revision_id)
        return {"id": revision_id, "status": "updated"}
    except HTTPException:
        raise
    except ValueError as e:
        raise _coerce_prompt_registry_error(e) from e
    except Exception as e:
        logger.error("update_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to update prompt: {e}")


@router.post("/brain/prompts/{revision_id}/publish")
async def publish_prompt_revision(revision_id: int) -> dict[str, Any]:
    """Publish a draft revision (deactivates current active, activates this one)."""
    try:
        revision = get_prompt_registry().publish_revision(revision_id)
        get_show_director().update_brain_runtime(
            prompt_revision=f'{revision["slug"]}:v{revision["version"]}',
        )
        logger.info("prompt_published", id=revision_id, slug=revision["slug"])
        return {
            "id": revision_id,
            "status": revision["status"],
            "slug": revision["slug"],
            "version": revision["version"],
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise _coerce_prompt_registry_error(e) from e
    except Exception as e:
        logger.error("publish_prompt_error", revision_id=revision_id, error=str(e), exc_info=True)
        raise HTTPException(500, f"Failed to publish prompt: {e}")


@router.delete("/brain/prompts/{revision_id}")
async def delete_prompt_revision(revision_id: int) -> dict[str, Any]:
    """Delete a draft prompt revision (only drafts can be deleted)."""
    try:
        result = get_prompt_registry().delete_revision(revision_id)
        logger.info("prompt_deleted", id=revision_id)
        return result
    except HTTPException:
        raise
    except ValueError as e:
        raise _coerce_prompt_registry_error(e) from e
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
        registry = get_prompt_registry()
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
            registry.validate_payload(
                templates=generated.get("templates", {}),
                persona=generated.get("persona", {}),
            )
            get_show_director().update_brain_runtime(
                provider=response.provider,
                model=response.model,
            )
            
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
            director = _sync_show_director_with_live_session()
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
        payload = status.to_dict()
        state = payload.get("state", "unknown")
        logger.info("engine_livetalking_start_api", state=state)
        if state == "running":
            receipt_status = "success"
        elif state == "error":
            receipt_status = "error"
        else:
            receipt_status = "blocked"
        return _build_engine_action_result(
            action="engine.start",
            status=receipt_status,
            message=(
                "Avatar menerima perintah jalan."
                if receipt_status == "success"
                else (
                    "Avatar gagal dijalankan."
                    if receipt_status == "error"
                    else "Perintah jalan sudah dikirim, tetapi avatar belum melapor berjalan."
                )
            ),
            reason_code=(
                "engine_start_requested"
                if receipt_status == "success"
                else ("engine_start_failed" if receipt_status == "error" else "engine_start_not_confirmed")
            ),
            next_step=(
                "Tunggu status avatar berubah menjadi berjalan."
                if receipt_status == "success"
                else (
                    "Periksa tab Teknis dan log engine sebelum mencoba lagi."
                    if receipt_status == "error"
                    else "Periksa tab Teknis atau muat ulang status avatar."
                )
            ),
            payload=payload,
            details=[
                f"state {state}",
                f"transport {payload.get('transport', 'unknown')}",
                f"port {payload.get('port', 'unknown')}",
                *([str(payload.get("last_error"))] if payload.get("last_error") else []),
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
        truth["director"] = _sync_show_director_with_live_session()
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
    """Validate the active RTMP target, falling back to env bootstrap if none exists."""
    try:
        store = get_control_plane_store()
        active_target = store.get_active_stream_target("tiktok")
        if active_target is not None:
            active_secret = store.get_stream_target_secret(int(active_target["id"]))
            if active_secret is not None:
                checks = _build_target_validation_checks(active_secret)
                status = "pass" if all(check["passed"] for check in checks) else "fail"
                persisted = store.save_stream_target_validation(int(active_target["id"]), status=status, checks=checks)
                return {"status": status, "checks": checks, "target": persisted}

        bootstrap_target = {
            "platform": "tiktok",
            "rtmp_url": os.getenv("TIKTOK_RTMP_URL", ""),
            "stream_key": os.getenv("TIKTOK_STREAM_KEY", ""),
        }
        checks = _build_target_validation_checks(bootstrap_target)
        checks.append(
            {
                "check": "control_plane_target",
                "passed": False,
                "message": "No active persisted TikTok stream target yet; using env bootstrap fallback",
            }
        )
        status = "pass" if all(check["passed"] for check in checks[:-1]) else "fail"
        return {"status": status, "checks": checks}
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


@router.get("/voice/profiles")
async def list_voice_profiles() -> list[dict[str, Any]]:
    _ensure_default_voice_profile()
    return get_control_plane_store().list_voice_profiles()


@router.post("/voice/profiles")
async def create_voice_profile(payload: VoiceProfileMutationRequest) -> dict[str, Any]:
    try:
        return get_control_plane_store().create_voice_profile(
            name=payload.name,
            reference_wav_path=payload.reference_wav_path,
            reference_text=payload.reference_text,
            language=payload.language,
            supported_languages=payload.supported_languages,
            profile_type=payload.profile_type,
            quality_tier=payload.quality_tier,
            guidance=payload.guidance,
            notes=payload.notes,
            engine=payload.engine,
        )
    except Exception as exc:
        logger.error("voice_profile_create_error", error=str(exc), exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/voice/profiles/{profile_id}")
async def update_voice_profile(profile_id: int, payload: VoiceProfileMutationRequest) -> dict[str, Any]:
    try:
        return get_control_plane_store().update_voice_profile(
            profile_id,
            name=payload.name,
            reference_wav_path=payload.reference_wav_path,
            reference_text=payload.reference_text,
            language=payload.language,
            supported_languages=payload.supported_languages,
            profile_type=payload.profile_type,
            quality_tier=payload.quality_tier,
            guidance=payload.guidance,
            notes=payload.notes,
            engine=payload.engine,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/voice/profiles/{profile_id}")
async def delete_voice_profile(profile_id: int) -> dict[str, Any]:
    try:
        return get_control_plane_store().delete_voice_profile(profile_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/voice/profiles/{profile_id}/activate")
async def activate_voice_profile(profile_id: int) -> dict[str, Any]:
    try:
        return get_control_plane_store().activate_voice_profile(profile_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/voice/lab")
async def get_voice_lab_state() -> dict[str, Any]:
    _ensure_default_voice_profile()
    return get_control_plane_store().get_voice_lab_state()


@router.put("/voice/lab")
async def update_voice_lab_state(payload: VoiceLabStateRequest) -> dict[str, Any]:
    return get_control_plane_store().update_voice_lab_state(
        mode=payload.mode,
        active_profile_id=payload.active_profile_id,
        preview_session_id=payload.preview_session_id,
        selected_avatar_id=payload.selected_avatar_id,
        selected_language=payload.selected_language,
        selected_profile_type=payload.selected_profile_type,
        selected_revision_id=payload.selected_revision_id,
        selected_style_preset=payload.selected_style_preset,
        selected_stability=payload.selected_stability,
        selected_similarity=payload.selected_similarity,
        draft_text=payload.draft_text,
        last_generation_id=payload.last_generation_id,
    )


@router.post("/voice/lab/preview-session")
async def update_voice_lab_preview_session(payload: VoiceLabStateRequest) -> dict[str, Any]:
    current = get_control_plane_store().get_voice_lab_state()
    return get_control_plane_store().update_voice_lab_state(
        mode=current["mode"],
        active_profile_id=current["active_profile_id"],
        preview_session_id=payload.preview_session_id,
        selected_avatar_id=payload.selected_avatar_id or current["selected_avatar_id"],
        selected_language=current.get("selected_language", "id"),
        selected_profile_type=current.get("selected_profile_type", "quick_clone"),
        selected_revision_id=current.get("selected_revision_id"),
        selected_style_preset=current.get("selected_style_preset", "natural"),
        selected_stability=current.get("selected_stability", 0.75),
        selected_similarity=current.get("selected_similarity", 0.8),
        draft_text=current["draft_text"],
        last_generation_id=current.get("last_generation_id"),
    )


@router.get("/voice/generations")
async def list_voice_generations(limit: int = 20) -> list[dict[str, Any]]:
    return get_control_plane_store().list_voice_generations(limit=limit)


@router.get("/voice/generations/{generation_id}")
async def get_voice_generation(generation_id: int) -> dict[str, Any]:
    generation = get_control_plane_store().get_voice_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail=f"Voice generation {generation_id} not found")
    return generation


@router.get("/voice/audio/{generation_id}")
async def get_voice_generation_audio(generation_id: int):
    generation = get_control_plane_store().get_voice_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail=f"Voice generation {generation_id} not found")
    audio_path = Path(generation["audio_path"])
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio file missing for generation {generation_id}")
    return FileResponse(audio_path, media_type="audio/wav", filename=audio_path.name)


@router.get("/voice/audio/{generation_id}/download")
async def get_voice_generation_audio_download(generation_id: int):
    generation = get_control_plane_store().get_voice_generation(generation_id)
    if generation is None:
        raise HTTPException(status_code=404, detail=f"Voice generation {generation_id} not found")
    audio_path = Path(generation["audio_path"])
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail=f"Audio file missing for generation {generation_id}")
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=generation.get("download_name") or audio_path.name,
    )


@router.post("/voice/generate")
async def generate_voice(payload: VoiceGenerationRequest) -> dict[str, Any]:
    _ensure_default_voice_profile()
    store = get_control_plane_store()
    lab_state = store.get_voice_lab_state()
    profile_id = payload.profile_id or lab_state.get("active_profile_id")
    if profile_id is None:
        raise HTTPException(status_code=404, detail="No active voice profile selected")

    profile = store.get_voice_profile(int(profile_id))
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Voice profile {profile_id} not found")

    attach_to_avatar = bool(payload.attach_to_avatar or payload.mode == "attach_avatar")
    preview_session_id = payload.preview_session_id or lab_state.get("preview_session_id", "")
    if attach_to_avatar and not preview_session_id:
        raise HTTPException(status_code=409, detail="No preview session available for avatar attach")

    engine = get_voice_lab_engine()
    if not await engine.health_check():
        raise HTTPException(status_code=409, detail="Fish-Speech sidecar is not reachable")

    synth_kwargs = {
        "text": payload.text,
        "reference_wav_path": profile["reference_wav_path"],
        "reference_text": profile["reference_text"],
        "emotion": payload.emotion,
        "speed": payload.speed,
        "language": payload.language,
        "style_preset": payload.style_preset,
        "stability": payload.stability,
        "similarity": payload.similarity,
    }
    try:
        result = await engine.synthesize_with_profile(**synth_kwargs)
    except TypeError as exc:
        if "unexpected keyword argument" not in str(exc):
            raise
        logger.warning(
            "voice_lab_engine_legacy_signature",
            error=str(exc),
            engine=type(engine).__name__,
        )
        result = await engine.synthesize_with_profile(
            text=payload.text,
            reference_wav_path=profile["reference_wav_path"],
            reference_text=profile["reference_text"],
            emotion=payload.emotion,
            speed=payload.speed,
        )
    audio_path = _get_voice_audio_path()
    audio_path.write_bytes(result.audio_data)

    if attach_to_avatar:
        await _attach_audio_to_livetalking(audio_path=audio_path, session_id=preview_session_id)

    generation = store.create_voice_generation(
        mode=payload.mode,
        profile_id=profile["id"],
        source_type=payload.source_type,
        input_text=payload.text,
        emotion=payload.emotion,
        speed=payload.speed,
        status="success",
        audio_path=str(audio_path),
        audio_size_bytes=len(result.audio_data),
        latency_ms=result.latency_ms,
        duration_ms=result.duration_ms,
        attached_to_avatar=attach_to_avatar,
        avatar_session_id=preview_session_id if attach_to_avatar else "",
        language=payload.language,
        style_preset=payload.style_preset,
        stability=payload.stability,
        similarity=payload.similarity,
        audio_filename=audio_path.name,
        download_name=f"{profile['name'].lower().replace(' ', '-')}-{payload.language}.wav",
    )
    updated_state = store.update_voice_lab_state(
        mode=payload.mode,
        active_profile_id=profile["id"],
        preview_session_id=preview_session_id if attach_to_avatar else lab_state.get("preview_session_id", ""),
        selected_avatar_id=payload.avatar_id or lab_state.get("selected_avatar_id", ""),
        selected_language=payload.language,
        selected_profile_type=profile.get("profile_type", "quick_clone"),
        selected_revision_id=lab_state.get("selected_revision_id"),
        selected_style_preset=payload.style_preset,
        selected_stability=payload.stability,
        selected_similarity=payload.similarity,
        draft_text=payload.text,
        last_generation_id=generation["id"],
    )
    return {
        "status": "success",
        "message": f"Synthesized {len(payload.text)} characters successfully",
        "provenance": "mock" if is_mock_mode() else "real_local",
        "action": "voice.generate",
        "generation_id": generation["id"],
        "audio_url": f"/api/voice/audio/{generation['id']}",
        "download_url": f"/api/voice/audio/{generation['id']}/download",
        "latency_ms": result.latency_ms,
        "duration_ms": result.duration_ms,
        "audio_length_bytes": len(result.audio_data),
        "attached_to_avatar": attach_to_avatar,
        "avatar_session_id": preview_session_id if attach_to_avatar else "",
        "language": payload.language,
        "style_preset": payload.style_preset,
        "stability": payload.stability,
        "similarity": payload.similarity,
        "profile": profile,
        "lab_state": updated_state,
    }


@router.get("/voice/training-jobs")
async def list_voice_training_jobs(limit: int = 20) -> list[dict[str, Any]]:
    return get_control_plane_store().list_voice_training_jobs(limit=limit)


@router.post("/voice/training-jobs")
async def create_voice_training_job(payload: VoiceTrainingJobRequest) -> dict[str, Any]:
    store = get_control_plane_store()
    active_session = store.get_active_live_session()
    if active_session.get("session") is not None:
        raise HTTPException(status_code=409, detail="Cannot start voice training while an active live session is running")

    profile = store.get_voice_profile(payload.profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Voice profile {payload.profile_id} not found")
    if profile.get("profile_type") != "studio_voice":
        raise HTTPException(status_code=409, detail="Training jobs require a studio_voice profile")

    log_dir = _get_voice_runtime_dir() / "training"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"voice-training-{payload.profile_id}-{int(time.time())}.log"
    log_path.write_text(
        "Voice training job created from dashboard control plane.\n"
        "This host currently records the orchestration state only.\n",
        encoding="utf-8",
    )

    job = store.create_voice_training_job(
        profile_id=payload.profile_id,
        job_type=payload.job_type,
        status="queued",
        current_stage="queued",
        progress_pct=0.0,
        dataset_path=payload.dataset_path,
        log_path=str(log_path),
        meta={
            "profile_name": profile["name"],
            "supported_languages": profile.get("supported_languages", [profile.get("language", "id")]),
            "quality_tier": profile.get("quality_tier", "studio"),
        },
    )
    return {
        "status": "success",
        "message": "Voice training job queued",
        "job": job,
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


