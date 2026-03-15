# Task Status

> Honest status snapshot for the internal-live architecture.
> Last broad verification: 2026-03-11
> Last targeted dashboard verification: 2026-03-14
> Last targeted vendor preview verification: 2026-03-14
> Package manager policy: `uv` only

## Verification Snapshot

| Check | Command | Result |
|-------|---------|--------|
| Voice Lab hybrid control-plane slice | `uv run pytest tests/test_control_plane.py tests/test_dashboard.py -q -p no:cacheprovider` + `cd src/dashboard/frontend && npm test -- --run src/tests/voice-panel.test.ts src/tests/performer-panel.test.ts` + `cd src/dashboard/frontend && npm run build` | PASS — `Suara` is now a single-flow audio workspace: `Generate Audio`, `Manajer File Lokal`, `Quick Clone`, `Studio Voice`, and `Training Jobs` all live on one page, `Tujuan output` cleanly separates `Simpan Audio Lokal` vs `Kirim ke Avatar Live`, local artifacts can be played/downloaded/deleted in place, the seeded default clone is normalized to bilingual `id/en`, and browser verification confirms real Fish generation plus local file CRUD from `performer.html` |
| Dashboard control-plane backend slice | `uv run pytest tests/test_brain.py tests/test_dashboard.py tests/test_control_plane.py -q -p no:cacheprovider` | PASS — `101 passed` |
| LiveTalking browser preview slice | `uv run pytest tests/test_livetalking_integration.py tests/test_dashboard.py -q -p no:cacheprovider` | PASS — manager uses dedicated sidecar interpreter, startup readiness waits for port `8010`, `rtcpushapi.html` has direct WebRTC fallback, and `webrtcapi.html` now ships a built-in preview-session bridge plus cache-busted `client.js` |
| Browser smoke (vendor preview) | `http://127.0.0.1:8010/webrtcapi.html` + `http://127.0.0.1:8010/rtcpushapi.html` + `/dashboard/performer.html` | PASS — `webrtcapi` delivers live `audio+video`; `rtcpushapi` auto-falls back to direct WebRTC when `:1985` relay is absent; dashboard Preview tab embeds the vendor page cleanly and preview `sessionid` syncs into `Suara` |
| Live console frontend slice | `cd src/dashboard/frontend && npm test -- --run src/tests/AIBrainPage.test.ts src/tests/live-console-panel.test.ts` | PASS — `8 passed` |
| Dashboard build recheck | `cd src/dashboard/frontend && npm run build` | PASS |
| Browser smoke (dashboard Q&A interrupt) | `http://127.0.0.1:8001/dashboard/?v=20260313b#/` | PASS — `Director Runtime` shows `SELLING` before chat, `PAUSED` after `Kirim Chat Simulasi`, then `POST /api/live-session/stop` returns `/api/pipeline/state` to `IDLE` |
| Test suite | `uv run pytest tests -q -p no:cacheprovider` | `255 passed, 1 skipped` |
| Pipeline verification | `uv run python scripts/verify_pipeline.py` | `11/11 layers passed` |
| Frontend build | `cd src/dashboard/frontend && npm run build` | PASS |
| Frontend unit tests | `cd src/dashboard/frontend && npm run test` | PASS — `67 passed` (19 test files) |
| Performer recovery suite | `cd src/dashboard/frontend && npm run test -- src/tests/performer-page.test.ts src/tests/action-receipt.test.ts src/tests/performer-preview-panel.test.ts src/tests/performer-validation-panel.test.ts src/tests/api.test.ts` | PASS — `18 passed` |
| Browser smoke test | `cd src/dashboard/frontend && npm run test:e2e -- e2e/dashboard.spec.ts` | PASS — `13 passed` |
| Real-mode readiness gate | `uv run python scripts/check_real_mode_readiness.py --json` | `READY FOR REAL MODE` |
| Fish-Speech operator validation | `uv run python scripts/manage.py validate fish-speech` | PASS — clone assets, config, canonical checkout/checkpoints, and sidecar reachability checks pass |
| Unified operator CLI | `uv run pytest tests/test_manage_cli.py tests/test_fish_speech_setup.py tests/test_menu_batch.py -q -p no:cacheprovider` | PASS — `34 passed`; nested setup/start/status/open commands and Windows menu wrapper are covered |
| Fish-Speech voice clone smoke | `MOCK_MODE=false uv run python -c "import asyncio, json; from src.dashboard.api import validate_voice_local_clone; print(json.dumps(asyncio.run(validate_voice_local_clone()), indent=2))"` | PASS — `resolved_engine=fish_speech`, `fallback_active=false`, Indonesian smoke synthesis returns `393260` bytes in `20884ms` on local GTX 1650 |
| FFmpeg runtime | `uv run python scripts/setup_ffmpeg.py` | portable FFmpeg verified in `tools/ffmpeg/bin/ffmpeg.exe` |
| MuseTalk assets | `uv run --extra livetalking python scripts/setup_musetalk_assets.py --sync-only` | models ready, canonical `musetalk_avatar1` ready, reference media present, `can_generate_avatar=True` |
| Unified setup flow | `uv run python scripts/manage.py setup all` | PASS — app, LiveTalking, MuseTalk model flow, and Fish-Speech bootstrap now resolve through one CLI surface |
| Fish-Speech bootstrap | `uv run python scripts/manage.py setup fish-speech` | PASS — upstream checkout pinned to `v1.5.1`, canonical checkpoints downloaded, dedicated UV env created at `external/fish-speech/runtime/.venv` |
| LiveTalking vendor imports | `uv run --extra livetalking python -c "import flask, flask_sockets, aiohttp_cors, transformers, diffusers, accelerate, omegaconf"` | PASS |
| LiveTalking smoke validation | `uv run python scripts/manage.py validate livetalking` | PASS — requested/resolved both `musetalk / musetalk_avatar1`, FFmpeg ready, vendor entrypoint/layout verified |
| Official real-mode operator slice | `uv run python scripts/manage.py serve --real` -> `POST /api/engine/livetalking/start` -> `GET /api/runtime/truth` | PASS — `face_runtime_mode=livetalking_local`, resolved runtime `musetalk / musetalk_avatar1`, `fallback_active=false` |
| Health summary alignment | `MOCK_MODE=false uv run python -c "import asyncio, json; from src.main import create_app; from src.dashboard.api import health_summary; create_app(); print(json.dumps(asyncio.run(health_summary()), indent=2))"` | PASS — `status=healthy`, `components.face_pipeline=healthy` |
| Voice runtime truth | `MOCK_MODE=false uv run python -c "import json; from src.dashboard.truth import get_runtime_truth_snapshot; print(json.dumps(get_runtime_truth_snapshot(), indent=2))"` | PASS — cold-start truth reports `voice_runtime_mode=unknown`, not a false `fish_speech_local` |
| Known noise | pytest temp cleanup on Windows; FastAPI `on_event` deprecation; 1 skipped vendor VAE import probe | warning/skip after pass, does not invalidate current audio findings |

