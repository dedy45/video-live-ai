# Changelog

## v0.5.0 — 2026-03-04 (LiteLLM Migration + Menu Overhaul)

### 🔥 Breaking Changes
- Semua custom LLM adapter (chutes.py, groq.py, gemini.py, dll) digantikan oleh **LiteLLM universal adapter**
- `CHUTES_API_KEY` → `CHUTES_API_TOKEN` (masih ada fallback ke lama)

### ✅ New Features
- **LiteLLM backend** (`src/brain/adapters/litellm_adapter.py`) — satu adapter untuk semua 100+ provider
- **`scripts/menu.bat` v0.5.0** — rewrite lengkap dengan:
  - PID-based server start/stop (tidak kill semua python.exe)
  - Menu LLM Test: Auto Route, Local Gemini, Groq, Chutes, Test ALL
  - Helper `check_port_free` dan `check_server_running`
  - Module import check yang diupdate (litellm_adapter)
- **PID file** (`data/.server.pid`) — ditulis saat server start, dihapus saat stop
- **Local proxy auto-detect** — jika `LOCAL_LLM_URL` == `LOCAL_GEMINI_URL`, otomatis pakai model Cherry Studio
- **`docs/architecture.md`** — tabel provider LiteLLM + routing table lengkap

### 🐛 Bug Fixes
- Fix `config.yaml` timeout Gemini 500ms → 10000ms (sebelumnya selalu timeout)
- Fix model Chutes: `MiniMaxAI/MiniMax-M2.5` → `MiniMaxAI/MiniMax-M2.5-TEE` (suffix TEE wajib)
- Fix `CHUTES_API_TOKEN` tidak ter-load karena `.env` tidak dibaca saat `python -c`
- Fix `diagnostic.py` missing `import os`
- Fix `pipeline/transition` endpoint pakai query param → JSON body `TransitionRequest`
- Fix `src/brain/adapters/__init__.py` masih import adapter lama
- Fix `main.py` shutdown handler yang kosong (stub)

### 📊 Test Results
- 66/66 tests passing (MOCK_MODE)
- Live test: gemini_local_flash ✅ groq ✅ chutes ✅ gemini (quota exceeded, auto-fallback ke groq ✅)

### 💡 Provider Status
| Provider | Status | Notes |
|----------|--------|-------|
| gemini_local_flash | ✅ OK | Cherry Studio port 8091 |
| gemini_local_pro | ✅ OK | Cherry Studio port 8091 |
| groq | ✅ OK | ~330ms |
| chutes | ✅ OK | ~8s (MiniMax-M2.5-TEE) |
| gemini | ⚠️ Quota | API key quota exceeded, auto-fallback |
| claude | ⚠️ No key | ANTHROPIC_API_KEY not set |
| gpt4o | ⚠️ No key | OPENAI_API_KEY not set |
| local | ✅ OK | Auto-detect Cherry Studio |

s

> Catatan evolusi teknis proyek dan keputusan Socratic Design Refinement (SDR).

---

## [0.5.0] — 2026-03-03

### Removed

- **HTTP Basic Auth** — Removed login requirement from all dashboard API endpoints
  - Login page was broken (credentials lost on every page reload, no localStorage)
  - All `/api/*` endpoints now open access (suitable for local development)
  - Removed `fastapi.security.HTTPBasic` dependency from `api.py`

### Added (Dashboard Command Center + LLM Brain Interactive UI)

**Dashboard Frontend Rebuild (Phase 14.5)**

- Complete rebuild of `dashboard/frontend/index.html` — "AI Live Commerce — Command Center"
- 5-tab navigation: Overview, LLM Brain, Pipeline, Commerce, Monitor
- Premium dark theme with glassmorphism, micro-animations, and responsive grid
- No login overlay — dashboard loads directly

**LLM Brain Interactive Control (Phase 14.6)**

- `GET /api/brain/stats` — Provider usage stats, routing table, adapter config
- `GET /api/brain/health` — Check all LLM provider connectivity
- `POST /api/brain/test` — Send test prompts with task type and provider selection
- `GET /api/brain/config` — View LLM configuration and routing rules
- Dashboard "🧠 LLM Brain" tab:
  - Provider grid (status, model, calls, latency, cost per provider)
  - Routing table visualization (task → primary → fallback chain)
  - Interactive test prompt tool (select task type, provider, view response)
  - Cost tracker with progress bar and per-provider breakdown

