# Frontend Pages Realignment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Repair every operator frontend page so the main dashboard shell and standalone pages share one truthful, no-cache, realtime-safe contract with the backend.

**Architecture:** Keep the dual-entrypoint model: `/dashboard` remains the primary shell, while standalone HTML pages remain fully functional. Centralize fetch, bootstrap, realtime normalization, and truth-contract mapping in shared frontend library code so panels stop drifting from backend payloads.

**Tech Stack:** Svelte 5, Vite, Vitest, Playwright, FastAPI

---

### Task 1: Lock the no-cache frontend request policy

**Files:**
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/api.test.ts`

**Step 1: Write the failing test**

Add a test proving operator fetch calls use request options that disable browser caching.

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/api.test.ts`
Expected: FAIL because current fetch options do not enforce `cache: 'no-store'`.

**Step 3: Write minimal implementation**

Update the shared request helper in `src/lib/api.ts` to send:
- `cache: 'no-store'`
- `Cache-Control: no-cache`
- `Pragma: no-cache`

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/api.test.ts`
Expected: PASS

### Task 2: Add shared runtime bootstrap and snapshot normalization

**Files:**
- Create: `src/dashboard/frontend/src/lib/runtime-client.ts`
- Modify: `src/dashboard/frontend/src/lib/realtime.ts`
- Test: `src/dashboard/frontend/src/tests/runtime-client.test.ts`

**Step 1: Write the failing test**

Add tests proving:
- bootstrap fetches fresh status, truth, and health data
- polling fallback emits a normalized snapshot with the same required fields as websocket mode

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/runtime-client.test.ts`
Expected: FAIL because the shared runtime client does not exist yet.

**Step 3: Write minimal implementation**

Create shared helpers to:
- bootstrap page state from API
- merge status, truth, and health into one snapshot
- keep realtime source markers stable across websocket and polling

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/runtime-client.test.ts`
Expected: PASS

### Task 3: Repair Performer page against the current truth contract

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/PerformerPanel.svelte`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Test: `src/dashboard/frontend/src/tests/performer-panel.test.ts`

**Step 1: Write the failing test**

Update the performer test to use the current backend truth shape and assert the page renders truthful face and voice runtime details without relying on removed fields.

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/performer-panel.test.ts`
Expected: FAIL because current component still reads removed face-engine fields.

**Step 3: Write minimal implementation**

Refactor `PerformerPanel.svelte` to:
- use current `face_engine` fields (`requested_model`, `resolved_model`, `requested_avatar_id`, `resolved_avatar_id`, `engine_state`, `fallback_active`)
- use current `voice_engine` fields consistently
- show truthful readiness derived from existing contract only
- keep loading, error, and empty states explicit

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/performer-panel.test.ts`
Expected: PASS

### Task 4: Repair Monitor page realtime and fallback behavior

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- Modify: `src/dashboard/frontend/src/lib/stores/dashboard.svelte.ts`
- Test: `src/dashboard/frontend/src/tests/monitor-panel.test.ts`

**Step 1: Write the failing test**

Add tests proving Monitor still shows health/resource/incidents data when websocket is absent and polling fallback is active.

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/monitor-panel.test.ts`
Expected: FAIL because there is no monitor regression test and current realtime flow is inconsistent.

**Step 3: Write minimal implementation**

Update Monitor and the shared store flow to:
- consume normalized runtime bootstrap data
- merge realtime health updates without depending on websocket-only fields
- avoid stale state across remount/reload

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/monitor-panel.test.ts`
Expected: PASS

### Task 5: Realign standalone page entrypoints with shared shell behavior

**Files:**
- Modify: `src/dashboard/frontend/src/pages/PerformerPage.svelte`
- Modify: `src/dashboard/frontend/src/pages/MonitorPage.svelte`
- Modify: `src/dashboard/frontend/src/pages/StreamPage.svelte`
- Modify: `src/dashboard/frontend/src/pages/ValidationPage.svelte`
- Modify: `src/dashboard/frontend/src/pages/DiagnosticsPage.svelte`
- Modify: `src/dashboard/frontend/src/pages/ProductsPage.svelte`
- Modify: `src/dashboard/frontend/src/entries/performer.ts`
- Modify: `src/dashboard/frontend/src/entries/monitor.ts`
- Modify: `src/dashboard/frontend/src/entries/stream.ts`
- Modify: `src/dashboard/frontend/src/entries/validation.ts`
- Modify: `src/dashboard/frontend/src/entries/products.ts`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write the failing test**

Add tests verifying standalone entries render the same operator panels cleanly and do not depend on browser-persisted state.

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/App.test.ts`
Expected: FAIL on missing shared wrapper expectations or stale assumptions.

**Step 3: Write minimal implementation**

Make standalone entries use shared wrapper/layout/bootstrap behavior where needed, while preserving focused debugging pages.

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/App.test.ts`
Expected: PASS

### Task 6: Enforce backend no-store headers on operator endpoints

**Files:**
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add backend tests proving critical operator endpoints emit cache-prevention headers.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`
Expected: FAIL because headers are not enforced yet.

**Step 3: Write minimal implementation**

Add a reusable no-store response policy for key operator endpoints such as:
- `/api/status`
- `/api/metrics`
- `/api/runtime/truth`
- `/api/health/summary`
- `/api/resources`
- `/api/ops/summary`
- `/api/incidents`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`
Expected: PASS

### Task 7: Full regression verification

**Files:**
- Modify as needed from prior tasks

**Step 1: Run focused frontend tests**

Run: `npm run test -- src/tests/api.test.ts src/tests/runtime-client.test.ts src/tests/performer-panel.test.ts src/tests/monitor-panel.test.ts src/tests/App.test.ts`
Expected: PASS

**Step 2: Run full frontend test suite**

Run: `npm run test`
Expected: PASS

**Step 3: Run frontend build**

Run: `npm run build`
Expected: PASS

**Step 4: Run relevant backend tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`
Expected: PASS
