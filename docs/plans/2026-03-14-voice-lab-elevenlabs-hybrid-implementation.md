# Voice Lab ElevenLabs-Style Hybrid Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the dashboard `Suara` tab into a richer ElevenLabs-style Voice Lab with browser-visible language selection, multi-clone management, playable/downloadable outputs, and control-plane foundations for Studio Voice training jobs.

**Architecture:** Extend the existing voice control-plane instead of replacing it. Keep generation and avatar attach stable, enrich SQLite/API contracts for richer voice metadata, then rebuild the `Suara` tab into multiple sub-workspaces that expose real backend state rather than static shells.

**Tech Stack:** FastAPI, SQLite, Svelte 5, Fish-Speech sidecar, LiveTalking sidecar, Vitest, Pytest, Playwright.

---

### Task 1: Expand backend schema and state contracts

**Files:**
- Modify: `src/data/schema.sql`
- Modify: `src/control_plane/store.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_control_plane.py`

**Step 1: Write the failing test**

Add tests for:
- new `voice_lab_state` defaults include language/style/stability/similarity
- voice generations persist language + download metadata
- training jobs can be created and listed

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_control_plane.py -q -p no:cacheprovider`

Expected: FAIL on missing schema/state fields and missing training job methods.

**Step 3: Write minimal implementation**

- extend schema tables
- extend row serializers in store
- add training job CRUD helpers

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_control_plane.py -q -p no:cacheprovider`

Expected: PASS

### Task 2: Enrich voice generate and library API

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/voice/lab.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for:
- `POST /api/voice/generate` accepts language/style/stability/similarity
- `GET /api/voice/audio/{id}/download` returns attachment response
- library/generation payload includes per-item playback/download metadata

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL on missing fields/routes.

**Step 3: Write minimal implementation**

- widen request models
- persist richer metadata
- add download endpoint
- keep router thin over store + voice lab engine

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS

### Task 3: Add training-job control-plane surface

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/control_plane/store.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for:
- training job creation succeeds when live session inactive
- training job creation is blocked when live session active
- training job listing returns durable state

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL on missing route/guardrail.

**Step 3: Write minimal implementation**

- add training-job endpoints
- implement live-session guard
- persist queued jobs with honest status

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS

### Task 4: Rebuild Voice Lab frontend around sub-workspaces

**Files:**
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/components/panels/VoicePanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/voice/VoiceGenerateWorkspace.svelte`
- Create: `src/dashboard/frontend/src/components/panels/voice/VoiceCloneWorkspace.svelte`
- Create: `src/dashboard/frontend/src/components/panels/voice/VoiceStudioWorkspace.svelte`
- Create: `src/dashboard/frontend/src/components/panels/voice/VoiceLibraryWorkspace.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte`
- Test: `src/dashboard/frontend/src/tests/voice-panel.test.ts`
- Test: `src/dashboard/frontend/src/tests/performer-panel.test.ts`

**Step 1: Write the failing test**

Add frontend tests for:
- language selector and model/style controls
- informative clone requirements
- per-item play/download controls
- training job controls visibility and blocked state

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/tests/voice-panel.test.ts src/tests/performer-panel.test.ts`

Expected: FAIL on missing controls and actions.

**Step 3: Write minimal implementation**

- split Voice Lab into focused subcomponents
- wire richer API/types
- keep attach flow intact

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/tests/voice-panel.test.ts src/tests/performer-panel.test.ts`

Expected: PASS

### Task 5: Browser validation and documentation sync

**Files:**
- Modify: `README.md`
- Modify: `docs/task_status.md`
- Modify: `docs/operations/livetiktokubuntu.md`

**Step 1: Run full targeted verification**

Run:

```bash
uv run pytest tests/test_control_plane.py tests/test_dashboard.py tests/test_livetalking_integration.py -q -p no:cacheprovider
cd src/dashboard/frontend && npm test -- --run src/tests/voice-panel.test.ts src/tests/performer-panel.test.ts src/tests/performer-preview-panel.test.ts
cd src/dashboard/frontend && npm run build
```

**Step 2: Browser smoke**

Verify in browser:
- `performer.html` -> `Suara`
- standalone generation with language selection
- per-item playback/download
- attach generation still works
- training job guard shows blocked during live

**Step 3: Sync docs**

Document the actual verified Voice Lab behavior, especially:
- bilingual generation controls
- clone guidance
- downloadable artifacts
- current training-job boundary