**Pipeline State Machine UI (Phase 14.7)**

- `GET /api/pipeline/state` — Current state, valid transitions, history
- `POST /api/pipeline/transition` — Transition to new state with validation
- States: IDLE → SELLING ⇄ REACTING ⇄ ENGAGING → PAUSED → IDLE
- Dashboard "⚙️ Pipeline" tab:
  - Clickable state machine nodes (green = available, cyan = current)
  - Full architecture diagram (Python Brain + Visual GPU layers)
  - Transition history log

### Fixed

**Batch Script Path Resolution (Critical)**

- `menu.bat` — Fixed `start cmd /c` commands that crashed with `!` in path
  - Root cause: `\"%PYTHON%\"` inside `cmd /c "..."` breaks when path contains `!`
  - Fix: Generate temporary `_launcher.bat` script, run via `start /b cmd /c`
  - Both mock and production server start commands fixed
- `menu.bat` + `validate.bat` — Fixed `PROJECT_DIR` resolution
  - Changed from `set "PROJECT_DIR=%~dp0.."` to `cd /d %~dp0\..` + `set "PROJECT_DIR=%CD%"`
  - Resolves `..` in path so Python gets clean absolute path

### SDR Notes

- **SDR-011**: Removed auth for local dev dashboard — security via network isolation, not HTTP Basic
- **SDR-012**: LLM Brain UI enables rapid debugging without terminal — test prompts, check routing, monitor costs
- **SDR-013**: Pipeline state machine is API-driven — frontend is pure visualization, state lives server-side

---

## [0.1.0] — 2026-03-03

### Added

**Phase 0: Pre-Production**

- Inisialisasi 6 docs files untuk Agent persistence
- Mock Mode: `MockVoiceSynthesizer` + `MockAvatarRenderer` (format identik produksi)

**Phase 1: Infrastructure**

- `pyproject.toml` — UV package manager, GPU optional
- `config/loader.py` — Pydantic typed config + YAML + .env override
- `utils/logging.py` — structlog JSON + trace_id generation (Req 34)
- `utils/validators.py` — Asset validation (Req 17)
- `data/schema.sql` — 6 tables (products, chat_events, llm_usage, affiliate, metrics, safety)
- `dashboard/diagnostic.py` — `/diagnostic` health endpoint

**Phase 2: Multi-LLM Brain**

- 6 LLM adapters: Gemini Flash, Claude Sonnet, GPT-4o-mini, **Groq** (ultra-fast), Local/Qwen
- `router.py` — Task-type routing + fallback chain + daily budget ($5 cap)
- `persona.py` — AI host "Sari" + 7-phase selling scripts
- `safety.py` — Keyword blacklist + excessive caps detection

**Phase 3-4: Voice & Face**

- FishSpeechEngine + EdgeTTSEngine + AudioCache + VoiceRouter
- MuseTalkEngine + GFPGANEnhancer + TemporalSmoother + IdentityController + AvatarPipeline

**Phase 5-8: Composition, Stream, Chat, Commerce**

- FFmpegCompositor (7-layer filter graph)
- RTMPStreamer (auto-reconnect eksponstial backoff)
- ChatMonitor (Platform Abstraction + TikTok/Shopee + PriorityQueue + IntentDetector)
- ProductManager + ScriptEngine + AffiliateTracker

**Phase 9: Orchestrator**

- State machine: SELLING ↔ REACTING ↔ ENGAGING
- Event-driven chat handling + product rotation + safety pipeline

### SDR Notes

- **SDR-001**: Hybrid Rendering → mengurangi GPU load during selling
- **SDR-002**: Mock Mode → full local development tanpa GPU
- **SDR-003**: Groq sebagai primary chat reply → sub-100ms latency
- **SDR-004**: Platform Abstraction (Observer) → extensible ke YouTube/Instagram
- **SDR-005**: Safety Filter dipasang sebelum TTS → prevent banned content

---

## [0.2.0] — 2026-03-03

### Fixed (Hardening Pass)

- `database.py` — Added exception handling to `init_database`, connection timeout 10s
- `main.py` — Graceful shutdown, config/logging fallback if loading fails
- `router.py` — `asyncio.wait_for` timeout per adapter (prevents chain blocking)
- `groq.py` — Removed type-ignore, added client timeout
- All 5 adapters — Empty prompt validation (returns `success=False`)
- `diagnostic.py` — Real module import checks, PID in system info

### Added

