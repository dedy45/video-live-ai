# Voice Lab Two-Mode Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a dashboard-hosted Voice Lab with `Standalone Fish TTS` and `Attach ke Avatar/MuseTalk` modes that can generate audio from web prompts and hand off audio to LiveTalking.

**Architecture:** Add durable SQLite tables and control-plane store methods for voice profiles, lab state, and generations. Expose thin FastAPI endpoints in `src/dashboard/api.py`, then upgrade the `Suara` tab into a two-mode workspace that drives those endpoints.

**Tech Stack:** FastAPI, SQLite, Svelte 5, Vitest, pytest, local Fish-Speech sidecar, LiveTalking sidecar.

---

### Task 1: Voice Lab Schema And Store

**Files:**
- Modify: `src/data/schema.sql`
- Modify: `src/control_plane/store.py`
- Test: `tests/test_control_plane.py`

**Step 1: Write the failing test**

Add tests for:
- profile CRUD round-trip
- lab state update/read
- generation history insert/read

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_control_plane.py -q -p no:cacheprovider`

Expected: FAIL because voice-lab methods/tables do not exist.

**Step 3: Write minimal implementation**

Add:
- `voice_profiles`
- `voice_lab_state`
- `voice_generations`

Implement store methods:
- `list_voice_profiles`
- `create_voice_profile`
- `update_voice_profile`
- `delete_voice_profile`
- `activate_voice_profile`
- `get_voice_lab_state`
- `update_voice_lab_state`
- `create_voice_generation`
- `list_voice_generations`
- `get_voice_generation`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_control_plane.py -q -p no:cacheprovider`

Expected: PASS for the new store tests.

### Task 2: Voice Lab API Backend

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for:
- `GET /api/voice/profiles`
- `POST /api/voice/profiles`
- `PUT /api/voice/lab`
- `POST /api/voice/generate` standalone
- `POST /api/voice/generate` attach blocked when avatar/session missing

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL because endpoints and request models do not exist.

**Step 3: Write minimal implementation**

Add request models and endpoints that call the store. Persist audio files under:

- `data/runtime/voice/`

Use Fish-Speech client directly for profile-specific reference audio/text.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS for new endpoint tests.

### Task 3: Avatar Attach Handoff

**Files:**
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for:
- saving preview session id
- attach mode uploading audio to LiveTalking `/humanaudio`

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL because attach handoff is not wired.

**Step 3: Write minimal implementation**

Implement:
- `POST /api/voice/lab/preview-session`
- attach path in `POST /api/voice/generate`

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS.

### Task 4: Voice Lab Frontend

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/VoicePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/voice-panel.test.ts`

**Step 1: Write the failing test**

Add tests for:
- mode switch
- profile list rendering
- standalone generate action
- attach mode status rendering
- history/result rendering

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/tests/voice-panel.test.ts`

Expected: FAIL because UI does not expose the new controls.

**Step 3: Write minimal implementation**

Upgrade `VoicePanel` into a Voice Lab workspace that:
- switches mode
- lists profiles
- triggers generate
- renders audio history/result
- shows attach session state

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/tests/voice-panel.test.ts`

Expected: PASS.

### Task 5: Verification And Docs

**Files:**
- Modify: `docs/operations/livetiktokubuntu.md`
- Modify: `README.md`
- Modify: `docs/task_status.md`

**Step 1: Run backend verification**

Run: `uv run pytest tests/test_control_plane.py tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS.

**Step 2: Run frontend verification**

Run: `npm test -- --run src/tests/voice-panel.test.ts`

Expected: PASS.

**Step 3: Run build**

Run: `npm run build`

Expected: PASS.

**Step 4: Browser smoke**

Check:
- `/dashboard/#/performer`
- tab `Suara`
- standalone generate works
- attach mode blocks or attaches correctly

**Step 5: Commit**

```bash
git add docs/plans/2026-03-14-voice-lab-two-mode-design.md docs/plans/2026-03-14-voice-lab-two-mode-implementation.md src/data/schema.sql src/control_plane/store.py src/dashboard/api.py src/dashboard/frontend/src/components/panels/VoicePanel.svelte src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/lib/api.ts tests/test_control_plane.py tests/test_dashboard.py src/dashboard/frontend/src/tests/voice-panel.test.ts docs/operations/livetiktokubuntu.md README.md docs/task_status.md
git commit -m "feat: add two-mode voice lab"
```
