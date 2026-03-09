# Development Workflow

> Last updated: 2026-03-09
> Package manager: `uv` only

## Official Commands

```bash
uv sync --extra dev
uv run python scripts/manage.py status
uv run python scripts/manage.py health
uv run python scripts/manage.py validate tests
uv run python scripts/manage.py validate livetalking
uv run python scripts/manage.py setup-livetalking --skip-models
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py
uv run python scripts/manage.py serve --mock
uv run python scripts/manage.py serve --real
```

Windows operator shortcut:

```bat
scripts\menu.bat
```

## Active Milestone

**`LOCAL_VERTICAL_SLICE_REAL_MUSETALK`** — MuseTalk is the only acceptance path.
Wav2Lip fallback is visible but does NOT count as milestone completion.

## Current Validation Snapshot

- `cd src/dashboard/frontend && npm run build` -> PASS
- `cd src/dashboard/frontend && npm run test` -> PASS (`40 passed`, 5 test files)
- `cd src/dashboard/frontend && npx playwright test` -> PASS (`8 passed`)
- `uv run pytest tests -q -p no:cacheprovider` -> `161 passed`
- `uv run python scripts/verify_pipeline.py` -> `11/11 layers passed`
- `uv run python scripts/check_real_mode_readiness.py --json` -> `READY FOR REAL MODE` (11/11 checks passed), but the command is only a prerequisite gate and does not complete the MuseTalk milestone
- `uv sync --extra dev` followed by `uv run python scripts/manage.py setup-livetalking --skip-models` -> PASS; setup now rehydrates vendor deps in the UV env and treats no-GPU machines as advisory warning only
- `uv run --extra livetalking python -c "import flask, flask_sockets, aiohttp_cors, transformers, diffusers, accelerate, omegaconf"` -> PASS
- `uv run python scripts/manage.py validate livetalking` -> PASS with truthful Wav2Lip fallback (milestone requires musetalk resolution)
- non-mock LiveTalking process now spawns past the old Flask/import blocker; on this CPU/no-GPU Windows box port `8010` became reachable after vendor image scan/model warmup in about 20 seconds
- current gaps remain explicit: `resolved_model=wav2lip`, canonical `musetalk_avatar1` is still missing, and readiness truth still reports `face_runtime_mode=mock`
- `/dashboard` is the primary operator UI
- `localhost:8010/*.html` are vendor debug pages only

## Remaining Gap To Milestone

The next required operator proof is still:

```bash
uv run python scripts/manage.py setup-livetalking --skip-models
uv run python scripts/manage.py serve --real
uv run python scripts/manage.py health --json
uv run python scripts/manage.py validate livetalking
```

Acceptance stays blocked until:

- `resolved_model=musetalk`
- `resolved_avatar_id=musetalk_avatar1`
- runtime truth no longer reports `face_runtime_mode=mock`
- the audit captures the official operator slice, not just prerequisite checks

## Local Development

```bash
cd videoliveai
uv sync --extra dev
uv run python scripts/manage.py serve --mock
```

### Local URLs

| URL | Purpose |
|-----|---------|
| `http://localhost:8000/dashboard` | Operator dashboard |
| `http://localhost:8000/docs` | FastAPI schema |
| `http://localhost:8000/diagnostic/` | Diagnostics |
| `http://localhost:8010/*.html` | LiveTalking vendor debug pages |

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
- `scripts/manage.py` now opts into `--extra livetalking` internally for LiveTalking setup, validation, and real-mode app launch.
- Treat `external/livetalking/app.py` as the vendor engine entrypoint.
- Do not document `conda` as an active path.
- Do not treat vendor HTML pages as the main dashboard.

## Related Docs

- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [docs/README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/README.md)
- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