- `utils/health.py` — Centralized health manager (per-check timeout, concurrent)
- `/diagnostic/health/detailed` — Detailed health endpoint via HealthManager
- `check_database_health()` — Reusable DB health function
- `tests/test_hardening.py` — 14 edge case tests
- `pyproject.toml` — Added `edge-tts`, `pytest-cov` dependencies

---

## [0.3.0] — 2026-03-03

### Added (Verification + Dashboard + Analytics)

**Verification System**

- `scripts/verify_pipeline.py` — CLI tool verifying all 11 system layers
- Supports `--verbose` and `--layer <name>` filtering
- Covers Checkpoints 3, 6, 10, 13 from tasks.md

**Dashboard REST API (Phase 14.1)**

- `dashboard/api.py` — 13 REST endpoints + 2 WebSocket streams
- `GET /api/status` — System state, viewers, budget, stream status
- `GET /api/metrics` — Latency P50/P95, revenue, counters, gauges
- `GET /api/products` + `POST /api/products/{id}/switch` — Product control
- `GET /api/chat/recent` — Recent chat events with intent
- `POST /api/stream/start|stop` — Stream controls
- `POST /api/emergency-stop|reset` — Emergency kill switch
- `WS /api/ws/dashboard` — Real-time updates (1s interval)
- `WS /api/ws/chat` — Real-time chat events
- HTTP Basic auth on all endpoints

**Analytics Engine (Phase 11.6)**

- `commerce/analytics.py` — MetricBuffer ring buffer
- P50/P95 percentile tracking, 60s aggregation window
- Revenue, latency, LLM usage, event counters, gauges
- Dashboard snapshot generation for WebSocket

**Dashboard Frontend (Phase 14.3)**

- `dashboard/frontend/index.html` — Premium dark glassmorphic UI
- Live metrics, stream controls, product switching, chat monitor
- Health check grid, revenue summary
- WebSocket real-time updates

**Tests**

- `tests/test_dashboard.py` — 13 tests (analytics + dashboard API)

### SDR Notes

- **SDR-006**: Chose HTML/JS dashboard over Svelte for zero-dependency deploy
- **SDR-007**: Analytics uses ring buffer (deque) for O(1) memory-bounded metrics

---

## [0.3.7] — 2026-03-06

### Fixed (Documentation Sync)

**All 6 Documentation Files Updated**

- `docs/architecture.md` — Updated to v0.3.7
  - Added LiveTalking to Layer 3 (Face) architecture diagram
  - Updated directory structure with `livetalking_adapter.py` and `external/livetalking/`
  - Changed "7 test files" → "8 test files" (added test_livetalking_integration.py)
  - Updated scripts section to include `setup_livetalking.py`
- `docs/changelogs.md` — Added v0.3.2 through v0.3.7 entries
  - v0.3.2: LiveTalking integration (adapter, setup script, tests, quickstart)
  - v0.3.3: Git repository setup (.gitignore for UV, README, backup checklist)
  - v0.3.4: UV vs Conda documentation (guide, setup batch file, cleanup analysis)
  - v0.3.5: UV troubleshooting (simple_setup, fix_and_setup batch files)
  - v0.3.6: Setup automation (quick_setup.bat, SETUP_GUIDE.md, graceful error handling)
  - v0.3.7: This documentation sync
- `docs/contributing.md` — Updated to v0.3.7
  - Added "UV Package Manager Rules" section with setup commands
  - Added UV best practices (never mix with conda, always use `uv run`)
  - Added common UV errors table with solutions
  - Updated project structure to show `.venv/`, `external/livetalking/`, setup scripts
  - Clarified: Package Manager is UV (NOT conda)
- `docs/security.md` — Updated to v0.3.7
  - Added "LiveTalking Configuration" table (7 env variables)
  - Added "Git Repository Security" section
  - Documented what IS committed vs NOT committed (.gitignore rules)
  - Added setup-after-clone instructions
- `docs/task_status.md` — Updated to v0.3.7
  - Added 4 new completed phases: LiveTalking Integration, Git Repository, UV Setup, Documentation Update
  - Added `test_livetalking_integration.py` to test results table (status: pending)
  - Updated "Overall Status" section with new phases
- `docs/workflow.md` — Updated to v0.3.7
  - Replaced "Quick Start — CLI Scripts" with "Quick Start — Setup Options"
  - Added 3 setup options: quick_setup.bat, setup_livetalking_uv.bat, simple_setup_uv.bat
  - Added reference to `SETUP_GUIDE.md` for detailed instructions

