# Server-Hosted Ops Controller Design

**Status:** Approved design for implementation planning  
**Date:** 2026-03-10  
**Audience:** operator, reviewer, coding agent  
**Scope:** evolve the existing dashboard into a server-hosted operations controller that supports local validation first, then remote production operation with long-run resilience

---

## 1. Problem Statement

`videoliveai` currently has the right local building blocks:

- `/dashboard` is already the primary operator UI
- the FastAPI app already binds to `0.0.0.0:8000`
- local face and local Fish-Speech voice slices now work in non-mock mode

But the original dashboard architecture still behaves like a local-development operator shell:

- docs still frame the operator flow around `localhost`
- there is no first-class production operations model for a GPU host that keeps running after the operator browser disconnects
- there is no dedicated voice operations panel
- incident handling, restart visibility, resource growth monitoring, and soak-run guardrails are not yet first-class parts of the control plane
- current auth assumptions are still local-network oriented and not safe enough for internet exposure without reverse-proxy policy

That is acceptable for local verification, but not for a 12-hours-per-day production host where the operator may connect remotely and the browser must never be part of the execution path.

---

## 2. Architecture Change Summary

This is an **architecture evolution**, not a rewrite.

The core media/control shape remains the same:

- `FastAPI` remains the main control plane
- `Fish-Speech` remains a local sidecar for voice
- `LiveTalking / MuseTalk` remains a local sidecar for face
- `/dashboard` remains the only operator UI

What changes is the **operator and runtime model**:

- from: local operator shell primarily accessed on `localhost`
- to: **server-hosted operations controller** accessed remotely through `IP:port` or a domain behind `Kong`, `Nginx`, or `Caddy`

If implemented, this will change the practical architecture baseline for operations, because the dashboard is no longer treated as a local convenience surface. It becomes the production cockpit.

---

## 3. Non-Negotiable Goals

1. **Server execution independence:** livestream keeps running even if the operator laptop/browser disconnects or powers off.
2. **Single dashboard truth:** the same dashboard UX is used in local validation and on the production server.
3. **Local-first validation discipline:** local host remains the truth lab for script correctness, validation gates, and recovery-path testing before promotion to the GPU server.
4. **Remote-safe access path:** production access must work through `IP:port` or domain with reverse proxy support.
5. **Long-run resilience:** the controller must surface incidents, restarts, queue buildup, resource growth, and degraded modes clearly enough for 12-hour runs.
6. **Honest state reporting:** no subsystem may appear healthy when running on fallback, blocked, or degraded behavior.

---

## 4. Non-Goals

The following are explicitly out of scope for this design:

- multi-tenant SaaS control plane
- fleet orchestration across many GPU nodes
- replacing FastAPI with another backend framework
- browser-to-browser remote desktop streaming
- pretending local GTX 1650 latency is production-ready
- exposing vendor debug pages as operator-facing UI

---

## 5. Current Baseline and Gaps

### Existing strengths

- consolidated truth endpoint already exists: `GET /api/runtime/truth`
- health and readiness endpoints already exist
- validation history already exists
- existing frontend shell already has panels for overview, readiness, engine, stream, monitor, diagnostics, and validation
- local non-mock Fish-Speech clone validation already passes

### Operational gaps

- truth model does not yet describe host identity, deployment mode, guardrails, resource budgets, or incidents
- there is no voice-specific control panel
- stream control is still too shallow for live recovery work
- monitor panel is still generic and not a real ops cockpit
- no first-class incident timeline or structured operator receipts for long-run recovery
- production access still assumes the old local-dev threat model

---

## 6. Architecture Options

### Option A: Local cockpit controls remote host

- Operator runs dashboard locally and points it to the remote host.
- Pros: familiar dev workflow.
- Cons: wrong failure model for production, introduces split state, and makes the dashboard feel like a remote client instead of the source of truth.

### Option B (Recommended): Server-hosted dashboard behind reverse proxy

- The dashboard is served by the production host itself.
- The operator opens the server URL from any browser.
- Pros: clean execution model, browser disconnect does not affect stream, state lives where the processes live, simplest operational truth.
- Cons: requires proxy/auth hardening and more production-grade observability.

### Option C: Dedicated control plane + node agents

- Separate orchestrator talks to per-host agents.
- Pros: strongest future scale story.
- Cons: overkill for the workspace and current stage.

**Decision:** adopt **Option B**.

---

## 7. Chosen Architecture

