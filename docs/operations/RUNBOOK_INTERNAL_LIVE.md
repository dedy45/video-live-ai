# Operator Runbook — Internal Live

> **Status**: Active
> **Date**: 2026-03-07

## Before Stream

1. Open dashboard: `http://localhost:8000/dashboard`
2. Check readiness: `GET /api/readiness`
3. Verify all checks pass (especially: config, database, LiveTalking, models)
4. Confirm RTMP target is configured (if streaming to TikTok/Shopee)

```bash
# Quick CLI check
uv run python scripts/smoke_livetalking.py
```

## Start Engine

1. From dashboard: click "Start Engine" on Engine tab
2. Or via API: `POST /api/engine/livetalking/start`
3. Wait for status to show `running`
4. Verify port 8010 responds

## Validate Readiness

1. Check readiness endpoint: `GET /api/readiness`
2. All blocking issues must be resolved
3. Optional: run validation endpoints:
   - `POST /api/validate/mock-stack`
   - `POST /api/validate/livetalking-engine`
   - `POST /api/validate/rtmp-target`

## Run Live Slice

1. Open preview: `http://localhost:8010/webrtcapi.html`
2. Verify avatar renders
3. Test text-to-speech pipeline
4. If RTMP configured: `POST /api/stream/start`
5. Monitor stream status on dashboard

## Recover from Common Failures

| Problem | Action |
|---------|--------|
| Engine not starting | Check logs: `GET /api/engine/livetalking/logs` |
| Port in use | Kill process on port 8010 |
| No video output | Check model/avatar paths |
| Stream failed | Check RTMP URL/key in .env |
| System unresponsive | `POST /api/emergency-stop`, then `/api/emergency-reset` |

## Stop Safely

1. Stop stream: `POST /api/stream/stop`
2. Stop engine: `POST /api/engine/livetalking/stop`
3. Verify engine status shows `stopped`
4. Optional: check logs for any errors during session