**Summary of Changes Documented:**

- LiveTalking integration as production-ready Face engine (60fps, RTMP/WebRTC native)
- Git repository setup with UV-optimized .gitignore
- UV package manager setup automation (4 batch files)
- 3 new documentation files: SETUP_GUIDE.md, LIVETALKING_QUICKSTART.md, UV_VS_CONDA_GUIDE.md
- Setup flow: quick_setup.bat (fast) → test → setup_livetalking_uv.bat (full)

---

## [0.3.6] — 2026-03-06

### Added (Setup Automation & Documentation)

**Quick Setup System**

- `quick_setup.bat` — Fast setup WITHOUT LiveTalking (2-5 min, ~200MB)
  - Installs core dependencies only (FastAPI, LLM providers, basic utilities)
  - Skips torch, opencv, aiortc (heavy LiveTalking deps)
  - Perfect for testing project without GPU
- `SETUP_GUIDE.md` — Comprehensive setup guide with 3 options
  - Option 1: Quick Setup (recommended for first time)
  - Option 2: Full Setup with LiveTalking
  - Option 3: Fix Corrupt Environment
  - Includes flow diagram, comparison table, troubleshooting

**Setup Script Improvements**

- `scripts/setup_livetalking.py` — Handle missing submodule gracefully
  - No crash if `external/livetalking/` not cloned yet
  - Clear error message with instructions
  - Skip LiveTalking-specific steps if submodule missing
- `setup_livetalking_uv.bat` — Don't crash if submodule missing
  - Check submodule before running setup script
  - Provide git submodule command if missing

### Fixed

- **KeyboardInterrupt crash** — Setup script no longer crashes when LiveTalking submodule missing
- **Missing requirements.txt** — Script handles `external/livetalking/requirements.txt` not found

### Workflow

**Recommended Setup Flow:**
```bash
# Day 1: Quick start (no LiveTalking)
quick_setup.bat
set MOCK_MODE=true
uv run python -m src.main

# Day 2-3: Test, develop, configure

# Day 4: Add LiveTalking when ready
git submodule update --init
setup_livetalking_uv.bat
```

---

## [0.3.5] — 2026-03-06

### Added (UV Troubleshooting & Cleanup Scripts)

**UV Environment Cleanup**

- `simple_setup_uv.bat` — Simple and robust UV setup
  - Delete `.venv` if exists
  - Clean UV cache
  - Create fresh `.venv`
  - Install with `--no-cache` flag
  - Verify installation
- `fix_and_setup_uv.bat` — Comprehensive fix script
  - Full cleanup (`.venv` + UV cache)
  - Fresh install with no cache
  - Detailed error messages

### Fixed

- **Websockets corruption error** — `Failed to read metadata from installed package websockets==16.0`
  - Root cause: Corrupt package metadata in UV cache or `.venv`
  - Solution: Delete `.venv` + clean UV cache + install with `--no-cache`
- **Missing METADATA file** — System cannot find `websockets-16.0.dist-info\METADATA`
  - Fixed by fresh install without cache

---

## [0.3.4] — 2026-03-06

### Added (UV vs Conda Documentation)

**UV Package Manager Documentation**

- `UV_VS_CONDA_GUIDE.md` — Complete guide for UV vs Conda
  - Why UV uses miniconda Python (fallback when `.venv` missing)
  - 3 solutions: Batch file (auto), Manual step-by-step, Activate venv
  - Verification commands for Python path
  - Common errors & solutions
  - UV vs Conda comparison table
  - Best practices for this project
  - Migration guide from Conda to UV
- `setup_livetalking_uv.bat` — Automated UV setup script
  - Check UV installed
  - Create `.venv` if not exists
  - Install dependencies to `.venv`
  - Run setup with UV Python (not conda)
- `CONDA_VS_UV_CLEANUP.md` — Analysis of conda base environment
  - Confirmed conda base is CLEAN (no LiveTalking packages)
  - Root cause: `.venv` not created, not conda pollution

### Fixed

- **UV using miniconda Python** — `uv run python` was using `C:\Users\Dedy\miniconda3\python.exe`
  - Root cause: `.venv` not created yet, UV fallback to system Python
  - Solution: Create `.venv` first with `uv venv`, then install dependencies
