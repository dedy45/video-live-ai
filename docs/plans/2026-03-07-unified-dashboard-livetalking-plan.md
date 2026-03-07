# Unified Dashboard and LiveTalking Stabilization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Menyatukan `videoliveai` dan `external/livetalking` menjadi satu sistem internal yang bisa dikontrol dari satu dashboard Svelte ringan, dengan prioritas utama validasi operasional dan jalur live yang stabil.

**Architecture:** `videoliveai` tetap menjadi orchestrator FastAPI utama. `external/livetalking` diperlakukan sebagai sidecar engine untuk rendering wajah/preview/RTMP. Dashboard tunggal berada di `src/dashboard`, menggantikan HTML statis lama dengan frontend Svelte yang tetap disajikan oleh FastAPI. Halaman vendor LiveTalking tetap dipertahankan hanya untuk debug engine, bukan sebagai dashboard operator utama.

**Tech Stack:** Python 3.12, FastAPI, **UV-only** environment management, SQLite, structlog, Svelte static build, LiveTalking vendor app, FFmpeg, PyTorch, Windows batch scripts, Ubuntu server target.

---

## Working assumptions

- Scope saat ini adalah **internal system first**, bukan SaaS multi-user.
- Dashboard utama tetap berada di jalur `/dashboard` milik FastAPI.
- `external/livetalking` tidak direwrite besar di fase awal; cukup dibungkus dan dikendalikan.
- Prioritas fase awal adalah **runability, observability, repeatability**, bukan realism maksimum.
- Semua dependency, venv, dan execution flow harus **menggunakan UV**, bukan conda.
- Semua command baru harus dirancang agar mudah dipindah ke **Ubuntu server** dengan perubahan seminimal mungkin.

## Non-goals for this plan

- Tidak membangun Next.js, NestJS, Redis, PostgreSQL, billing, multi-tenant auth.
- Tidak menulis ulang engine vendor LiveTalking dari nol.
- Tidak mengejar face swap / FaceFusion / body-double hybrid.
- Tidak menambahkan dependency manager kedua seperti conda atau poetry.

## Environment policy

- Gunakan `uv venv`, `uv sync`, `uv run`, dan `uv pip` sebagai jalur resmi.
- Jangan memperkenalkan instruksi `conda create`, `conda activate`, `pip install` langsung ke system Python, atau `.bat`/script yang bergantung pada conda env.
- Semua script baru harus punya padanan yang masuk akal untuk Windows dan Ubuntu, atau minimal tidak hard-coded ke tooling Windows jika logic-nya bisa dibuat portable.
- Jika perlu menjalankan command Python, default format yang dipakai di docs dan scripts adalah:

```bash
uv run python -m src.main
uv run pytest tests -v
uv run python scripts/verify_pipeline.py --verbose
```

- Jika perlu install dependency tambahan, format default yang dipakai adalah:

```bash
uv sync --extra dev
uv pip install <package>
```

## Definition of done for the overall roadmap

- Operator cukup membuka satu dashboard untuk:
  - melihat health Python app dan LiveTalking
  - start/stop LiveTalking
  - memeriksa readiness model/path/port
  - menjalankan preview lokal
  - memicu RTMP test
  - melihat log dan status stream
- Jalur internal live minimal berjalan reproducible dari command yang jelas.

---

## Phase 0: Freeze Direction and Single Source of Truth

**Goal:** Menghilangkan kebingungan arsitektur sebelum implementasi teknis dimulai.

**Why now:** Tanpa keputusan eksplisit soal dashboard utama, source of truth model, dan peran `external/livetalking`, implementasi berikutnya akan terus pecah ke dua jalur UI dan dua jalur runtime.

**Deliverables:**
- Dokumen keputusan arsitektur fase internal
- Peta kepemilikan komponen
- Daftar command resmi proyek

### Task 0.1: Create internal architecture decision note

**Files:**
- Create: `docs/decisions/architecture_internal_live.md`
- Reference: `docs/audits/AUDIT_CONTEXT_2026-03-07.md`
- Reference: `docs/architecture.md`
- Reference: `../../../docs/02-LIVE-STREAMING-AI/stacklokal.md`
- Reference: `../../../docs/02-LIVE-STREAMING-AI/fullstack.md`

**Required contents:**
- `videoliveai` = main control plane
- `external/livetalking` = sidecar engine
- `src/dashboard` = only operator dashboard
- `external/livetalking/web` = debug-only vendor pages
- `Svelte` = dashboard frontend target
- `Next.js/NestJS` = deferred

**Verification:**
- Review doc and ensure no contradictory wording remains.

