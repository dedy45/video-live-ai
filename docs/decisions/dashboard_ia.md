# Dashboard Information Architecture

> **Status**: Active
> **Date**: 2026-03-07

## Tabs / Screens

| Tab | Purpose | Key Data |
|-----|---------|----------|
| **Overview** | System status at a glance | State, uptime, mock mode, stream status |
| **Readiness** | Pre-flight checklist | Config, DB, LiveTalking, models, FFmpeg, RTMP |
| **Engine** | LiveTalking control | Start/stop, status, model, transport, port, debug links |
| **Preview** | Avatar preview | Preview link/iframe, WebRTC test |
| **Stream** | RTMP streaming | Target config, dry-run, stream start/stop |
| **Scripts** | Script queue | Enqueue text, pending items, dispatch |
| **Diagnostics** | Logs and health | App logs, engine logs, health checks, validation |

## API Mapping

| Tab | Primary Endpoints |
|-----|-------------------|
| Overview | `GET /api/status`, `WS /api/ws/dashboard` |
| Readiness | `GET /api/readiness` |
| Engine | `GET/POST /api/engine/livetalking/*` |
| Preview | `GET /api/engine/livetalking/config` (debug URLs) |
| Stream | `POST /api/stream/start`, `POST /api/validate/rtmp-target` |
| Scripts | `GET /api/products`, TBD script queue endpoints |
| Diagnostics | `GET /api/health/summary`, `GET /api/engine/livetalking/logs` |

## Navigation

Single-page app with tab navigation. No nested routes needed for internal tool.
