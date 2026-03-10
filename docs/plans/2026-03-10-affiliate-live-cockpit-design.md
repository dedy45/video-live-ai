# Affiliate Live Cockpit Design

**Status:** Proposed and aligned for implementation planning
**Date:** 2026-03-10
**Audience:** operator, reviewer, coding agent
**Scope:** evolve the server-hosted dashboard from an operations controller into a unified affiliate live cockpit that combines sales assistance, operator controls, validation, and runtime monitoring for TikTok and Shopee live commerce.

---

## 1. Problem Statement

The current dashboard is already stronger than the previous local shell:

- it has first-class surfaces for `Voice`, `Face Engine`, `Stream`, `Validation`, `Monitor`, and `Commerce`
- it exposes runtime truth, readiness, validation history, and operator receipts
- it works as a server-hosted ops controller rather than a localhost-only surface

But it is still incomplete for real affiliate live selling.

The main gap is not just missing widgets. The dashboard still behaves mostly like a technical control surface, while affiliate livestreaming requires a combined cockpit that supports:

- runtime operations
- product rotation
- affiliate offer visibility
- platform-aware talking points
- live operator guidance
- compliance-safe phrasing
- rapid recovery when voice/face/stream degrade

For affiliate live commerce, the operator does not just need to know whether Fish-Speech or RTMP are healthy. They need to know:

- what product is active now
- what to say next
- what CTA to use on TikTok vs Shopee
- which product should rotate next
- whether the affiliate link, commission, stock, and promo context are ready
- whether the runtime is healthy enough to keep selling without awkward silence

That means the dashboard must evolve again:

- from: server-hosted ops controller
- to: **unified affiliate live cockpit**

This is still an evolution, not a rewrite.

---

## 2. Goals

1. **One cockpit for sales + ops**: operators should not need to mentally merge a sales dashboard and a runtime dashboard.
2. **Flexible staffing**: the UI must work for one operator or two-role operation without redesign.
3. **Affiliate-first product flow**: products must carry selling context, affiliate link readiness, commission context, and rotation state.
4. **Live usability**: the most common live actions must be executable without tab-hopping across technical screens.
5. **Platform awareness**: TikTok and Shopee must be modeled explicitly where stream targets, CTA copy, or product links differ.
6. **Honest runtime truth**: the UI must never imply readiness or normality when validation or subsystem health says otherwise.
7. **Progressive rollout**: the cockpit should be deliverable in phases without blocking current operator use.

---

## 3. Non-Goals

The following remain out of scope for this design:

- full autonomous sales-agent orchestration
- multi-tenant seller management
- marketplace order ingestion from official APIs in this phase
- replacing FastAPI or Svelte
- building a generic CRM inside the dashboard
- implementing complete BI/reporting beyond operator needs

---

## 4. Key UX Findings from Current State

The reviewed UX analysis in `docs/ide/ux.md` is directionally correct and should be treated as grounded operator feedback.

### 4.1 Current strengths

- `Overview` already gives fast operational orientation.
- `Voice`, `Face Engine`, and `Validation` are substantially better than the earlier UI.
- The current operator guidance path is good for non-technical use.
- Validation surfaces are among the most complete and trustworthy parts of the dashboard.

### 4.2 Current weaknesses

- the UI is still **tab-centric**, not **workflow-centric**
- Commerce is too minimal for affiliate selling
- there is no strong inline script assistance
- TikTok/Shopee platform context is not explicit enough
- some critical runtime information is hidden or too passive
- Diagnostics is still broken in the frontend despite rich backend data
- RTMP target management is not operator-friendly yet
- “current product” is visible, but not operationally rich enough

### 4.3 Structural gap

The dashboard currently answers:
- “is the system healthy?”

But during real affiliate live operation, the operator also needs the dashboard to answer:
- “what am I selling right now?”
- “what should I say next?”
- “what should rotate next?”
- “which platform am I speaking for?”
- “what is broken and how do I recover without losing flow?”

---

## 5. Recommended Architecture Option

### Option A: Keep current tabs and enrich them heavily
- Pros: smallest structural change
- Cons: risks becoming crowded and incoherent

### Option B: Split into separate sales and ops dashboards
- Pros: clean conceptual separation
- Cons: wrong for flexible staffing; too much context switching