### Task 0.2: Define source-of-truth paths

**Files:**
- Modify: `README.md`
- Modify: `docs/workflow.md`
- Modify: `docs/task_status.md`
- Create: `docs/operations/runtime_paths.md`
- Create: `docs/operations/environment_policy.md`

**Decisions to document:**
- model root
- avatar root
- engine port
- dashboard URL
- debug vendor URL
- official test commands
- UV-only workflow for Windows and Ubuntu

**Verification commands:**

```powershell
uv run pytest tests -q -p no:cacheprovider
cmd /c scripts\validate.bat
```

**Expected outcome:**
- Docs point to commands and paths that actually exist.
- Docs do not recommend conda anywhere in the active internal-live path.

### Task 0.3: Define operator vs debug UI boundary

**Files:**
- Modify: `README.md`
- Modify: `docs/guides/LIVETALKING_QUICKSTART.md`

**Content rules:**
- `/dashboard` is the operator UI
- `http://localhost:8010/*.html` is debug UI for LiveTalking engine only

**Exit criteria:**
- New contributor can answer “dashboard mana yang dipakai?” in one sentence.

### Phase 0 exit criteria

- Ada satu dokumen keputusan arsitektur internal.
- Semua docs utama tidak lagi memberi kesan ada dua dashboard utama.
- Tidak ada referensi aktif yang menyarankan Next.js sebagai jalur implementasi sekarang.

---

## Phase 1: Stabilize LiveTalking Runtime Contract

**Goal:** Menyamakan adapter Python, batch runner, model paths, dan command startup LiveTalking.

**Why now:** Runtime contract saat ini masih mismatch. Wrapper internal merujuk `server.py`, sementara vendor repo nyata menggunakan `app.py`.

### Task 1.1: Inventory actual LiveTalking runtime entrypoints

**Files:**
- Review: `external/livetalking/app.py`
- Review: `run_livetalking_web.bat`
- Review: `run_livetalking_musetalk.bat`
- Review: `src/face/livetalking_adapter.py`

**Output to produce:**
- table of:
  - startup file
  - supported transport modes
  - required model paths
  - required avatar paths
  - default ports

**Verification:**
- One markdown table saved in `docs/specs/livetalking_runtime_contract.md`

### Task 1.2: Correct adapter assumptions

**Files:**
- Modify: `src/face/livetalking_adapter.py`
- Test: `tests/test_livetalking_integration.py`

**Required changes:**
- replace `server.py` references with `app.py`
- make command construction explicit
- define supported transports: `webrtc`, `rtmp`, `rtcpush` as applicable
- return precise errors if model/avatar missing

**Verification commands:**

```powershell
uv run pytest tests/test_livetalking_integration.py -v
```

**Expected outcome:**
- Tests describe real startup assumptions, not fictional ones.

### Task 1.3: Unify model and avatar path policy

**Files:**
- Modify: `setup_wav2lip_model.bat`
- Modify: `setup_musetalk_model.bat`
- Modify: `verify_livetalking.bat`
- Modify: `run_livetalking_web.bat`
- Modify: `run_livetalking_musetalk.bat`
- Create: `docs/specs/model_path_policy.md`

**Decision to implement:**
- Pick exactly one source of truth:
  - Option A: keep all runtime models under `external/livetalking/models` and avatars under `external/livetalking/data/avatars`
  - Option B: keep all runtime models under project root and make runners symlink/copy before launch

**Recommendation:**
- Choose `Option A` for runtime simplicity.

**Verification:**
- `run_livetalking_*.bat` and setup scripts check the same directories.

### Task 1.4: Standardize ports and engine modes

**Files:**
- Modify: `.env.example`
- Modify: `src/config/loader.py`
- Create: `docs/operations/engine_ports.md`

**Settings to add or confirm:**
- `LIVETALKING_PORT`
- `LIVETALKING_TRANSPORT`
- `LIVETALKING_MODEL`
- `LIVETALKING_AVATAR_ID`

**Verification:**
- Config loader can expose these values consistently.
- No env bootstrap step assumes conda activation.

### Task 1.5: Add repeatable engine smoke test

**Files:**
- Create: `scripts/smoke_livetalking.py`
- Test: `tests/test_livetalking_integration.py`

**Smoke test responsibilities:**
- verify `app.py` exists
- verify model path exists
- verify avatar path exists
- verify port free/busy state
- print exact launch command
- print command in UV-compatible form where Python execution is needed

**Verification command:**

```powershell
uv run python scripts/smoke_livetalking.py
```

### Phase 1 exit criteria

