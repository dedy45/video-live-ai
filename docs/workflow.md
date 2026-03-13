# Development Workflow

> Last updated: 2026-03-11
> Package manager: `uv` only

## Official Commands

```bash
uv sync --extra dev
uv run python scripts/manage.py setup all
uv run python scripts/manage.py setup app
uv run python scripts/manage.py setup livetalking
uv run python scripts/manage.py setup musetalk-model
uv run python scripts/manage.py setup fish-speech
uv run python scripts/manage.py status all
uv run python scripts/manage.py status fish-speech
uv run python scripts/manage.py health
uv run python scripts/manage.py validate tests
uv run python scripts/manage.py validate livetalking
uv run python scripts/manage.py validate fish-speech
uv run python scripts/manage.py start fish-speech
uv run python scripts/manage.py start livetalking --mode musetalk
uv run python scripts/manage.py open performer
uv run python scripts/manage.py open monitor
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py
uv run python scripts/manage.py serve --mock
uv run python scripts/manage.py serve --real
```

Windows operator shortcut:

```bat
scripts\menu.bat
```

## Active Milestones

### Face: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK` — `LOCAL VERIFIED`

MuseTalk is the only acceptance path. Wav2Lip fallback is visible but does NOT count as milestone completion.

### Audio: `LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH` — `LOCAL VERIFIED`

Fish-Speech local sidecar is the only acceptance path. Edge TTS fallback does NOT count as acceptance pass.
See `docs/specs/local_audio_vertical_slice_fish_speech.md`.

## Current Validation Snapshot

- `cd src/dashboard/frontend && npm run build` -> PASS
- `cd src/dashboard/frontend && npm run test` -> PASS (`67 passed`, 19 test files)
- `cd src/dashboard/frontend && npm run test:e2e` -> BLOCKED on the current Windows host because the Playwright webServer startup hits a local port `8001` bind conflict before the browser phase starts
- `uv run pytest tests -q -p no:cacheprovider` -> `255 passed, 1 skipped`
- `uv run python scripts/verify_pipeline.py` -> `11/11 layers passed`
- `uv run python scripts/check_real_mode_readiness.py --json` -> `READY FOR REAL MODE`
- `uv run python scripts/manage.py setup all` -> READY as the single Python setup entrypoint; real Fish-Speech start still depends on a populated canonical checkout and checkpoints
- `uv run python scripts/manage.py setup fish-speech` -> PASS; now clones pinned Fish-Speech `v1.5.1`, hydrates canonical checkpoints, and builds a dedicated sidecar UV env under `external/fish-speech/runtime/.venv`
- `uv run --extra livetalking python -c "import flask, flask_sockets, aiohttp_cors, transformers, diffusers, accelerate, omegaconf"` -> PASS
- `uv run --extra livetalking python scripts/setup_musetalk_assets.py --sync-only` -> `Models ready: True`, `Avatar ready: True`
- `uv run python scripts/manage.py validate livetalking` -> PASS with requested/resolved both `musetalk / musetalk_avatar1`
- `uv run python scripts/manage.py validate fish-speech` -> PASS
- `MOCK_MODE=false uv run python -c "import asyncio, json; from src.dashboard.api import validate_voice_local_clone; print(json.dumps(asyncio.run(validate_voice_local_clone()), indent=2))"` -> PASS (`voice_runtime_mode=fish_speech_local`, `fallback_active=false`, local smoke latency observed around `20.9s`)
- `MOCK_MODE=false uv run python -c "import json; from src.dashboard.truth import get_runtime_truth_snapshot; print(json.dumps(get_runtime_truth_snapshot(), indent=2))"` -> cold-start truth reports `voice_runtime_mode=unknown`
- official non-mock face operator slice is now verified: `serve --real`, engine start, and `runtime_truth` resolve to MuseTalk with `fallback_active=false`
- health summary alignment is verified: `GET /api/health/summary` now reports `face_pipeline=healthy` on readiness-complete non-mock setup
- `/dashboard` is the primary operator UI
- operator workflow is now fixed to 6 surfaces, with validation + diagnostics embedded into `Setup & Validasi` and `Monitor & Insiden`
- standalone operator entrypoints now resolve to `index.html`, `setup.html`, `products.html`, `performer.html`, `stream.html`, and `monitor.html`
- `localhost:8010/*.html` are vendor debug pages only