### Option C (Recommended): Unified dual-mode cockpit
- Keep one dashboard
- Reorganize around live workflow
- Preserve deep technical panels behind the same shell
- Support both solo operator mode and split-role operation

**Decision:** adopt **Option C**.

---

## 6. Information Architecture

The dashboard should be reorganized into seven primary surfaces.

### 6.1 Live Console
The main operator workspace during an active session.

Contains:
- current product card
- live script rail
- next best line / next action suggestions
- active CTA block
- quick voice test
- quick product switch
- mini stream posture
- mini voice/face posture
- critical alerts

Purpose:
- minimize tab switching during live operation
- support one-person operation

### 6.2 Products & Offers
The affiliate commerce workspace.

Contains:
- active product
- product queue
- reorder controls
- platform-specific affiliate links
- commission context
- promo/discount context
- stock/campaign status
- product talking points
- objection-handling snippets
- auto-rotate controls

Purpose:
- make affiliate product flow operational, not just informational

### 6.3 Voice & Face
The performer control surface.

Contains:
- voice warmup and truth
- inline test speak
- clone smoke shortcut
- sidecar reachability badge
- face engine start/stop
- preview thumbnail
- FPS and latency visibility
- fallback state visibility

Purpose:
- let operator verify performer output quickly without leaving the main cockpit for every action

### 6.4 Stream & Platform
The platform delivery surface.

Contains:
- TikTok target config
- Shopee target config
- active target state
- bitrate / drops / duration
- active pipeline highlight
- emergency stop and recovery actions
- stream validation actions

Purpose:
- make platform delivery operator-friendly and explicit

### 6.5 Validation & Readiness
The preflight and recovery confidence surface.

Contains:
- readiness summary
- run all checks
- grouped validation gates
- auto-refresh or auto-run on entry
- recent validation history
- expandable failure detail

Purpose:
- keep the go/no-go path honest and fast

### 6.6 Monitor & Incidents
The long-run observability surface.

Contains:
- all relevant component health
- CPU / RAM / Disk / VRAM / upload throughput
- recent incidents
- open incidents
- recent chat stream
- long-run degradation warnings

Purpose:
- support multi-hour operation and recovery

### 6.7 Diagnostics
The deep debugging surface.

Contains:
- raw component state
- system info
- backend diagnostic payloads
- structured debug summaries

Purpose:
- give technical depth without cluttering the operator workspace

---

## 7. Flexible Staffing Model

The cockpit must support three real-world modes with the same UI:

### Solo operator
One person handles:
- speaking flow
- product switching
- voice/face checks
- stream confirmation

Design implication:
- Live Console must expose the highest-frequency controls inline.

### Split-role operation
Two people divide work:
- sales operator uses Live Console + Products & Offers
- ops operator uses Voice & Face + Stream & Platform + Monitor

Design implication:
- each surface must stand on its own without hidden dependencies.

### Mixed mode
The workflow changes by session.

Design implication:
- avoid role-locked navigation
- keep the same truth model and action model across all surfaces

---

## 8. Product Data Model Expansion

The current product model is too thin for affiliate live operation.

### Current model
- `id`
- `name`
- `price`
- `price_formatted`
- `category`
- `is_active`

### Required expanded model
Each product should eventually support at least:

- `id`
- `name`
- `category`
- `image_url`
- `description`
- `selling_points: string[]`
- `host_talking_points: string[]`
- `cta_lines: string[]`
- `objection_answers: { [key: string]: string }`
- `original_price`
- `discount_price`
- `price_formatted`
- `discount_badge`
- `commission_rate`
- `commission_amount_estimate`
- `affiliate_links: { tiktok?: string, shopee?: string }`
- `platform_availability: { tiktok: boolean, shopee: boolean }`
- `stock_status`
- `campaign_end`
- `compliance_notes: string[]`
- `queue_position`
- `rotation_enabled`
- `target_duration_sec`

### Why this matters
Without these fields, the dashboard cannot:
- render a useful affiliate queue
- show platform-ready CTA lines
- support truthful product scripting
- prioritize high-value offers
- avoid unsafe product claims

---

## 9. Core Interaction Design

### 9.1 Live script rail
A persistent section in Live Console that shows:
- opening hook
- current pitch block
- proof/benefit line
- urgency line
- CTA line
- fallback alternative line