- Wrapper, scripts, and docs all point to the same engine startup contract.
- Model and avatar location policy is unambiguous.
- A dedicated smoke test exists for LiveTalking readiness.

---

## Phase 2: Build a Python Bridge Layer to Control LiveTalking

**Goal:** FastAPI dapat mengontrol LiveTalking tanpa operator harus membuka batch file manual.

**Why now:** Dashboard tunggal membutuhkan backend bridge untuk start/stop/status engine.

### Task 2.1: Introduce LiveTalking process manager

**Files:**
- Create: `src/face/livetalking_manager.py`
- Modify: `src/face/__init__.py`
- Test: `tests/test_livetalking_integration.py`

**Manager responsibilities:**
- build launch command
- start process
- stop process
- detect if already running
- read stdout/stderr tail
- expose status object

**Verification:**
- unit tests cover command building and state transitions in mock/process-stub mode.

### Task 2.2: Expose bridge API endpoints

**Files:**
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Endpoints to add:**
- `GET /api/engine/livetalking/status`
- `POST /api/engine/livetalking/start`
- `POST /api/engine/livetalking/stop`
- `GET /api/engine/livetalking/logs`
- `GET /api/engine/livetalking/config`

**Verification command:**

```powershell
uv run pytest tests/test_dashboard.py -v
```

### Task 2.3: Register LiveTalking in health manager

**Files:**
- Modify: `src/main.py`
- Modify: `src/utils/health.py`
- Test: `tests/test_hardening.py`

**Health dimensions:**
- process running
- startup command valid
- model path valid
- avatar path valid
- engine URL reachable if process started

**Verification:**
- `/diagnostic/health/detailed` shows dedicated LiveTalking component.

### Task 2.4: Add vendor debug links into backend state

**Files:**
- Modify: `src/dashboard/api.py`

**Returned URLs:**
- operator dashboard URL
- vendor debug dashboard URL
- vendor `webrtcapi.html` URL

**Purpose:**
- make debug access available without making vendor pages the main UI.

### Phase 2 exit criteria

- FastAPI can start/stop/check LiveTalking.
- Engine status is observable through API.
- Operator no longer depends on manual batch-file execution for normal control.

---

## Phase 3: Unify Observability and Readiness Validation

**Goal:** Dashboard utama bisa menjawab “sistem python berfungsi atau tidak” dari satu tempat.

**Why now:** Ini tujuan utama yang Anda sebutkan untuk dashboard.

### Task 3.1: Define readiness checklist schema

**Files:**
- Create: `src/dashboard/readiness.py`
- Test: `tests/test_dashboard.py`

**Readiness items:**
- config loaded
- database healthy
- dashboard API healthy
- LiveTalking installed
- LiveTalking model ready
- LiveTalking avatar ready
- FFmpeg available
- RTMP target configured
- mock mode / production mode explicit

### Task 3.2: Add consolidated readiness endpoint

**Files:**
- Modify: `src/dashboard/api.py`

**Endpoint:**
- `GET /api/readiness`

**Response shape:**
- `overall_status`
- `checks[]`
- `blocking_issues[]`
- `recommended_next_action`

### Task 3.3: Add validation workflow endpoint group

**Files:**
- Modify: `src/dashboard/api.py`
- Optional create: `src/dashboard/validators.py`

**Endpoints:**
- `POST /api/validate/mock-stack`
- `POST /api/validate/livetalking-engine`
- `POST /api/validate/rtmp-target`
- `POST /api/validate/full-live-slice`

**Note:**
- These can shell out to scripts or call internal Python bridge methods.

### Task 3.4: Normalize log surfaces

**Files:**
- Modify: `src/utils/logging.py`
- Modify: `src/dashboard/api.py`
- Create: `docs/operations/log_surfaces.md`

**Targets:**
- app logs
- LiveTalking process logs
- validation logs

### Task 3.5: Fix verification CLI encoding and consistency

**Files:**
- Modify: `scripts/verify_pipeline.py`
- Modify: `scripts/validate.bat`
- Test: manual validation

**Goal:**
- CLI works without requiring `PYTHONUTF8=1`
- validation output remains Windows-safe

**Verification commands:**

```powershell
uv run python scripts/verify_pipeline.py --verbose
cmd /c scripts\validate.bat
```

### Phase 3 exit criteria

- A single readiness endpoint exists.
- Operator can see blocking issues without reading raw logs.
- Validation commands are Windows-safe and reproducible.

---

## Phase 4: Replace Static HTML Dashboard with Svelte Operator UI