## Active Milestones

### Face: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK` — `LOCAL VERIFIED`

See `docs/specs/local_vertical_slice_real_musetalk.md`

Active face runtime: **MuseTalk only** (Wav2Lip fallback does NOT count as milestone pass).

### Audio: `LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH` — `LOCAL VERIFIED`

See `docs/specs/local_audio_vertical_slice_fish_speech.md`

Active voice runtime: **Fish-Speech local sidecar** (Edge TTS fallback does NOT count as acceptance pass).
Voice clone assets required: `assets/voice/reference.wav` + `assets/voice/reference.txt`.
Current local caveat: functional direct-test validation now passes, but observed local smoke latency remains high (`~20.9s`) on the current GTX 1650 box.

## Overall Verdict

Face development baseline is **verified**.
Portable FFmpeg is **installed and working locally**.
Real product data source is **present** (`data/products.json`).
Canonical MuseTalk model storage is **ready**.
Canonical MuseTalk avatar is **generated** in the vendor path.
The official non-mock face operator slice is **verified locally**: runtime truth resolves to `musetalk / musetalk_avatar1` without fallback.
`LOCAL_VERTICAL_SLICE_REAL_MUSETALK` is now **LOCAL VERIFIED**.
Milestone audit is recorded at `docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md`.
Health summary alignment is now verified: `GET /api/health/summary` reports `face_pipeline=healthy` on readiness-complete non-mock local setup.
Fish-Speech audio integration code is **implemented and locally verified** for direct synthesis with clone assets and a reachable sidecar.
Unified operator setup/runtime commands are now centralized in `scripts/manage.py`, with canonical Fish-Speech layout rooted at `external/fish-speech/`.
Fish-Speech local install is now replicated in-repo with a dedicated sidecar UV env, so control-plane dependencies no longer get polluted by voice-sidecar packages.
The global real-mode readiness script is now **READY FOR REAL MODE** with voice prerequisites satisfied.
Runtime truth now resolves honestly to `voice_runtime_mode=fish_speech_local` after real synthesis, with `resolved_engine=fish_speech` and `fallback_active=false`.
Observed local smoke latency is improved but still above the live target on current hardware, so the next bottleneck is performance rather than basic correctness.
The TikTok-first dashboard control-plane slice is now **locally validated in mock mode** for durable stream targets, single live session state, simulated chat ingest, Q&A auto-pause, and director/session sync.

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
| Dashboard baseline | `LOCAL VERIFIED` | Current dashboard path works as operator entrypoint in local lab and is being evolved into a server-hosted ops controller |
| Svelte dashboard migration | `LOCAL VERIFIED` | Svelte build mounted at `/dashboard`, frontend unit tests pass, the operator workflow is consolidated into 6 surfaces, `Avatar & Suara` is restored as a 6-tab workspace, preview fallback is reachability-aware, standalone `performer.html` stays functional, requested/resolved LiveTalking state remains visible, Truth Bar provenance stays active, and operator actions now emit operator-first receipts across setup/live/stream/monitor surfaces |
| Brain layer | `LOCAL VERIFIED` | Covered by current test suite and verify pipeline |
| Voice orchestration | `LOCAL VERIFIED` | Fish-Speech health probe, binary request payload, runtime truth, readiness, local clone smoke validation, and the unified Voice Lab browser flow now pass; `performer.html` verifies explicit `Indonesia / English` controls, local artifact management (`play / download / delete / clear`), and the current attach proof still grounded on the `wav2lip` preview path |
| Composition / stream / chat / commerce | `LOCAL VERIFIED` | Covered by tests and verify pipeline |
| FFmpeg runtime | `LOCAL VERIFIED` | Project-local FFmpeg installed at `tools/ffmpeg/bin/ffmpeg.exe` |
| LiveTalking vendor repo present | `LOCAL VERIFIED` | Sidecar code exists in `external/livetalking` |
| LiveTalking runtime contract | `LOCAL VERIFIED` | UV dependency blocker is fixed, sidecar starts through the operator path, and the vendor process runs with `--model musetalk --avatar_id musetalk_avatar1` |
| LiveTalking browser preview pages | `LOCAL VERIFIED` | Dedicated sidecar env works through dashboard start, `webrtcapi.html` is live, `rtcpushapi.html` now degrades gracefully to direct WebRTC when no local relay is running on `:1985`, and `webrtcapi` now self-bridges `sessionid` back to the dashboard even if an older `client.js` was cached in the browser |
| MuseTalk models inside vendor LiveTalking | `LOCAL VERIFIED` | Weights normalized into `external/livetalking/models/musetalk` |
| MuseTalk avatar runtime asset | `LOCAL VERIFIED` | Canonical `musetalk_avatar1` exists in `external/livetalking/data/avatars/musetalk_avatar1` and resolves without fallback |
| Wav2Lip inside vendor LiveTalking | `LOCAL VERIFIED` | Legacy fallback still active |
| Ultralight inside vendor LiveTalking | `LOCAL VERIFIED` | Active vendor low-resource path |
| ER-NeRF inside vendor LiveTalking | `TARGET ONLY` | Advertised in docs, but runtime branch is commented out |
| GFPGAN inside vendor LiveTalking | `TARGET ONLY` | Claimed in project docs, not found in vendor runtime |
| `src/face/pipeline.py` MuseTalk path | `PARTIAL` | Still raises `NotImplementedError` for production GPU path |
| `src/face/pipeline.py` GFPGAN path | `PARTIAL` | Still raises `NotImplementedError` |
| Unified dashboard for full system validation | `LOCAL VERIFIED` | Operator shell is live, requested/resolved LiveTalking state visible in Engine panel, Truth Bar with runtime truth active, and the ops-controller surfaces now include ops summary, voice operations, validation expansion, incidents, and resource-focused monitoring |
| Dashboard Single Truth Real Validation | `LOCAL VERIFIED` | Realtime dashboard store, Validation Console, performer reconciliation, evidence history, preview target probing, and operator controls are locally verified for both the MuseTalk face slice and the local Fish-Speech direct-test voice slice |
| TikTok-first dashboard control-plane slice | `LOCAL VERIFIED` | Single active live session, persisted stream targets, SQLite product/session pool, simulated chat ingest -> `SOFT_PAUSED_FOR_QNA`, and `Director Runtime` sync verified in browser against the server-hosted dashboard |
| RTMP live slice to TikTok/Shopee | `PENDING GPU` | Needs end-to-end run with real target |
| 18-24 hour stability layer | `PENDING GPU` | Not validated yet |

