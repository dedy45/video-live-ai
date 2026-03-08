# FFmpeg and MuseTalk Normalization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Normalize local FFmpeg installation and MuseTalk asset setup so Windows local runtime matches the canonical vendor path contract and remains portable to Ubuntu.

**Architecture:** FFmpeg becomes a project-local runtime dependency discoverable through explicit env vars and a shared resolver. MuseTalk assets remain canonical under `external/livetalking/`; setup scripts only sync legacy root assets or prepare generation from user-provided reference media.

**Tech Stack:** Python 3.12, UV, PowerShell, GitHub release download API, Hugging Face client, LiveTalking vendor tools.

---

### Task 1: FFmpeg Resolver Hardening

**Files:**
- Modify: `src/utils/ffmpeg.py`
- Modify: `src/dashboard/api.py`
- Modify: `src/composition/compositor.py`
- Test: `tests/test_engine_resolver.py`

**Step 1: Write the failing test**

Add tests for:
- `FFMPEG_BIN` explicit file path
- `FFMPEG_DIR` directory path
- project-local `tools/ffmpeg/bin/ffmpeg(.exe)` fallback

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_engine_resolver.py -q -p no:cacheprovider`

**Step 3: Write minimal implementation**

Update FFmpeg resolver to check:
1. `FFMPEG_BIN`
2. `FFMPEG_DIR`
3. project-local `tools/ffmpeg/bin`
4. PATH
5. known platform locations

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_engine_resolver.py -q -p no:cacheprovider`

### Task 2: MuseTalk Asset Normalization Helper

**Files:**
- Create: `src/face/asset_setup.py`
- Test: `tests/test_asset_setup.py`

**Step 1: Write the failing test**

Add tests for:
- syncing `models/musetalk` into `external/livetalking/models/musetalk`
- syncing `data/avatars/musetalk_avatar1` into vendor avatar path
- reporting missing `assets/avatar/reference.mp4` when avatar generation is impossible

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider`

**Step 3: Write minimal implementation**

Implement a small helper that:
- knows canonical vendor paths
- copies legacy root assets if present
- returns a status report for models, avatar, and reference media

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider`

### Task 3: Setup Scripts and Runtime Checks

**Files:**
- Create: `scripts/setup_ffmpeg.py`
- Create: `scripts/setup_musetalk_assets.py`
- Modify: `scripts/setup_livetalking.py`
- Modify: `scripts/smoke_livetalking.py`
- Modify: `.env.example`
- Modify: `.gitignore`

**Step 1: Write the failing test**

Add focused tests for helper functions used by setup scripts.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_asset_setup.py tests/test_engine_resolver.py -q -p no:cacheprovider`

**Step 3: Write minimal implementation**

- `setup_ffmpeg.py` downloads/extracts project-local FFmpeg and writes `FFMPEG_BIN` into `.env`
- `setup_musetalk_assets.py` syncs legacy assets and optionally prepares avatar generation
- `setup_livetalking.py` points to canonical vendor paths and delegates to new helpers
- `smoke_livetalking.py` reports requested vs resolved runtime

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_asset_setup.py tests/test_engine_resolver.py tests/test_livetalking_integration.py -q -p no:cacheprovider`

### Task 4: Real Validation and Docs

**Files:**
- Modify: `docs/workflow.md`
- Modify: `docs/task_status.md`
- Modify: `docs/changelogs.md`

**Step 1: Run real setup commands**

Run:
- `uv run python scripts/setup_ffmpeg.py`
- `uv run python scripts/setup_musetalk_assets.py --sync-only`

**Step 2: Verify runtime**

Run:
- `uv run python scripts/verify_pipeline.py`
- `uv run python scripts/smoke_livetalking.py`
- `uv run python -c "from src.dashboard.readiness import run_readiness_checks; import json; print(json.dumps(run_readiness_checks().to_dict(), indent=2))"`

**Step 3: Update docs**

Document:
- canonical FFmpeg install path
- MuseTalk canonical vendor paths
- current missing external prerequisites if any

**Step 4: Final verification**

Run: `uv run pytest tests -q -p no:cacheprovider`
