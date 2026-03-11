# Brain Director Runtime Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace dashboard-global pipeline state with a persistent `ShowDirector`, move hardcoded persona prompts into a versioned `PromptRegistry`, expose a unified runtime contract to the UI, and tighten the shell layout so the content stays centered while the sidebar remains fixed.

**Architecture:** Introduce backend-first services (`ShowDirector`, `PromptRegistry`) and refactor API/truth assembly to consume them. Then surface the new runtime contract in `SetupPage` and `LiveConsolePage`, while updating the app shell layout so panels are centered, full-width, responsive, and the sidebar does not drift.

**Tech Stack:** FastAPI, SQLite, Svelte 5, Vitest, Pytest, Playwright

---

### Task 1: Add ShowDirector Service

**Files:**
- Create: `src/orchestrator/show_director.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - `ShowDirector().get_runtime_snapshot()` returns `state=IDLE`
  - transition history is stored
  - emergency stop flips state to `STOPPED`
  - singleton getter returns the same instance

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "show_director"`
Expected: FAIL because `show_director.py` does not exist yet

**Step 3: Write minimal implementation**
- Implement `ShowDirector`
- Add singleton getter
- Add `transition`, `emergency_stop`, `reset_emergency`, `get_runtime_snapshot`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "show_director"`
Expected: PASS

### Task 2: Add PromptRegistry

**Files:**
- Create: `src/brain/prompt_registry.py`
- Modify: `tests/test_brain.py`
- Modify: `src/data/database.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - registry bootstraps a default active prompt pack
  - default pack is versioned
  - active prompt contains selling/reacting/engaging/filler templates

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_brain.py -q -p no:cacheprovider -k "prompt_registry"`
Expected: FAIL because registry module does not exist yet

**Step 3: Write minimal implementation**
- Add prompt registry service backed by SQLite
- Ensure schema bootstrap for prompt tables
- Provide default active revision

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_brain.py -q -p no:cacheprovider -k "prompt_registry"`
Expected: PASS

### Task 3: Refactor PersonaEngine to Use PromptRegistry

**Files:**
- Modify: `src/brain/persona.py`
- Modify: `tests/test_brain.py`

**Step 1: Write the failing test**
- Add tests asserting persona prompts still contain expected context but now come from registry-backed templates

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_brain.py -q -p no:cacheprovider -k "persona"`
Expected: FAIL due to old hardcoded behavior

**Step 3: Write minimal implementation**
- Keep public API stable
- Move literals into registry templates
- Inject placeholders at render time

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_brain.py -q -p no:cacheprovider -k "persona"`
Expected: PASS

### Task 4: Refactor Dashboard API and Truth Contract

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/truth.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**
- Add tests asserting:
  - `/api/pipeline/state` reads from `ShowDirector`
  - `/api/pipeline/transition` updates director history
  - `/api/director/runtime` exposes director + prompt + brain runtime metadata
  - `/api/runtime/truth` no longer depends on private API globals for stream state

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "director_runtime or pipeline_state"`
Expected: FAIL

**Step 3: Write minimal implementation**
- Replace private pipeline globals with `ShowDirector`
- Extend `brain/config`
- Add `director/runtime`
- Update websocket snapshot fields

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "director_runtime or pipeline_state"`
Expected: PASS

### Task 5: Add Frontend Brain/Director Runtime Surfaces

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/BrainPromptPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/DirectorRuntimePanel.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/pages/SetupPage.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte`
- Modify: `src/dashboard/frontend/src/tests/setup-page.test.ts`
- Modify: `src/dashboard/frontend/src/tests/live-console-panel.test.ts`

**Step 1: Write the failing test**
- Setup page test should assert active prompt pack and routing/provider cards render
- Live console test should assert director runtime cards and phase state render

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/setup-page.test.ts src/tests/live-console-panel.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**
- Add typed API wrappers
- Render read-only runtime surfaces
- Include loading/error/empty states

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/setup-page.test.ts src/tests/live-console-panel.test.ts`
Expected: PASS

### Task 6: Stabilize App Shell Layout

**Files:**
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `src/dashboard/frontend/src/app.css`
- Modify: `src/dashboard/frontend/src/pages/SetupPage.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte`
- Modify: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write the failing test**
- Add assertions for fixed sidebar class hooks and centered content container hooks

**Step 2: Run test to verify it fails**

Run: `npm run test -- src/tests/App.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**
- Keep sidebar fixed/sticky with non-shifting width
- Add centered max-width content wrapper
- Make primary pages use full responsive box layout

**Step 4: Run test to verify it passes**

Run: `npm run test -- src/tests/App.test.ts`
Expected: PASS

### Task 7: Verify End-to-End

**Files:**
- Modify if needed: `src/dashboard/frontend/e2e/dashboard.spec.ts`

**Step 1: Run targeted backend and frontend verification**

Run:
- `uv run pytest tests/test_dashboard.py tests/test_brain.py -q -p no:cacheprovider`
- `cd src/dashboard/frontend && npm run test -- src/tests/App.test.ts src/tests/setup-page.test.ts src/tests/live-console-panel.test.ts`

Expected: PASS

**Step 2: Run build**

Run: `cd src/dashboard/frontend && npm run build`
Expected: PASS

**Step 3: Run browser validation**

Run: `cd src/dashboard/frontend && npm run test:e2e -- e2e/dashboard.spec.ts`
Expected: PASS with sidebar stable and new runtime surfaces visible
