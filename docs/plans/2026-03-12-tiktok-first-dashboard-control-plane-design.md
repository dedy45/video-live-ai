# TikTok-First Dashboard Control Plane Design

**Status:** Approved design for implementation  
**Date:** 2026-03-12  
**Audience:** operator, reviewer, coding agent  
**Scope:** evolve the current affiliate live cockpit into a TikTok-first single-source-of-truth dashboard for `1 host GPU` and `1 active live session`, with SQLite-backed products, sessions, stream targets, operator commands, and recovery state

---

## 1. Problem Statement

`videoliveai` already has the beginnings of a live-commerce cockpit:

- FastAPI serves `/dashboard`
- AI Brain and prompt registry already exist
- products can be shown in the dashboard
- stream controls already exist in the UI

But the current runtime model is still fragmented:

- stream control does not actually own RTMP publishing end-to-end
- product state still depends on `data/products.json` and in-memory manager state
- RTMP target data is still effectively env-driven
- dashboard panels still treat browser state as part of the workflow
- there is no durable session model for a long-running live
- there is no clear pause/resume model for Q&A interruptions

That is not sufficient for a live session that can run up to 18 hours. The operator needs one authoritative dashboard that owns product pool, stream target, session state, AI rotation, Q&A interruption state, and recovery evidence.

---

## 2. Decision Summary

The approved operating model is:

- `TikTok-first`
- `1 host GPU`
- `1 active live session`
- `dashboard` as the only official control plane
- `operator-assisted rotation`
- `many session_products`
- `one current_focus_product at a time`
- `Q&A can pause rotation`
- `SQLite` as durable state store
- `Shopee` remains secondary/manual-companion until official ingest/control support is proven for the target account

---

## 3. Non-Negotiable Goals

1. **Single dashboard truth:** all operational mutation must go through FastAPI/dashboard APIs.
2. **Durable server-side state:** browser refresh or disconnect must not lose live state.
3. **TikTok-first streaming:** stream target management must support real TikTok RTMP operation from the dashboard.
4. **Multi-product live session:** one session can preload and operate on dozens of products.
5. **Controlled AI autonomy:** AI can rotate across products, but only within the session product pool and with operator override.
6. **Q&A interruption support:** chat questions can pause rotation and route the system into an answer workflow.
7. **Strong recovery model:** incidents, commands, and degraded modes must be durable and inspectable.

---

## 4. Non-Goals

The following are intentionally out of scope for this wave:

- multi-host orchestration
- multi-operator locking
- per-user session slots
- public-facing auth inside FastAPI
- Shopee ingest automation without verified public support
- full chat-ingest automation for TikTok live comments if the target environment still needs a separate connector

---

## 5. Current Baseline and Gaps

### Existing strengths

- dashboard already acts as the main operator UI
- AI Brain runtime and prompt registry already exist
- SQLite infrastructure already exists
- product-oriented UI already exists
- stream-oriented UI already exists

### Critical gaps

- `src/stream/rtmp.py` builds RTMP publishing commands, but the dashboard does not persist stream targets or own the publisher lifecycle
- `/api/stream/start` and `/api/stream/stop` currently move director state, not the actual RTMP worker lifecycle
- `src/commerce/manager.py` still hydrates from `data/products.json` into memory instead of using durable CRUD
- important affiliate/compliance fields are not fully preserved from JSON into runtime state
- there is no durable `live_session` state model
- there is no durable `session_products` model
- there is no durable `current_focus_product` state
- the stream panel still exposes RTMP draft fields that are not source-of-truth data

---

## 6. Architecture Options

### Option A: Thin dashboard over env + JSON + in-memory state

- Fast to patch
- Keeps current architecture mostly intact
- Fails the source-of-truth requirement

### Option B (Chosen): Dashboard control plane + SQLite state store + in-process runtime coordinator

- FastAPI owns all operator mutations
- SQLite stores durable operational state
- runtime coordinator and RTMP publisher run on the same host
- simplest model that still satisfies the 18-hour single-host requirement

### Option C: Separate runtime daemon + controller API

- Stronger future operational separation
- Adds complexity too early for the current stage

**Decision:** adopt **Option B**.

---

## 7. Chosen Architecture

### 7.1 Control Plane

FastAPI + `/dashboard` becomes the only official control plane for:

- product catalog CRUD
- live session lifecycle
- stream target CRUD and validation
- session product pool
- current focus product
- rotation mode and Q&A pause state
- operator commands
- incidents and recovery receipts

### 7.2 State Plane

SQLite becomes the durable state store for:

- product catalog
- stream targets
- live sessions
- session products
- session runtime state
- operator command journal
- runtime events and incidents

### 7.3 Runtime Plane

Runtime-critical execution still happens on the same host:

- AI Brain routing
- voice engine
- face engine
- RTMP/ffmpeg publisher
- rotation/Q&A coordinator

But none of those components are allowed to become the source of truth. They read and report against server-side controller state.

---

## 8. Domain Model

### 8.1 Product Catalog

`products` remains the master catalog across sessions.

Each product must be able to store:

- core identity and description
- price
- category
- stock
- margin
- selling points
- affiliate links by platform
- commission rate
- objection handling
- compliance notes
- active/archive state

### 8.2 Live Session

There is exactly one active session on the host at a time.

`live_sessions` stores:

- platform
- status
- started_at / ended_at
- stream_target_id
- rotation_mode
- qna_mode
- pause_reason
- operator notes

### 8.3 Session Products

