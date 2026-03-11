# Frontend Pages Realignment Design

**Date:** 2026-03-11
**Status:** Approved for implementation

## Goal

Realign the Svelte operator frontend so `/dashboard` remains the main operator shell while standalone pages such as `performer.html`, `monitor.html`, `stream.html`, `validation.html`, `diagnostics.html`, and `products.html` remain fully functional and share the same truth contract, action model, and realtime behavior.

## Decisions

### 1. Dual entrypoint model stays

- `/dashboard` remains the primary operator UI.
- Standalone pages remain first-class frontend entrypoints for focused debugging and future feature growth.
- Standalone pages are not vendor pages and must stay aligned with the same operator backend contracts.

### 2. One frontend data contract

- Panels and pages must not read backend payloads ad hoc.
- Shared frontend adapters/stores under `src/dashboard/frontend/src/lib/` normalize backend payloads into stable UI shapes.
- Contract drift is fixed once in shared code, not separately in each page.

### 3. No browser persistence for runtime state

- No runtime truth, health state, or operator state may be restored from `localStorage`, `sessionStorage`, `IndexedDB`, or service workers.
- Store state is in-memory only for the lifetime of the tab.
- Reload must clear in-memory state and re-bootstrap from backend endpoints.

### 4. Fresh data policy

- Frontend requests for operator state must opt into no-cache fetch behavior.
- Realtime fallback polling must also fetch fresh data and must not reuse stale browser state.
- Backend operator responses should expose `Cache-Control: no-store, no-cache, must-revalidate`.

### 5. Realtime policy

- Page bootstrap performs a fresh API load on mount.
- After bootstrap, the page subscribes to WebSocket realtime updates.
- If WebSocket disconnects, fallback polling continues with fresh requests only.
- Realtime payload shape should be normalized so pages do not depend on transport-specific quirks.

## Known root causes confirmed before implementation

1. `PerformerPanel.svelte` reads face-engine fields that no longer exist in the current runtime truth contract.
2. `MonitorPanel.svelte` depends partly on realtime-only health fields, but polling fallback does not provide equivalent health payloads.
3. Existing standalone entries and shell pages do not consistently share one bootstrap/realtime flow.
4. The API layer does not explicitly enforce no-cache fetch semantics.

## Implementation direction

- Add shared runtime bootstrap helpers for fresh fetches.
- Normalize realtime snapshots to include consistent truth and health payloads.
- Refactor standalone pages and `/dashboard` pages to consume the same shared data sources.
- Fix broken panels one by one starting with `Performer` and `Monitor`.
- Add regression tests for no-cache fetch options, contract normalization, and repaired page behavior.
