# Internal Architecture Decision — Live System

> **Status**: Active
> **Date**: 2026-03-07
> **Scope**: Internal-first live streaming system
> **References**: `docs/architecture.md`, `docs/audits/AUDIT_CONTEXT_2026-03-07.md`

## Decision Summary

| Component | Role | Owner |
|-----------|------|-------|
| `videoliveai` (this repo) | Main control plane & orchestrator | FastAPI backend |
| `external/livetalking` | Sidecar engine for face rendering | Vendor subprocess |
| `src/dashboard` | **Only** operator dashboard | Svelte frontend served by FastAPI |
| `external/livetalking/web/*.html` | Debug-only vendor pages | LiveTalking vendor (not for operators) |

## Architecture Decisions

### 1. `videoliveai` = Main Control Plane

All control flow, configuration, health checks, API endpoints, and stream management
live in this repository. `videoliveai` is the single orchestrator that:

- Loads config and environment
- Manages the FastAPI server on port 8000
- Exposes all operator-facing API endpoints under `/api/*`
- Serves the operator dashboard at `/dashboard`
- Controls LiveTalking as a subprocess via the process manager

### 2. `external/livetalking` = Sidecar Engine

LiveTalking is treated as a **vendor sidecar**, not as a co-equal application.

- It runs as a subprocess managed by `src/face/livetalking_manager.py`
- Its primary role: render face/avatar frames and expose WebRTC/RTMP output
- Default port: `8010` (configurable via `LIVETALKING_PORT`)
- Entry point: `external/livetalking/app.py` (NOT `server.py`)
- We do NOT fork or rewrite LiveTalking internals in this phase

### 3. `src/dashboard` = Only Operator Dashboard

- The operator opens **one URL**: `http://localhost:8000/dashboard`
- This dashboard (Svelte, built to static files) is the single source of truth for:
  - System health and readiness
  - Engine start/stop control
  - Preview and stream management
  - Log viewing and diagnostics
- No second dashboard. No Next.js. No NestJS.

### 4. Vendor Debug Pages = Debug Only

- `http://localhost:8010/*.html` pages (webrtcapi.html, rtcpushapi.html, etc.) are
  vendor debug tools for testing the LiveTalking engine directly
- They are **not** the operator UI
- The operator dashboard links to them as "debug tools" when needed

### 5. Frontend Target = Svelte (Not Next.js)

- Dashboard frontend: Vite + Svelte, static build
- Build output: `src/dashboard/frontend/dist`
- FastAPI serves the built assets at `/dashboard`
- Next.js and NestJS are **deferred** — not part of current internal phase

### 6. Environment = UV Only

- All dependency management uses `uv` (not conda, not pip directly)
- Commands: `uv sync`, `uv run`, `uv pip install`
- No conda environments, no `conda activate` in any active documentation
- Scripts must work on both Windows and Ubuntu with minimal changes

## Component Ownership Map

```
videoliveai/
├── src/main.py                    → App entry point (FastAPI)
├── src/config/loader.py           → Config loading (Pydantic)
├── src/dashboard/api.py           → Operator API endpoints
├── src/dashboard/readiness.py     → Readiness checks [NEW]
├── src/dashboard/frontend/        → Svelte operator UI
├── src/face/livetalking_adapter.py → Engine adapter (frame generation)
├── src/face/livetalking_manager.py → Process manager (start/stop) [NEW]
├── src/stream/rtmp.py             → RTMP streaming
├── src/utils/health.py            → Health check system
├── src/data/database.py           → SQLite database
├── external/livetalking/          → Vendor sidecar (git submodule)
│   ├── app.py                     → Engine entry point
│   ├── web/                       → Debug pages (NOT operator UI)
│   └── models/                    → Runtime model weights
└── scripts/                       → Automation and verification
```

## What This Plan Does NOT Do

- Does not build Next.js, NestJS, Redis, PostgreSQL, billing, or multi-tenant auth
- Does not rewrite LiveTalking engine internals
- Does not pursue FaceFusion or body-double hybrid
- Does not add conda or poetry as dependency managers
- Does not target SaaS multi-user in this phase

## Official Commands

```bash
# Setup
uv sync --extra dev

# Test
uv run pytest tests -q -p no:cacheprovider

# Verify pipeline
uv run python scripts/verify_pipeline.py --verbose

# Validate (lint + checks)
cmd /c scripts\validate.bat

# Run server
uv run python -m src.main

# Smoke test LiveTalking
uv run python scripts/smoke_livetalking.py
```
