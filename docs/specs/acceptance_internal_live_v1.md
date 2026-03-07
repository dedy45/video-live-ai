# Internal Acceptance Checklist — Live v1

> **Status**: Active
> **Date**: 2026-03-07

## Checklist

### Install
- [ ] `uv sync --extra dev` completes without errors
- [ ] `.env` file exists with required settings
- [ ] `external/livetalking/app.py` exists (git submodule initialized)

### Readiness
- [ ] `GET /api/readiness` returns `overall_status: ready` or `degraded`
- [ ] No blocking issues reported
- [ ] Database healthy
- [ ] Config loaded

### Preview
- [ ] LiveTalking engine starts from dashboard
- [ ] `http://localhost:8010/webrtcapi.html` loads
- [ ] Avatar renders in browser preview

### Engine Control
- [ ] `POST /api/engine/livetalking/start` starts engine
- [ ] `GET /api/engine/livetalking/status` shows `running`
- [ ] `POST /api/engine/livetalking/stop` stops engine
- [ ] `GET /api/engine/livetalking/logs` returns log lines

### RTMP Dry-Run
- [ ] `POST /api/validate/rtmp-target` returns check results
- [ ] FFmpeg is available
- [ ] RTMP URL and stream key configured (or intentionally skipped)

### Live Slice
- [ ] Text input produces avatar speech/video
- [ ] Stream can start to test endpoint
- [ ] Stream can stop gracefully

### Recovery
- [ ] Engine restart works after stop
- [ ] Emergency stop halts all operations
- [ ] Emergency reset allows restart
- [ ] Error states are diagnosable from dashboard

## Verification Commands

```bash
# All tests pass
uv run pytest tests -q -p no:cacheprovider

# Smoke test passes
uv run python scripts/smoke_livetalking.py

# Pipeline verification
uv run python scripts/verify_pipeline.py --verbose

# Validation
cmd /c scripts\validate.bat
```
