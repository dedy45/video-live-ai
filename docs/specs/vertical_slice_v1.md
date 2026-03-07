# Vertical Slice v1 — "Can Go Live" Test

> **Status**: Active
> **Date**: 2026-03-07

## Slice Definition

The minimum end-to-end flow that proves the system can go live:

1. Start LiveTalking engine (from dashboard or API)
2. Open preview (WebRTC in browser)
3. Send text/script to engine
4. Avatar outputs speech/video
5. Validate RTMP target configuration
6. Attempt stream start to test endpoint

## Success Criteria

| Step | Validation | Pass/Fail |
|------|-----------|-----------|
| Engine starts | `GET /api/engine/livetalking/status` returns `running` | |
| Preview accessible | `http://localhost:8010/webrtcapi.html` loads | |
| Text accepted | Engine processes text input | |
| Video output | Avatar renders frames | |
| RTMP config valid | `POST /api/validate/rtmp-target` returns `pass` | |
| Stream attempt | `POST /api/stream/start` succeeds | |

## Verification Command

```bash
uv run python scripts/validate_live_slice.py
```

## Failure Modes

| Failure | Diagnosis | Recovery |
|---------|-----------|----------|
| Engine won't start | Check logs, model paths | Run smoke test |
| No video output | GPU/model issue | Use mock mode |
| RTMP rejected | Wrong URL/key | Check .env |
| Port conflict | Another process on 8010 | Kill process |