Operator actions:
- copy line
- mark as used
- shuffle variation
- pin line

### 9.2 Next best action rail
A compact guidance area that always answers:
- what to say next
- what to check next
- what blocker exists now

Examples:
- “Voice ready, switch to next product in 90s”
- “Run RTMP validation before going live”
- “Shopee link missing for active product”

### 9.3 Product queue
The queue must support:
- active product highlight
- next product visibility
- reorder controls
- per-product timer
- auto-rotate toggle
- skip / next / pin

### 9.4 Quick test interactions
Operators need inline tests for:
- voice speak test
- face preview health
- RTMP target validity
- product script preview

### 9.5 Alert semantics
A single truth rule must apply:
- if readiness is degraded, top-level alert cannot say normal
- if voice sidecar is unreachable, voice surface must show warning prominently
- if a platform target is invalid, Live Console must surface a visible blocker

---

## 10. Panel-by-Panel Improvements

### Overview → absorb into Live Console orientation
Keep:
- top-level posture
- operator alert
- recommended path

Change:
- make status colors semantic
- align operator alert with readiness truth
- enrich current product block with commission and time-on-product

### Voice
Add:
- inline test speak
- explicit sidecar badge
- better surfaced warning state
- quick clone smoke launch

### Face Engine
Add:
- preview thumbnail
- VRAM / FPS / health summary
- clearer running-state feedback

### Stream
Add:
- editable target config from UI
- TikTok + Shopee target handling
- active pipeline highlight
- bitrate / drops / duration metrics

### Validation
Add:
- run all checks
- expandable failure reasons
- better linkage to top-level alerts
- optional auto-run on entry

### Monitor
Add:
- real VRAM value if available
- upload throughput
- fuller component list
- better recent chat rendering

### Commerce → evolve into Products & Offers
Add:
- active product section
- queue management
- commission-centric stats
- thumbnails
- platform link readiness
- talking points and CTA content

### Diagnostics
Fix:
- frontend rendering bug
- keep backend payload as source of truth

---

## 11. Backend Surfaces Needed

The frontend redesign requires corresponding backend evolution.

### New or expanded API needs
- expanded product model endpoint
- active product + queue state endpoint
- product reorder / rotate actions
- affiliate link readiness fields
- voice quick test endpoint or safe reuse path
- stream target config endpoints for TikTok/Shopee
- diagnostics payload compatibility fix in frontend
- richer resource metrics including VRAM and upload if available
- alert aggregation endpoint or truth-field enrichment for operator severity

### Important constraint
This should remain additive where possible. Existing truth/readiness/validation surfaces should be reused rather than replaced.

---

## 12. Documentation Impact

If this design is implemented, the documentation must stop describing the dashboard as only an ops controller.

It should instead describe the dashboard as:
- the single operator cockpit
- combining runtime control, validation, and affiliate selling assistance
- suitable for flexible single-operator or split-role workflows

Minimum docs to update:
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/changelogs.md`
- `docs/task_status.md`
- `docs/README.md`
- dashboard-specific docs if they describe outdated menu structure or operator assumptions

---

## 13. Delivery Strategy

Implement in phases.

### Phase 1: Fix truth, broken surfaces, and inline interactivity
- diagnostics render fix
- alert alignment
- run-all checks
- voice inline test
- stream active-state clarity
- active product highlighting

### Phase 2: Introduce affiliate data richness and product queue
- expanded product model
- queue management
- commission and platform context
- CTA and talking points surfaces

### Phase 3: Promote Live Console as the main cockpit
- next best action rail
- live script rail
- mini runtime posture cards
- integrated quick actions

### Phase 4: Long-run optimization
- richer metrics
- better incident workflows
- auto-rotation and session pacing
- deeper platform-specific guidance

---

## 14. Recommended Decision

Proceed with a phased implementation of the **unified affiliate live cockpit**.

This is the best fit because it:
- preserves the server-hosted ops-controller architecture already established
- adds missing affiliate-selling functionality without forcing a rewrite
- works for solo and split-role operation
- turns the dashboard into a real production cockpit rather than a set of technical tabs

---

## 15. Approval Summary

Approved direction for planning:
- combined sales assist + ops control
- flexible operator model
- workflow-centric cockpit
- affiliate-first product enrichment
- phased implementation with documentation sync at the end