**Goal:** Menjadikan dashboard operator lebih maintainable tanpa menambah kompleksitas Next.js.

**Why now:** Setelah bridge dan observability ada, barulah UI punya backend yang stabil untuk dikendalikan.

### Task 4.1: Decide frontend packaging strategy

**Files:**
- Create: `src/dashboard/frontend/package.json`
- Create: `src/dashboard/frontend/vite.config.ts`
- Create: `src/dashboard/frontend/src/*`
- Create: `docs/decisions/dashboard_frontend_strategy.md`

**Recommendation:**
- Vite + Svelte static build
- build output lands in `src/dashboard/frontend/dist`
- FastAPI serves the built assets

### Task 4.2: Define operator IA (information architecture)

**Files:**
- Create: `docs/decisions/dashboard_ia.md`

**Required screens/tabs:**
- Overview
- Readiness
- Engine
- Preview
- Stream
- Scripts
- Diagnostics/Logs

### Task 4.3: Implement shell layout and API client

**Files:**
- Create: `src/dashboard/frontend/src/App.svelte`
- Create: `src/dashboard/frontend/src/lib/api.ts`
- Create: `src/dashboard/frontend/src/lib/types.ts`
- Create: `src/dashboard/frontend/src/lib/stores.ts`

**Requirements:**
- no auth layer yet
- support polling and WebSocket where useful
- show API unreachable state clearly

### Task 4.4: Build Readiness and Engine panels first

**Files:**
- Create: `src/dashboard/frontend/src/routes-or-components/*`

**Minimum controls:**
- show readiness check results
- start/stop LiveTalking
- show vendor debug links
- show current model/avatar/transport settings

### Task 4.5: Add Preview and Stream panels

**Files:**
- Create: `src/dashboard/frontend/src/routes-or-components/*`

**Capabilities:**
- show preview link or iframe launcher rules
- show RTMP target state
- trigger stream validation

### Task 4.6: Switch FastAPI to serve built Svelte output

**Files:**
- Modify: `src/main.py`

**Verification commands:**

```powershell
uv run python -m src.main
```

**Expected outcome:**
- `/dashboard` serves Svelte build successfully.

### Phase 4 exit criteria

- Dashboard uses Svelte, not ad-hoc single HTML file.
- Operator can validate engine and readiness from one UI.
- Vendor pages are linked as debug tools, not embedded as the main control plane.

---

## Phase 5: Deliver the First Vertical Slice of “Can Go Live”

**Goal:** Menyediakan jalur minimal yang benar-benar bisa dipakai untuk internal live test.

**Why now:** Setelah control plane ada, proyek perlu bukti end-to-end yang kecil tapi nyata.

### Task 5.1: Define the vertical slice contract

**Files:**
- Create: `docs/specs/vertical_slice_v1.md`

**Slice definition:**
- start LiveTalking
- open preview
- send text/script to engine
- avatar outputs speech/video
- validate RTMP target config
- attempt stream start to test endpoint

### Task 5.2: Add script submission bridge

**Files:**
- Modify: `src/face/livetalking_manager.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_livetalking_integration.py`

**Need to determine:**
- which LiveTalking endpoint accepts text payload
- expected request body
- response contract

### Task 5.3: Add script queue minimum viable flow