### 7.1 Execution Plane

The production server owns all runtime-critical processes:

- `FastAPI` dashboard/backend
- `Fish-Speech` local sidecar
- `LiveTalking / MuseTalk` face engine
- `RTMP / ffmpeg` stream worker
- log/metrics collectors
- process supervisor

The browser never becomes part of the execution plane.

### 7.2 Access Plane

Operators access the dashboard through:

- `http://<ip>:<port>/dashboard` for trusted private setups, or preferably
- `https://<domain>/dashboard` behind `Kong`, `Nginx`, or `Caddy`

The reverse proxy is responsible for:

- TLS termination
- auth gate
- websocket upgrade
- request/stream timeout policy
- rate limiting and IP allowlists where appropriate
- hiding internal sidecar ports from the public internet

### 7.3 State Plane

Operational state must be stored server-side, not in browser session state:

- pipeline state
- live session state
- emergency state
- restart counters
- last incidents
- rolling resource metrics
- validation receipts
- last known runtime truth

### 7.4 Supervisor Plane

Each critical process must run under a supervisor (`systemd`, `supervisor`, or container restart policy) with:

- startup order
- health-aware restart policy
- cooldown windows
- bounded retry policy
- log rotation integration

### 7.5 Promotion Flow

- **Local host** proves correctness and controller behavior.
- **Server host** proves live latency, long-run stability, and production readiness.

Local pass is required before server deployment, but local pass is not the same as production readiness.

---

## 8. Dashboard Controller Design

The dashboard remains a single UI, but becomes an operations cockpit.

### 8.1 Truth Bar

Extend the truth bar to include:

- `host_name`
- `host_role`: `local_lab` | `server_production`
- `deployment_mode`: `cold` | `warming` | `ready` | `live` | `degraded` | `recovering` | `blocked` | `stopped`
- `session_id`
- `last_incident_severity`
- `active_guardrails`

### 8.2 Ops Summary Panel

New panel for top-level operator decisions:

- overall status
- voice status
- face status
- stream status
- system uptime
- recent restart count
- last critical incident
- CPU/RAM/VRAM/disk growth summary
- current deployment mode

### 8.3 Voice Panel

New first-class voice control and observability panel:

- requested vs resolved engine
- fallback active flag
- sidecar reachable flag
- reference asset readiness
- warm/cold state
- last synthesis latency
- rolling `p50/p95`
- queue depth
- chunk size / timeout in use
- last error

Operator actions:

- `Warmup Voice`
- `Run Voice Smoke`
- `Clear Voice Queue`
- `Restart Voice Worker`
- `Disable Fallback`
- `Enable Emergency Fallback`

### 8.4 Face Panel Enhancements

Existing face panel is extended with:

- render FPS
- frame backlog
- audio-to-face drift
- avatar loaded state
- worker restart count
- last frame age

### 8.5 Stream Panel Enhancements

Existing stream panel is extended with:

- target platform name
- masked RTMP target
- connection state
- dropped frames
- bitrate
- output resolution/FPS
- reconnect count
- stream uptime

Operator actions:

- `Validate RTMP`
- `Dry Run`
- `Go Live`
- `Reconnect Stream`
- `Graceful Stop`
- `Emergency Stop`

### 8.6 Validation Console Enhancements

Validation becomes a formal gate, not a loose toolbox.

Required checks:

- `runtime-truth`
- `real-mode-readiness`
- `voice-local-clone`
- `audio-chunking-smoke`
- `face-sync-smoke`
- `rtmp-target`
- `stream-dry-run`
- `resource-budget-check`
- `soak-sanity`

Validation results must distinguish:

- `local function pass`
- `server ready`
- `live ready`

### 8.7 Incident Panel

New incident timeline panel:

- severity `info/warn/error/critical`
- incident code
- first seen / last seen
- subsystem
- auto-recovery action taken
- resolved/unresolved state
- operator acknowledgement

### 8.8 Logs and Evidence

Expose structured operational evidence:

- latest structured log lines by subsystem
- recent action receipts
- recent validation receipts
- downloadable evidence bundle for audit

---

## 9. Runtime Truth and API Contract Extensions

The existing truth contract is kept, but extended.

### Required new truth fields