One live session can include many products.

`session_products` stores:

- session_id
- product_id
- queue_order
- enabled_for_rotation
- operator_priority
- ai_score
- cooldown_until
- last_pitched_at
- times_pitched
- last_question_at
- runtime state flags

### 8.4 Session Runtime State

`session_state` stores the single authoritative runtime snapshot:

- current mode
- current phase
- rotation paused flag
- pause reason
- current_focus_product_id
- pending question metadata
- awaiting_operator flag
- active prompt revision
- active provider/model
- stream status

### 8.5 Stream Targets

`stream_targets` stores durable, operator-managed stream destinations:

- platform
- label
- rtmp_url
- stream_key_ref or stream_key_value for local-host protected storage
- enabled flag
- validation state
- validation evidence
- last_validated_at

For this wave, TikTok is first-class. Shopee may exist as a disabled/manual companion record, but not as a first-class automated runtime until public support is verified for the target operating environment.

---

## 9. Rotation and Focus Model

The live can carry many products, but the runtime still needs coherence. The approved model is:

- many `session_products`
- one `current_focus_product` at a time
- operator-assisted rotation

That means:

- AI can propose and select from the eligible session pool
- rotation policy enforces cooldown and queue discipline
- operator can `pin`, `skip`, `boost`, `disable`, `pause`, or `switch`
- script generation, CTA, and chat answers stay grounded in the current focus unless a question clearly points to another product in the active session

---

## 10. Q&A Interrupt Model

The runtime must support long-form selling plus chat interruption without losing control.

### Runtime modes

- `ROTATING`
- `SOFT_PAUSED_FOR_QNA`
- `ANSWERING`
- `AWAITING_OPERATOR`
- `MANUAL_PAUSED`
- `RESUMING`

### Interrupt rules

- purchase, price, stock, shipping, voucher, and product questions can pause rotation
- spam or low-value reactions do not pause rotation
- after the answer, the coordinator either returns to the previous focus or switches focus to a more relevant session product

### Guardrails

AI may answer:

- about the current focus product
- about another product that exists inside the current session
- about store policy and operations

AI must not hallucinate outside known product or store policy data. Sensitive or compliance-heavy topics must either use safe templates or enter `AWAITING_OPERATOR`.

---

## 11. Error Handling and Recovery Model

This design treats failures as first-class state, not just log output.

### Failure classes

- `validation_error`
- `state_conflict`
- `runtime_dependency_failure`
- `degraded_ai_mode`
- `storage_failure`
- `policy_block`
- `operator_required`

### Recovery mechanisms

- command journal with durable receipts
- incident registry with severity and ack status
- component heartbeats
- idempotent operator commands
- bounded retries and reconnect logic for RTMP
- safe fallback AI responses
- restart recovery from SQLite-backed session state

### Recovery principles

- browser disconnect never owns runtime lifecycle
- stream failure does not erase session state
- AI failure degrades gracefully instead of crashing the session
- no action result is ambiguous; each command must return `accepted`, `completed`, `blocked`, `rejected`, or `degraded`

---

## 12. API Surface Changes

The dashboard will shift from ad-hoc endpoints to controller-owned resources.

### Product APIs

- `GET /api/products`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`

### Stream Target APIs

- `GET /api/stream-targets`
- `POST /api/stream-targets`
- `PUT /api/stream-targets/{id}`
- `POST /api/stream-targets/{id}/validate`
- `POST /api/stream-targets/{id}/activate`

### Session APIs

- `GET /api/live-session`
- `POST /api/live-session/start`
- `POST /api/live-session/stop`
- `POST /api/live-session/products`
- `DELETE /api/live-session/products/{session_product_id}`
- `POST /api/live-session/focus`
- `POST /api/live-session/pause`
- `POST /api/live-session/resume`

### Existing stream endpoints

`/api/stream/start` and `/api/stream/stop` will become controller-backed session actions instead of thin director toggles.

---

## 13. Dashboard UI Evolution

### Products panel

The products panel must evolve from:

- one active product + queue viewer

to:

- catalog CRUD
- session assignment
- focus control
- queue and candidate visibility
- compliance and affiliate metadata editing

### Stream panel

The stream panel must evolve from:

- draft RTMP fields in the browser

to:

- durable stream target management
- activation and validation
- live session start/stop
- RTMP validation evidence
- reconnect/degraded state visibility

### Live console

The live console must become the owner of:

- session status
- runtime mode
- current focus
- pause reason
- operator overrides
- command receipts

---

## 14. Persistence Rules

- `.env` remains bootstrap-only for host defaults and secrets
- `data/products.json` becomes seed/import input, not runtime source of truth
- SQLite is the runtime source of truth
- browser state is only a temporary view layer

---

## 15. Deployment Implications

This design intentionally supports the previously chosen security boundary:

- reverse proxy auth
- TLS termination
- server-hosted dashboard
- single GPU host

Because the dashboard owns all operational state, the future move to per-user slots or multi-session tenancy becomes a database and scheduling extension instead of a rewrite.

---

## 16. Acceptance Criteria

The design is considered implemented when:

1. dashboard-managed stream targets can be created, validated, and activated for TikTok
2. one live session can be started from the dashboard and survive browser refresh
3. products are stored and mutated in SQLite instead of in-memory JSON-only state
4. one session can load dozens of products
5. a current focus product can be switched explicitly
6. session pause/resume state is durable
7. operator commands and incidents are stored durably
8. dashboard panels read from controller APIs, not browser-only draft state