- **Path resolution error** — `can't open file ... No such file or directory`
  - User was in wrong directory when running `uv run python scripts/...`
  - Solution: Always `cd` to `videoliveai/` first

### Verified

- Conda base environment is CLEAN (no packages from LiveTalking)
- Issue was `.venv` not created, NOT conda pollution
- UV correctly uses `.venv/Scripts/python.exe` when venv exists

---

## [0.3.3] — 2026-03-06

### Added (Git Repository & Backup)

**Git Repository Setup**

- Initialize git in `videoliveai/` folder only (not parent folder)
- `.gitignore` optimized for UV package manager
  - Ignore `.venv/` (UV virtual environment)
  - Ignore `.env` (secrets)
  - Ignore `models/` (large model weights)
  - Ignore `data/*.db`, `data/logs/` (runtime data)
  - Ignore `assets/avatar/` (user-specific references)
  - Keep `.env.example`, `data/sample_products.json`
- `README.md` — Complete project documentation
  - Badges (Python, UV, License, Tests)
  - Features, architecture, quick start
  - Setup instructions, testing guide
  - Deployment, monitoring, contributing
- `BACKUP_CHECKLIST.md` — Backup guide for UV projects
  - What to backup (source code, config templates, docs, tests)
  - What NOT to backup (`.venv/`, models, runtime data)
  - Backup commands, restore procedure
  - UV-specific notes (no conda environments)

**Git Commit & Push**

- Committed 112 files (15,321 lines of code)
- Pushed to: https://github.com/dedy45/video-live-ai.git
- Includes: Source code, tests, scripts, docs, config templates
- Excludes: `.venv/`, `.env`, `models/`, runtime data

---

## [0.3.2] — 2026-03-06

### Added (LiveTalking Integration)

**LiveTalking Real-Time Avatar System**

- `src/face/livetalking_adapter.py` — LiveTalking integration adapter (500+ lines)
  - `LiveTalkingEngine` class wrapping LiveTalking capabilities
  - 60fps real-time rendering with MuseTalk 1.5 + ER-NeRF + GFPGAN
  - Native RTMP/WebRTC streaming support
  - Reference video/audio training pipeline
  - Mock mode support for GPU-less development
  - Async initialization and streaming methods
- `scripts/setup_livetalking.py` — Automated setup script
  - Clone LiveTalking as git submodule
  - Install dependencies (torch, opencv, aiortc)
  - Create model folders
  - Update `.env` with LiveTalking config
  - Verify installation
- `tests/test_livetalking_integration.py` — Test suite
  - Engine initialization tests
  - Mock mode tests (no GPU required)
  - Configuration validation
  - Integration with existing pipeline
- `LIVETALKING_QUICKSTART.md` — Quick start guide
  - 5-minute setup instructions
  - Reference material preparation guide
  - Model download links
  - Usage examples (Option A: Replace pipeline, Option B: Conditional)
  - Configuration guide (.env settings)
  - Testing strategy (3 levels)
  - Troubleshooting common errors
  - Performance expectations

**Dependencies**

- Updated `pyproject.toml` with `[project.optional-dependencies.livetalking]`
  - torch>=2.4.0, torchvision, torchaudio
  - opencv-python>=4.9.0
  - scikit-image, scipy, librosa, soundfile, resampy
  - aiortc>=1.6.0, av>=11.0.0 (WebRTC)
  - imageio, imageio-ffmpeg

**Architecture Changes**

- Face Layer (Layer 3) now has TWO engines:
  - `pipeline.py` — Basic MuseTalk engine (existing)
  - `livetalking_adapter.py` — Production LiveTalking engine (NEW)
- LiveTalking chosen over LinYTalker for:
  - Real-time 60fps (LinYTalker only partial)
  - Native RTMP/WebRTC built-in
  - Production-ready and battle-tested
  - Multi-concurrent streams support
  - Lower latency (2-3s vs 3-5s)

**Integration Strategy**

- LiveTalking integrated into EXISTING project (not new folder)
- Replaces Face layer, other components unchanged
- Drop-in replacement for MuseTalk engine
- Backward compatible (can switch between engines)

---

## [0.3.1] — 2026-03-03

### Fixed

- `config/loader.py` — Added missing `CompositionConfig` model to `Config` class
  - `compositor.py` crashed with `'Config' object has no attribute 'composition'`
  - Added: `resolution`, `fps`, `encoding`, `bitrate`, `avatar_anchor_pct`, `product_focus_pct`
  - Audited all 7 files using `get_config()` — no other mismatches found
