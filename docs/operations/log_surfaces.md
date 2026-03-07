# Log Surfaces

> **Status**: Active
> **Date**: 2026-03-07

## Log Sources

| Source | Location | Format | Access |
|--------|----------|--------|--------|
| **App logs** | `data/logs/app.log` | JSON (structlog) | File, stdout |
| **LiveTalking logs** | In-memory buffer | Plain text | `GET /api/engine/livetalking/logs` |
| **Validation logs** | Stdout | Plain text | CLI output |

## App Logs (structlog)

- Format: JSON with `timestamp`, `log_level`, `component`, `event`
- Components: `main`, `dashboard.api`, `livetalking`, `livetalking.manager`, `stream`, `health`, etc.
- File: `data/logs/app.log` (rotated every 30 days)
- Console: stdout (when running with `uv run python -m src.main`)

## LiveTalking Engine Logs

- Captured from subprocess stderr
- Stored in ring buffer (max 500 lines)
- Access: `GET /api/engine/livetalking/logs?tail=100`
- Contains: engine startup, model loading, frame processing, errors

## Validation Logs

- `scripts/verify_pipeline.py` — pipeline layer verification
- `scripts/smoke_livetalking.py` — engine readiness check
- `scripts/validate.bat` — lint + import checks
- Output: stdout (not persisted)

## Log Levels

| Level | Usage |
|-------|-------|
| `DEBUG` | Development details |
| `INFO` | Normal operations |
| `WARNING` | Degraded state, recoverable |
| `ERROR` | Operation failed |
| `CRITICAL` | Emergency stop, unrecoverable |
