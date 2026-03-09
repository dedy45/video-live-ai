# Task Status

> Honest status snapshot for the internal-live architecture.
> Last verified: 2026-03-09
> Package manager policy: `uv` only

## Verification Snapshot

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `uv run pytest tests -q -p no:cacheprovider` | `161 passed` |
| Pipeline verification | `uv run python scripts/verify_pipeline.py` | `11/11 layers passed` |
| Frontend build | `cd src/dashboard/frontend && npm run build` | PASS |
| Frontend unit tests | `cd src/dashboard/frontend && npm run test` | `40 passed` (5 test files) |
| Browser smoke test | `cd src/dashboard/frontend && npx playwright test` | `8 passed` |
| Real-mode readiness gate | `uv run python scripts/check_real_mode_readiness.py --json` | `READY FOR REAL MODE` — 11/11 checks passed, but this prerequisite gate does not override the milestone failure while fallback remains active |
| FFmpeg runtime | `uv run python scripts/setup_ffmpeg.py` | portable FFmpeg verified in `tools/ffmpeg/bin/ffmpeg.exe` |
| MuseTalk assets | `uv run python scripts/setup_musetalk_assets.py --sync-only` | models ready, canonical MuseTalk avatar still not generated, reference media now present |
| LiveTalking setup (UV) | `uv sync --extra dev` then `uv run python scripts/manage.py setup-livetalking --skip-models` | PASS — setup now rehydrates vendor deps in the managed UV env, prints ASCII-safe status, and treats no-GPU machines as advisory warning only |
| LiveTalking vendor imports | `uv run --extra livetalking python -c "import flask, flask_sockets, aiohttp_cors, transformers, diffusers, accelerate, omegaconf"` | PASS |
| LiveTalking smoke validation | `uv run python scripts/manage.py validate livetalking` | PASS — truthful Wav2Lip fallback, FFmpeg ready, vendor entrypoint/layout verified |
| LiveTalking non-mock spawn | `MOCK_MODE=false uv run --extra livetalking python -c "... LiveTalkingManager().start() ..."` | PASS — process spawns, warms up on CPU, and port `8010` becomes reachable after vendor image scan/model warmup (~20s on this box) |
| Known noise | pytest temp cleanup on Windows | warning after pass, does not invalidate result |

## Active Milestone

**`LOCAL_VERTICAL_SLICE_REAL_MUSETALK`** — see `docs/specs/local_vertical_slice_real_musetalk.md`

Active face runtime: **MuseTalk only** (Wav2Lip fallback does NOT count as milestone pass).

## Overall Verdict

Local development baseline is **verified**.
Portable FFmpeg is **installed and working locally**.
Real product data source is **present** (`data/products.json`).
Canonical MuseTalk model storage is **ready**.
Canonical MuseTalk avatar is **not yet generated** — runtime currently falls back to `wav2lip`.
Real-mode readiness gate passes all 11 prerequisites, but the active milestone is still **partial**.
Current readiness truth still shows `face_runtime_mode=mock`, so the official non-mock operator slice must be re-run and captured explicitly.
Milestone audit recorded at `docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md`; the current audit is a prerequisite snapshot, not final Task 7 acceptance evidence.
Humanization is **defined but blocked** until the MuseTalk milestone is truly complete — see `docs/specs/humanization_minimum_contract.md`.

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
| LiveTalking runtime contract | `PARTIAL` | UV dependency blocker is fixed and setup now hydrates the vendor stack correctly; non-mock vendor startup reaches ready port after warmup, but MuseTalk avatar generation and real GPU validation are still pending |
| MuseTalk models inside vendor LiveTalking | `LOCAL VERIFIED` | Weights normalized into `external/livetalking/models/musetalk` |
| MuseTalk avatar runtime asset | `PARTIAL` | `musetalk_avatar1` is still not generated into the canonical vendor path; runtime currently falls back to `wav2lip256_avatar1` |
| Wav2Lip inside vendor LiveTalking | `LOCAL VERIFIED` | Legacy fallback still active |
| Ultralight inside vendor LiveTalking | `LOCAL VERIFIED` | Active vendor low-resource path |
| ER-NeRF inside vendor LiveTalking | `TARGET ONLY` | Advertised in docs, but runtime branch is commented out |
| GFPGAN inside vendor LiveTalking | `TARGET ONLY` | Claimed in project docs, not found in vendor runtime |
| `src/face/pipeline.py` MuseTalk path | `PARTIAL` | Still raises `NotImplementedError` for production GPU path |
| `src/face/pipeline.py` GFPGAN path | `PARTIAL` | Still raises `NotImplementedError` |
| Unified dashboard for full system validation | `LOCAL VERIFIED` | Operator shell is live, requested/resolved LiveTalking state visible in Engine panel, Truth Bar with runtime truth active, frontend unit (40 tests) and browser smoke tests (8 tests) passing |
| Dashboard Single Truth Real Validation | `LOCAL VERIFIED` | Realtime dashboard store, Validation Console, evidence history, operator controls, and real-mode gate behavior are locally verified; the active blocker has moved to the MuseTalk milestone, not the old product-data gate |
| RTMP live slice to TikTok/Shopee | `PENDING GPU` | Needs end-to-end run with real target |
| 18-24 hour stability layer | `PENDING GPU` | Not validated yet |

## Current Architecture Truth

- `videoliveai` is the main control plane.
- `external/livetalking` is a vendor sidecar, not the whole system.
- `/dashboard` is the only operator dashboard.
- `localhost:8010/*.html` are vendor debug pages only.
- `GPT-SoVITS` / `CosyVoice` belong to the voice layer, not the face engine.

## Immediate Priorities

1. Generate `musetalk_avatar1` into the canonical vendor path so the runtime can resolve to MuseTalk instead of `wav2lip`.
2. Re-run the official operator slice with `uv run python scripts/manage.py serve --real`, `health --json`, and `validate livetalking`, then record requested/resolved truth in the audit.
3. Debug why readiness truth still reports `face_runtime_mode=mock` under `MOCK_MODE=false`, and confirm the same path while the app is actually serving in real mode.
4. Validate the same non-mock warmup path on a real GPU and record realistic readiness timings before starting Humanization Minimum.

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
- [local_vertical_slice_real_musetalk.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/local_vertical_slice_real_musetalk.md)
- [musetalk_asset_contract.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/musetalk_asset_contract.md)
- [humanization_minimum_contract.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/humanization_minimum_contract.md)
- [AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md)
- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)