- `pyproject.toml` — Moved `TikTokLive` to optional `[platform]` group
  - `betterproto` (TikTokLive dependency) incompatible with Python 3.13+
  - Added `groq>=0.5.0` to main dependencies
  - Install TikTokLive only when needed: `uv sync --extra platform`

### Added

- `scripts/validate.bat` — 8-step automated validation pipeline
  - Environment check, dep sync, config validation, 18 module imports
  - Ruff linting, pytest, pipeline verification, database health
  - Reports pass/fail/warn summary
- `scripts/menu.bat` — Interactive Node Controller (20 options)
  - Server: start mock/prod, stop, status
  - Validation: full pipeline, verify, tests, lint
  - Database: health check, reset
  - Dashboard: open browser, API docs, health API
  - Dependencies: sync dev/platform/gpu
  - Tools: config check, 24 module imports, logs, clean cache

---

## [0.4.0] — 2026-03-03

### Added (Infrastructure + Deployment + Resilience)

**Resilience Layer (Phase 12.4, 12.6)**

- `utils/gpu_manager.py` — GPU Memory Manager with 6-level degradation
  - NORMAL → REDUCED_BATCH → REDUCED_RES → NO_GFPGAN → CPU_TTS → EMERGENCY
- `utils/retry.py` — Async retry with exponential backoff + jitter
- `utils/circuit_breaker.py` — CLOSED/OPEN/HALF_OPEN state machine

**Tracing (Phase 18.2)**

- `utils/tracing.py` — FastAPI middleware: X-Trace-ID (UUID) + X-Response-Time-Ms
- Wired into `main.py` as middleware

**CI/CD (Phase 15.4)**

- `.github/workflows/test.yml` — Ruff lint + Mypy typecheck + pytest (UV + MOCK_MODE)

**Docker (Phase 16.3)**

- `Dockerfile` — PyTorch 2.4 + CUDA 12.4 + FFmpeg + UV
- `docker-compose.yml` — GPU passthrough + health check
- `.dockerignore` — Lean image

**Sample Data (Phase 16.6)**

- `data/sample_products.json` — 10 Indonesian products with golden trio roles

**Documentation (Phase 16.1)**

- `README.md` — Full project documentation with badges, quick start, architecture

### Fixed

- `pyproject.toml` — Added `python_version < '3.13'` marker to TikTokLive (betterproto fix)
- `pyproject.toml` — Added `[tool.uv] managed = true` for local .venv
- Version bumped to 0.3.1 → 0.4.0

### SDR Notes

- **SDR-009**: GPU degradation is progressive, not binary

---

## [0.4.1] — 2026-03-03

### Added (Testing, Deployment Scripts & Observability)

**Tests & Validations (Phase 15)**

- `tests/test_property.py` — Hypothesis property tests for Config models (Req 19.11)
- `tests/test_performance.py` — Benchmark placeholders for GPU (Req 19.4)
- `scripts/test_authentic_flow.py` — Authentic execution bypass script (No MOCK_MODE) to prove real LLM + TTS layer functionality.

**Deployment & Monitoring (Phase 16 & 18)**

- `src/monitoring/prometheus_exporter.py` — Prometheus `/metrics` router (counters, gauges, latencies, health)
- `prometheus.yml` — Scrape config for the backend.
- `ai-live-commerce.service` — systemd daemon configuration for 24/7 resilience.
- `scripts/remote_sync.sh` & `scripts/remote_run.sh` — Tooling for syncing and executing on remote GPU instances (e.g. RunPod).
- `scripts/backup.sh` & `scripts/restore.sh` — Data backup tools with 7-day retention.
- `scripts/load_sample_data.py` — Programmatic seed script for the database.
- `main.py` — Added dummy `sentry_sdk` tracker initialization parsing `SENTRY_DSN` from OS environment.

### Fixed

- Re-architected `validate.bat` script to use DelayedExpansion (`!FAIL!`) to fix the `FAILED was unexpected` CMD bug.
- Converted `src/utils/__init__.py` to use lazy imports to prevent broken test runs due to circular deep imports.
- Created `dump_pip.py` and wrapper `.bat` tools to diagnose Windows command execution glitches.
- Added proper workflow rule `.agent/workflows/update-docs.md` to ensure document trackers are strictly updated.

---

## [0.4.4] — 2026-03-03

### Fixed (menu.bat & validate.bat Full Debug Pass)