- `host`
- `host.name`
- `host.role`
- `deployment_mode`
- `session_id`
- `voice_engine.queue_depth`
- `voice_engine.chunk_chars`
- `voice_engine.time_to_first_audio_ms`
- `voice_engine.latency_p50_ms`
- `voice_engine.latency_p95_ms`
- `stream_engine.connection_state`
- `stream_engine.reconnect_count`
- `stream_engine.dropped_frames`
- `resource_metrics`
- `restart_counters`
- `incident_summary`
- `guardrails`

### Recommended new endpoints

- `GET /api/ops/summary`
- `GET /api/resources`
- `GET /api/incidents`
- `POST /api/incidents/{id}/ack`
- `POST /api/voice/warmup`
- `POST /api/voice/queue/clear`
- `POST /api/voice/restart`
- `POST /api/stream/reconnect`
- `POST /api/validate/audio-chunking-smoke`
- `POST /api/validate/stream-dry-run`
- `POST /api/validate/resource-budget`
- `POST /api/validate/soak-sanity`

All operator actions must return explicit action receipts.

---

## 10. Long-Run Resilience and Guardrails

Error handling must be layered.

### Request-level

- operator action failures return structured JSON errors
- request failure must not crash the main app

### Worker-level

- voice, face, and stream workers fail independently
- one worker crash does not take down the whole control plane

### Supervisor-level

- bounded restarts
- cooldown windows
- explicit degraded state after repeated failures

### Policy-level

Guardrails must be published in truth and enforced in code:

- too many restarts in a short window
- disk usage threshold
- temp file growth threshold
- queue depth threshold
- VRAM pressure threshold
- repeated RTMP reconnect failures

When guardrails trip, the dashboard must switch to `degraded`, `recovering`, or `blocked` honestly.

---

## 11. Audio Optimization Strategy

This phase is optimization, not “make audio work”.

### Local host goals

- prove all scripts and controls work
- prove chunking path exists
- prove incidents and recovery are visible
- prove validation gates behave correctly

### Server host goals

- reduce time-to-first-audio
- keep queue depth bounded
- sustain chunk throughput under live-like script load
- preserve audio-face sync

### Required optimization work

- preload reference assets once
- add warmup synthesis path
- split text into bounded chunks
- publish queue metrics
- add backpressure policy
- record `time_to_first_audio_ms`, `total_synthesis_ms`, `audio_duration_ms`, and real-time factor

Increasing timeout alone does not count as live optimization.

---

## 12. Security and Reverse Proxy Requirements

The dashboard may be accessed remotely, but raw production exposure is not acceptable without policy.

Minimum production stance:

- proxy-terminated TLS
- authenticated operator access
- websocket support
- hidden internal ports
- restricted docs/debug surfaces
- clear separation between operator UI and vendor debug pages

This design assumes `Kong`, `Nginx`, or `Caddy` will be used as the supported production ingress.

---

## 13. Testing Strategy

### Local

Validate controller correctness and script integrity:

- backend truth tests
- incident registry tests
- validation endpoint tests
- frontend panel tests
- action receipt tests
- local dry-run command tests

### Server

Validate production fitness:

- non-mock voice chunking smoke
- RTMP dry run
- reconnect recovery
- bounded queue behavior
- short soak run

### Regression

- existing dashboard tests must remain green
- no panel may silently show healthy when fallback or degraded mode is active

---

## 14. Acceptance Criteria

This design is successfully implemented only when all are true:

1. Production dashboard is server-hosted and remotely accessible behind proxy.
2. Browser disconnect does not interrupt the live pipeline.
3. Truth endpoint exposes host role, deployment mode, incidents, and guardrails honestly.
4. Voice operations are first-class in the dashboard.
5. Validation console can distinguish local function pass from server/live readiness.
6. Incident and restart visibility is available without SSH.
7. Local validation gates pass before deployment.
8. Server dry-run and soak validation produce auditable evidence.

---

## 15. Rollout Sequence

1. Extend truth/spec contracts and backend ops state.
2. Add incidents, resources, and operator receipts.
3. Add voice operations endpoints and chunking observability.
4. Add new dashboard panels and expand validation gates.
5. Harden production ingress assumptions and docs.
6. Re-verify local truth lab.
7. Promote to server and run dry-run plus short soak.

---

## 16. Impact on Earlier Architecture

Yes: if this design is implemented, it **changes the operational architecture baseline**.

It does **not** replace the existing engine architecture. Instead, it upgrades the original local-oriented dashboard architecture into a production-grade server-hosted operations model.

That means the older statements that frame `/dashboard` primarily as `localhost` operator UI become incomplete and will need to be updated in architecture and workflow docs during implementation.