## Current Architecture Truth

- `videoliveai` is the main control plane.
- `external/livetalking` is a vendor sidecar, not the whole system.
- `/dashboard` is the only operator dashboard.
- `localhost:8010/*.html` are vendor debug pages only.
- `GPT-SoVITS` / `CosyVoice` belong to the voice layer, not the face engine.

## Immediate Priorities

1. Reduce Fish-Speech latency on the local path so it approaches live-stream expectations instead of `~20.9s`.
2. Capture and store a dedicated local audio audit artifact for the first verified Fish-Speech voice slice.
3. Continue `Humanization Minimum` with the now-working audio + face baseline.
4. Run RTMP dry-run and short real live test after audio latency handling is defined.

## Pending GPU / Production Work

- Acquire production avatar and voice assets
- Regenerate MuseTalk avatar from final production reference media if the identity asset changes
- Validate MuseTalk path on real GPU
- **Voice path decided**: Fish-Speech local sidecar is the acceptance path (see `docs/specs/local_audio_vertical_slice_fish_speech.md`)
- Validate RTMP output against test target
- Add restart and recovery policy for long sessions

## Source Of Truth

- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [dashboard_truth_model.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/dashboard_truth_model.md)
- [local_vertical_slice_real_musetalk.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/local_vertical_slice_real_musetalk.md)
- [musetalk_asset_contract.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/musetalk_asset_contract.md)
- [humanization_minimum_contract.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/humanization_minimum_contract.md)
- [local_audio_vertical_slice_fish_speech.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/local_audio_vertical_slice_fish_speech.md)
- [AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md)
- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)