**Root causes identified and fixed via Sequential Thinking analysis:**

**Bug 1 — `EnvSettings()` crash (most impactful)**

- `.env` has `GPU_VRAM_BUDGET_MB=20000` which is NOT declared in `EnvSettings` fields
- pydantic-settings raised `ValidationError: Extra inputs are not permitted`
- Broke: options 9 (db_health), 10 (db_reset), 17 (check_config), verify_pipeline config layer
- **Fix**: Added `"extra": "ignore"` to `EnvSettings.model_config` in `src/config/loader.py`

**Bug 2 — `uv run python/pytest/ruff` fails (betterproto conflict)**

- `uv run` triggers fresh dependency resolution, fails on `betterproto>=2.0.0b6` pre-release
- Broke: ALL validation options (6, 7, 8) and script execution
- **Fix**: Replaced ALL `uv run python`/`uv run pytest`/`uv run ruff` with direct `.venv\Scripts\python.exe` calls

**Bug 3 — Bare `python` command used wrong interpreter**

- Options 9, 10, 17, 18 used `python` (conda base env, no venv packages)
- **Fix**: Use `.venv\Scripts\python.exe` for ALL python invocations

**Bug 4 — `verify_pipeline.py` Unicode crash**

- Script uses ✅/❌ emoji; Windows CMD defaults to charmap encoding
- **Fix**: Added `set PYTHONUTF8=1` at top of both .bat files → Result: 11/11 layers pass

**Bug 5 — `config.app.environment` AttributeError in `main.py`**

- `AppConfig` has `env` field, not `environment`; would crash if SENTRY_DSN set
- **Fix**: Changed `config.app.environment` → `config.app.env` in `src/main.py`

**Bug 6 — Server start logging broken**

- `start /b cmd /c "..." > logfile` redirected `start` output, not server output
- **Fix**: Moved redirection inside the cmd /c string; added `mkdir data\logs` guard

### Added

- `validate.bat` — Step 0 venv existence check (fails fast if .venv missing)
- Both .bat files show cleaner error messages and verbose import check list
- `menu.bat` version header bumped to v0.4.3

### Verified

- `load_config()` + `load_env()`: OK ✅
- `init_database()` + `check_database_health()`: OK, 8 tables ✅
- `verify_pipeline.py`: **11/11 layers passed** ✅
- `pytest tests/`: **67/67 passed** ✅
- Module imports: **24/24 OK** ✅

---

## [0.4.3] — 2026-03-03

### Fixed (Documentation Sync Audit)

- `.kiro/specs/ai-live-commerce-platform/tasks.md` — Comprehensive audit + checkbox sync
  - Marked all implemented phases as `[x]`: 11.3–11.7, 12.1–12.8, 13, 14.1–14.4, 15.1–15.4, 16.1–16.6, 17 (partial), 18.1–18.5
  - Updated task descriptions to reflect actual file locations (e.g., `commerce/manager.py` not `commerce/script_engine.py`)
  - Updated `Success Criteria` section to reflect real completion state
  - Phase 17 marked `[~]` — partially complete (3 items require GPU server deployment)
- `docs/changelogs.md` — Added this audit entry (v0.4.3)
- `docs/task_status.md` — Verified current and accurate (no changes needed)

### Verified

- All 7 local implementation phases complete and reflected accurately in docs
- 67/67 tests passing (2.72s) — no regression from docs-only changes
- Pending GPU-hardware tasks clearly documented: Phase 0.1 (assets), Phase 0.4 (weights), Phase 17 (production stream)

### SDR Notes

- **SDR-010**: tasks.md phased from spec-oriented to implementation-reality oriented — descriptions now reference actual file locations

---

## [0.4.2] — 2026-03-03

### Fixed (Audit Pass — 67/67 Tests Green)

- `tests/test_property.py` — Fixed `test_app_config_property`: used field `env` instead of `environment` to match `AppConfig` model
- `tests/test_config.py` — Fixed `test_config_loads_from_yaml`: env var `GPU_DEVICE` from `.env` was overriding YAML test values. Now uses empty env path + clears env vars before test
- Rebuilt `.venv` — Previous venv was corrupted (Python 3.13 but pip missing). Recreated with full dependency install

### Verified

- Full project audit: all 7 layers + dashboard + tests + deployment confirmed
- Venv rebuilt with 88 packages installed (Python 3.13.11)
- 67/67 tests passing in 2.63 seconds
