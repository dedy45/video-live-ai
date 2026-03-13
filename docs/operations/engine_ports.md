# Engine Ports

> **Status**: Active
> **Date**: 2026-03-07

## Port Assignments

| Service | Default Port | Env Variable | Protocol |
|---------|-------------|--------------|----------|
| FastAPI main app | `8001` | `DASHBOARD_PORT` | HTTP/WS |
| LiveTalking engine | `8010` | `LIVETALKING_PORT` | HTTP/WebRTC |
| Ollama (local LLM) | `11434` | `LOCAL_LLM_URL` | HTTP |
| Gemini proxy | `8091` | `LOCAL_GEMINI_URL` | HTTP |

## Transport Modes

| Mode | Flag | Use Case |
|------|------|----------|
| `webrtc` | `--transport webrtc` | Browser preview |
| `rtmp` | `--transport rtmp` | TikTok/Shopee streaming |
| `rtcpush` | `--transport rtcpush` | Server-side push |

## Configuration Variables

```bash
# .env settings
LIVETALKING_PORT=8010
LIVETALKING_TRANSPORT=webrtc
LIVETALKING_MODEL=wav2lip
LIVETALKING_AVATAR_ID=wav2lip256_avatar1
```