## Next Phase After Milestone

The MuseTalk face slice and Fish-Speech direct-test audio slice are now locally verified. The next work shifts to performance realism and live execution:

```bash
uv run python scripts/manage.py validate fish-speech
uv run python scripts/check_real_mode_readiness.py --json
```

Follow-up acceptance now shifts to:

- keep the local Fish-Speech sidecar healthy and capture/store the verified audio evidence
- reduce current local Fish-Speech latency from the observed `~20.9s` direct-test path
- maintain health-summary alignment (`face_pipeline` stays healthy when prerequisites are present)
- implement humanization minimum overlays on top of the now-working face + voice baseline
- RTMP dry-run and short real live test criteria are frozen before server rollout

## Local Development

```bash
cd videoliveai
uv sync --extra dev
uv run python scripts/manage.py serve --mock
```

## Operator Runtime Model

- Local machine remains the **truth lab** for mock mode, slice validation, and dry-run checks.
- Production/live execution moves to a **server-hosted ops controller** served from `/dashboard`.
- FastAPI remains the control plane, while Fish-Speech and LiveTalking remain sidecars.
- Browser disconnect must not stop a live session running on the server host.

### Operator URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8001/dashboard` | Local operator dashboard / truth lab |
| `http://SERVER_IP_OR_DOMAIN/dashboard` | Server-hosted ops controller |
| `http://localhost:8001/docs` | FastAPI schema |
| `http://localhost:8001/diagnostic/` | Diagnostics |
| `http://localhost:8010/*.html` | LiveTalking vendor debug pages |

> Production deployment requires a reverse proxy in front of FastAPI for auth and TLS.

## Verification

```bash
cd src/dashboard/frontend && npm run build
cd src/dashboard/frontend && npm run test
cd src/dashboard/frontend && npx playwright test
uv run pytest tests -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -v
uv run pytest tests/test_livetalking_integration.py -v
uv run python scripts/check_real_mode_readiness.py --json
uv run python scripts/verify_pipeline.py
uv run ruff check src/
```

## GPU / Remote Work

Use a Linux GPU host only for work that cannot be trusted in mock mode:

- MuseTalk runtime validation
- RTMP push validation
- long-session stability
- real TTS / real avatar asset validation

```bash
REMOTE_HOST=IP_ADDRESS REMOTE_PORT=22 REMOTE_USER=root scripts/remote_sync.sh
REMOTE_HOST=IP_ADDRESS REMOTE_PORT=22 REMOTE_USER=root scripts/remote_run.sh
```

## Rules

- Always use `uv run`, never plain `python` as the documented command path.
- Direct ad hoc LiveTalking commands outside `manage.py` must use `uv run --extra livetalking ...`.
- `scripts/manage.py` is the single source of truth for setup, start, stop, status, validate, and open flows.
- `scripts/menu.bat` is a thin Windows wrapper only; do not put real install/runtime logic in root `.bat` files.
- `scripts/manage.py` now opts into `--extra livetalking` internally for LiveTalking setup, validation, real-mode app launch, and vendor runtime starts.
- Fish-Speech acceptance requires local clone assets and a local sidecar; do not treat `edge_tts` fallback as milestone completion.
- Treat `external/livetalking/app.py` as the vendor engine entrypoint.
- Treat `external/fish-speech/` as the canonical Fish-Speech sidecar root.
- Treat `external/fish-speech/runtime/.venv/` as the only allowed Fish-Speech Python env; do not install Fish-Speech into the control-plane `.venv`.
- Do not document `conda` as an active path.
- Do not treat vendor HTML pages as the main dashboard.

## Related Docs

- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [docs/README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/README.md)
- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
