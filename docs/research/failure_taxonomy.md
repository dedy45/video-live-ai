# Failure Taxonomy

> **Status**: Active
> **Date**: 2026-03-07

## Failure Classes

| Class | Severity | Symptom | Diagnosis | Recovery |
|-------|----------|---------|-----------|----------|
| **Config error** | Blocking | App won't start | Check `config.yaml` and `.env` | Fix config, restart |
| **Missing model** | Blocking | Engine won't start | Smoke test fails on model check | Run setup script |
| **Missing avatar** | Blocking | Engine starts but no output | Avatar path check fails | Download/prepare avatar |
| **Port collision** | Blocking | Engine can't bind port | Port check shows IN USE | Kill process on port |
| **FFmpeg unavailable** | Warning | Stream can't start | `which ffmpeg` returns empty | Install FFmpeg |
| **RTMP rejected** | Warning | Stream fails | FFmpeg error log | Check URL/key in .env |
| **Engine crash** | Error | Process exits unexpectedly | Non-zero exit code | Check logs, restart |
| **GPU OOM** | Error | Engine crashes during render | CUDA out of memory error | Reduce resolution |
| **LLM timeout** | Warning | No AI response | LLM health check fails | Check API keys, fallback |
| **Database corrupt** | Error | Data operations fail | DB health check fails | Restore from backup |

## Detection Methods

| Method | Component | Endpoint |
|--------|-----------|----------|
| Health check | All | `GET /api/health/summary` |
| Readiness check | Pre-flight | `GET /api/readiness` |
| Engine status | LiveTalking | `GET /api/engine/livetalking/status` |
| Process poll | LiveTalking | Manager.is_running() |
| Smoke test | LiveTalking | `scripts/smoke_livetalking.py` |

## Alert Levels

| Level | Action | Example |
|-------|--------|---------|
| **Info** | Log only | Engine started normally |
| **Warning** | Dashboard indicator | FFmpeg not found |
| **Error** | Dashboard alert | Engine crashed |
| **Critical** | Emergency stop | Unrecoverable failure |
