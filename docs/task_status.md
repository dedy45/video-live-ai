# Task Status

> Honest status snapshot for the internal-live architecture.
> Last verified: 2026-03-08
> Package manager policy: `uv` only

## Verification Snapshot

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `uv run pytest tests -q -p no:cacheprovider` | `132 passed` |
| Pipeline verification | `uv run python scripts/verify_pipeline.py` | `11/11 layers passed` |
| Frontend build | `cd src/dashboard/frontend && npm run build` | PASS |
| Frontend unit tests | `cd src/dashboard/frontend && npm run test` | `40 passed` (5 test files) |
| Browser smoke test | `cd src/dashboard/frontend && npx playwright test` | `8 passed` |
| Real-mode readiness gate | `uv run python scripts/check_real_mode_readiness.py --json` | `BLOCKED` — 1 real prerequisite missing (`Product data source exists`) |
| FFmpeg runtime | `uv run python scripts/setup_ffmpeg.py` | portable FFmpeg verified in `tools/ffmpeg/bin/ffmpeg.exe` |
| MuseTalk assets | `uv run python scripts/setup_musetalk_assets.py --sync-only` | models ready, canonical MuseTalk avatar still not generated, reference media now present |
| Known noise | pytest temp cleanup on Windows | warning after pass, does not invalidate result |

## Overall Verdict

Local development baseline is **verified**.
Portable FFmpeg is **installed and working locally**.
Canonical MuseTalk model storage is **ready**, but production-ready internal live stack is **not complete yet**.

The old claim `All Local Phases COMPLETE` is retired because it mixed together:

- mock-mode validation
- documentation completion
- partial adapters
- real production runtime readiness

## Status Legend

- `LOCAL VERIFIED`: works in local dev or mock validation and is backed by current checks
- `IN PROGRESS`: active execution track, not yet eligible for final verification claims
- `PARTIAL`: exists, but integration contract or runtime path is still incomplete
- `TARGET ONLY`: documented target, not active implementation today
- `PENDING GPU`: needs real GPU/runtime validation before being trusted

## Component Status

| Area | Status | Notes |
|------|--------|-------|
| FastAPI control plane | `LOCAL VERIFIED` | Main app, diagnostics, API, orchestration baseline working |
| Dashboard baseline | `LOCAL VERIFIED` | Current dashboard path works as operator entrypoint |
| Svelte dashboard migration | `LOCAL VERIFIED` | Svelte build mounted at `/dashboard`, frontend unit tests passing (40 tests), Playwright browser tests passing (8 tests), requested/resolved LiveTalking state visible in Engine panel, Truth Bar with runtime truth, provenance badges on all panels, action receipts on operator actions, zero silent failures, and tab switching validated in browser |
| Brain layer | `LOCAL VERIFIED` | Covered by current test suite and verify pipeline |
| Voice orchestration | `LOCAL VERIFIED` | Project voice layer works in current validation path |
| Composition / stream / chat / commerce | `LOCAL VERIFIED` | Covered by tests and verify pipeline |
| FFmpeg runtime | `LOCAL VERIFIED` | Project-local FFmpeg installed at `tools/ffmpeg/bin/ffmpeg.exe` |
| LiveTalking vendor repo present | `LOCAL VERIFIED` | Sidecar code exists in `external/livetalking` |
| LiveTalking runtime contract | `PARTIAL` | Wrapper, docs, and vendor entrypoint still need alignment |
| MuseTalk models inside vendor LiveTalking | `LOCAL VERIFIED` | Weights normalized into `external/livetalking/models/musetalk` |
| MuseTalk avatar runtime asset | `PARTIAL` | `musetalk_avatar1` is still not generated into the canonical vendor path; runtime currently falls back to `wav2lip256_avatar1` |
| Wav2Lip inside vendor LiveTalking | `LOCAL VERIFIED` | Legacy fallback still active |
| Ultralight inside vendor LiveTalking | `LOCAL VERIFIED` | Active vendor low-resource path |
| ER-NeRF inside vendor LiveTalking | `TARGET ONLY` | Advertised in docs, but runtime branch is commented out |
| GFPGAN inside vendor LiveTalking | `TARGET ONLY` | Claimed in project docs, not found in vendor runtime |
| `src/face/pipeline.py` MuseTalk path | `PARTIAL` | Still raises `NotImplementedError` for production GPU path |
| `src/face/pipeline.py` GFPGAN path | `PARTIAL` | Still raises `NotImplementedError` |
| Unified dashboard for full system validation | `LOCAL VERIFIED` | Operator shell is live, requested/resolved LiveTalking state visible in Engine panel, Truth Bar with runtime truth active, frontend unit (40 tests) and browser smoke tests (8 tests) passing |
| Dashboard Single Truth Real Validation | `IN PROGRESS` | Task 1-9 now verified locally. Realtime dashboard store, Validation Console, evidence history, operator controls, and strict real-mode gate are all working in local validation. Task 10 remains blocked for `REAL VERIFIED` because the real-mode gate still fails on missing real product data source. |
| RTMP live slice to TikTok/Shopee | `PENDING GPU` | Needs end-to-end run with real target |
| 18-24 hour stability layer | `PENDING GPU` | Not validated yet |

## Current Architecture Truth

- `videoliveai` is the main control plane.
- `external/livetalking` is a vendor sidecar, not the whole system.
- `/dashboard` is the only operator dashboard.
- `localhost:8010/*.html` are vendor debug pages only.
- `GPT-SoVITS` / `CosyVoice` belong to the voice layer, not the face engine.

## Immediate Priorities

1. Provide a real product data source so `uv run python scripts/check_real_mode_readiness.py --json` can pass instead of blocking on `Product data source exists`.
2. Generate `musetalk_avatar1` into the canonical vendor path to remove the current Wav2Lip fallback.
3. Run Task 10 real-mode acceptance with `MOCK_MODE=false` and collect audit evidence.
4. Keep docs and verification counts synchronized with the current gate results.

## Pending GPU / Production Work

- Acquire production avatar and voice assets
- Generate MuseTalk avatar from real reference media
- Validate MuseTalk path on real GPU
- Decide final voice path for internal live: `FishSpeech`, `GPT-SoVITS`, or `CosyVoice`
- Validate RTMP output against test target
- Add restart and recovery policy for long sessions

## Source Of Truth

- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [dashboard_truth_model.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/dashboard_truth_model.md)
- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)
