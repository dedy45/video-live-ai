# Development Workflow

> Last updated: 2026-03-07
> Package manager: `uv` only

## Official Commands

```bash
uv sync --extra dev
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py
MOCK_MODE=true uv run python -m src.main
```

## Current Validation Snapshot

- `uv run pytest tests -q -p no:cacheprovider` -> `89 passed`
- `uv run python scripts/verify_pipeline.py` -> `11/11 layers PASS`
- `/dashboard` is the primary operator UI
- `localhost:8010/*.html` are vendor debug pages only

## Local Development

```bash
cd videoliveai
uv sync --extra dev
MOCK_MODE=true uv run python -m src.main
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
uv run pytest tests -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -v
uv run pytest tests/test_livetalking_integration.py -v
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
- Treat `external/livetalking/app.py` as the vendor engine entrypoint.
- Do not document `conda` as an active path.
- Do not treat vendor HTML pages as the main dashboard.

## Related Docs

- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [docs/README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/README.md)
- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