**Files:**
- Create: `src/dashboard/script_queue.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Capabilities:**
- enqueue text
- view pending items
- dispatch current item
- mark success/failure

### Task 5.4: Add RTMP validation and dry-run

**Files:**
- Modify: `src/stream/rtmp.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_layers.py`

**Goals:**
- check config completeness
- support dry-run FFmpeg command generation
- avoid “go live” when required fields missing

### Task 5.5: Create full live-slice verification script

**Files:**
- Create: `scripts/validate_live_slice.py`

**Verification command:**

```powershell
uv run python scripts/validate_live_slice.py
```

### Phase 5 exit criteria

- One documented and repeatable live-slice test exists.
- Dashboard can drive that slice.
- Failure modes are explicit and diagnosable.

---

## Phase 6: Increase Realism Without Breaking the Slice

**Goal:** Meningkatkan naturalness secara bertahap setelah operasional stabil.

**Why now:** Realism work mahal dan mudah membuat sistem tidak stabil jika dilakukan terlalu awal.

### Task 6.1: Pick the face realism track for v1

**Files:**
- Create: `docs/research/realism_track_v1.md`

**Recommendation:**
- choose one:
  - `Wav2Lip baseline`
  - `MuseTalk production track`

**Expected v1 recommendation:**
- baseline = Wav2Lip for operational validation
- upgrade path = MuseTalk when GPU + assets ready

### Task 6.2: Improve avatar/source asset requirements

**Files:**
- Create: `docs/specs/avatar_asset_spec.md`
- Create: `docs/specs/audio_asset_spec.md`

**Contents:**
- lighting
- framing
- resolution
- duration
- naming conventions

### Task 6.3: Add behavioral humanization backlog

**Files:**
- Create: `docs/research/humanization_backlog.md`

**Backlog items:**
- response delay variance
- filler token insertion
- pacing variation
- script segmentation
- safe fallback phrases
- natural silence windows

### Task 6.4: Add minimal TTS realism policy

**Files:**
- Modify: `src/voice/engine.py`
- Create: `docs/research/tts_realism_policy.md`

**Note:**
- this phase is policy-first unless actual engine implementation is ready
- no large TTS engine rewrite before slice remains stable

### Task 6.5: Add realism scorecard for internal review

**Files:**
- Create: `docs/research/realism_scorecard.md`

**Dimensions:**
- lip sync
- facial motion
- voice naturalness
- timing behavior
- stream stability

### Phase 6 exit criteria

- There is a realism roadmap that does not destabilize the live slice.
- Asset quality requirements are explicit.
- Internal team can score improvements using one rubric.

---

## Phase 7: Reliability and Internal Operations Hardening

**Goal:** Membuat sistem cukup tangguh untuk dipakai internal berulang kali.

**Why now:** Setelah sistem bisa live, barulah reliability work memberi nilai nyata.

### Task 7.1: Add process recovery policy

**Files:**
- Create: `src/utils/process_supervisor.py`
- Modify: `src/face/livetalking_manager.py`
- Create: `docs/operations/process_recovery_policy.md`

**Capabilities:**
- detect crash
- mark unhealthy
- controlled restart with backoff

### Task 7.2: Add persistent session and run logs

**Files:**
- Modify: `src/data/schema.sql`
- Modify: `src/data/database.py`
- Create: `src/operations/run_history.py`
- Test: `tests/test_layers.py`

**Data to store:**
- start time
- stop time
- mode
- model
- stream target
- success/failure
- failure reason

### Task 7.3: Add operator runbook

**Files:**
- Create: `docs/operations/RUNBOOK_INTERNAL_LIVE.md`

**Sections:**
- before stream
- start engine
- validate readiness
- run live slice
- recover from common failures
- stop safely

### Task 7.4: Add failure taxonomy and alerts

**Files:**
- Create: `docs/research/failure_taxonomy.md`
- Modify: `src/dashboard/api.py`

**Failure classes:**
- config error
- missing model
- missing avatar
- port collision
- FFmpeg unavailable
- RTMP rejected
- engine crash

### Task 7.5: Add final internal acceptance checklist

**Files:**
- Create: `docs/specs/acceptance_internal_live_v1.md`

**Checklist areas:**
- install
- readiness
- preview
- engine control
- RTMP dry-run
- live slice
- recovery

### Phase 7 exit criteria

- System has restart/recovery policy.
- Internal runbook exists.
- Acceptance checklist exists for recurring validation.

---

## Recommended implementation order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 5
6. Phase 4
7. Phase 6
8. Phase 7

## Why this order

- Phase 5 is intentionally placed before full dashboard polish if needed, because proving the vertical slice matters more than UI completeness.
- Phase 4 can start earlier for layout work, but should not block runtime stabilization.

## Commands expected to remain green throughout

```powershell
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py --verbose
cmd /c scripts\validate.bat
```

## Commands expected to exist on Ubuntu server as equivalents

```bash
uv sync --extra dev
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py --verbose
uv run python -m src.main
```

## Review checklist for another agent

- Does every phase have a concrete exit criterion?
- Are all source-of-truth path decisions explicit?
- Is LiveTalking treated as vendor sidecar, not silently forked application logic?
- Does the dashboard remain single-source for operator control?
- Are realism tasks sequenced after operational proof?

## Risks to watch

- Scope creep into `fullstack.md` architecture too early
- Path duplication between root project and vendor repo
- UI work starting before backend bridge exists
- Realism experiments breaking vertical slice stability
- Batch-script-only workflows bypassing dashboard APIs
- Reintroduction of conda-specific instructions that break portability to Ubuntu server

## Suggested milestone labels

- `M1`: Docs and runtime contract stable
- `M2`: LiveTalking controllable from FastAPI
- `M3`: Unified readiness validation
- `M4`: Vertical slice can go live
- `M5`: Svelte operator dashboard complete
- `M6`: Realism uplift baseline
- `M7`: Internal operations hardened
