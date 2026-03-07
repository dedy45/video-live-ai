# Task Status

> Honest status snapshot for the internal-live architecture.
> Last verified: 2026-03-07
> Package manager policy: `uv` only

## Verification Snapshot

| Check | Command | Result |
|-------|---------|--------|
| Test suite | `uv run pytest tests -q -p no:cacheprovider` | `89 passed` |
| Pipeline verification | `uv run python scripts/verify_pipeline.py` | `11/11 layers PASS` |
| Known noise | pytest temp cleanup on Windows | warning after pass, does not invalidate result |

## Overall Verdict

Local development baseline is **verified**.  
Production-ready internal live stack is **not complete yet**.

The old claim `All Local Phases COMPLETE` is retired because it mixed together:

- mock-mode validation
- documentation completion
- partial adapters
- real production runtime readiness

## Status Legend

- `LOCAL VERIFIED`: works in local dev or mock validation and is backed by current checks
- `PARTIAL`: exists, but integration contract or runtime path is still incomplete
- `TARGET ONLY`: documented target, not active implementation today
- `PENDING GPU`: needs real GPU/runtime validation before being trusted

## Component Status

| Area | Status | Notes |
|------|--------|-------|
| FastAPI control plane | `LOCAL VERIFIED` | Main app, diagnostics, API, orchestration baseline working |
| Dashboard baseline | `LOCAL VERIFIED` | Current dashboard path works as operator entrypoint |
| Svelte dashboard migration | `TARGET ONLY` | Planned, not implemented yet |
| Brain layer | `LOCAL VERIFIED` | Covered by current test suite and verify pipeline |
| Voice orchestration | `LOCAL VERIFIED` | Project voice layer works in current validation path |
| Composition / stream / chat / commerce | `LOCAL VERIFIED` | Covered by tests and verify pipeline |
| LiveTalking vendor repo present | `LOCAL VERIFIED` | Sidecar code exists in `external/livetalking` |
| LiveTalking runtime contract | `PARTIAL` | Wrapper, docs, and vendor entrypoint still need alignment |
| MuseTalk inside vendor LiveTalking | `LOCAL VERIFIED` | Active vendor runtime path |
| Wav2Lip inside vendor LiveTalking | `LOCAL VERIFIED` | Legacy fallback still active |
| Ultralight inside vendor LiveTalking | `LOCAL VERIFIED` | Active vendor low-resource path |
| ER-NeRF inside vendor LiveTalking | `TARGET ONLY` | Advertised in docs, but runtime branch is commented out |
| GFPGAN inside vendor LiveTalking | `TARGET ONLY` | Claimed in project docs, not found in vendor runtime |
| `src/face/pipeline.py` MuseTalk path | `PARTIAL` | Still raises `NotImplementedError` for production GPU path |
| `src/face/pipeline.py` GFPGAN path | `PARTIAL` | Still raises `NotImplementedError` |
| Unified dashboard for full system validation | `PARTIAL` | Direction fixed, implementation not finished |
| RTMP live slice to TikTok/Shopee | `PENDING GPU` | Needs end-to-end run with real target |
| 18-24 hour stability layer | `PENDING GPU` | Not validated yet |

## Current Architecture Truth

- `videoliveai` is the main control plane.
- `external/livetalking` is a vendor sidecar, not the whole system.
- `/dashboard` is the only operator dashboard.
- `localhost:8010/*.html` are vendor debug pages only.
- `GPT-SoVITS` / `CosyVoice` belong to the voice layer, not the face engine.

## Immediate Priorities

1. Stabilize LiveTalking runtime contract around `external/livetalking/app.py`.
2. Unify model and avatar paths so docs, scripts, and runtime stop disagreeing.
3. Add a single dashboard readiness surface for engine health, preview, and stream state.
4. Keep Svelte migration behind runtime stabilization, not before it.

## Pending GPU / Production Work

- Acquire production avatar and voice assets
- Validate MuseTalk path on real GPU
- Decide final voice path for internal live: `FishSpeech`, `GPT-SoVITS`, or `CosyVoice`
- Validate RTMP output against test target
- Add restart and recovery policy for long sessions

## Source Of Truth

- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)
