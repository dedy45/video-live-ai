# Process Recovery Policy

> **Status**: Active
> **Date**: 2026-03-07

## Policy

When the LiveTalking engine process crashes or becomes unresponsive:

1. **Detect crash**: Process manager checks `poll()` on every status request
2. **Mark unhealthy**: State transitions to `ERROR` with exit code recorded
3. **Controlled restart**: Operator can restart from dashboard or API
4. **Backoff**: If auto-restart is enabled, use exponential backoff

## Restart Backoff Schedule

| Attempt | Wait | Max |
|---------|------|-----|
| 1 | 2s | - |
| 2 | 4s | - |
| 3 | 8s | - |
| 4 | 16s | - |
| 5+ | 30s | 30s (cap) |

## Recovery Actions

| Failure Type | Auto-Recovery | Manual Action |
|-------------|---------------|---------------|
| Clean exit (code 0) | No | Restart from dashboard |
| Crash (non-zero) | Log + mark error | Check logs, restart |
| Port conflict | No | Kill conflicting process |
| OOM | No | Reduce resolution/model |

## Implementation

- `src/face/livetalking_manager.py` handles process lifecycle
- `src/utils/process_supervisor.py` (future) for auto-restart with backoff
- Dashboard shows last error and recovery options
