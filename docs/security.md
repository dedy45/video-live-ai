# Security Policy

> **Version**: 0.3.7
> **Last Updated**: 2026-03-06 14:00
> Kebijakan keamanan untuk AI Live Commerce Platform.

## Credential Management

- **NEVER** hardcode API keys dalam source code
- Gunakan `.env` file untuk local development (sudah di `.gitignore`)
- Gunakan environment variables di server production
- Rotasi API keys setiap 90 hari
- Gunakan `.env.example` sebagai template (tanpa values)

## API Keys Required

| Service | Env Variable        | Purpose           | Required |
| ------- | ------------------- | ----------------- | -------- |
| Gemini  | `GEMINI_API_KEY`    | Fast chat replies | ✅       |
| Claude  | `ANTHROPIC_API_KEY` | Script generation | ⬜ opt   |
| GPT-4o  | `OPENAI_API_KEY`    | Emotion detection | ⬜ opt   |
| Groq    | `GROQ_API_KEY`      | Ultra-fast chat   | ⬜ opt   |
| TikTok  | `TIKTOK_SESSION_ID` | Chat monitoring   | ✅       |
| Shopee  | `SHOPEE_API_KEY`    | Chat monitoring   | ⬜ opt   |
| Sentry  | `SENTRY_DSN`        | Error Tracking    | ⬜ opt   |

## LiveTalking Configuration

| Variable | Default | Purpose |
|----------|---------|---------|
| `LIVETALKING_ENABLED` | `false` | Enable LiveTalking engine |
| `LIVETALKING_REFERENCE_VIDEO` | `assets/avatar/reference.mp4` | 5-min reference video |
| `LIVETALKING_REFERENCE_AUDIO` | `assets/avatar/reference.wav` | 3-10s voice sample |
| `LIVETALKING_USE_WEBRTC` | `false` | Enable WebRTC streaming |
| `LIVETALKING_USE_RTMP` | `true` | Enable RTMP streaming |
| `LIVETALKING_FPS` | `30` | Target frames per second |
| `LIVETALKING_RESOLUTION` | `512,512` | Output resolution (W,H) |

## Dashboard Authentication

| Variable             | Default    | Purpose         |
| -------------------- | ---------- | --------------- |
| `DASHBOARD_USERNAME` | `admin`    | HTTP Basic auth |
| `DASHBOARD_PASSWORD` | `changeme` | HTTP Basic auth |

> ⚠️ **PENTING**: Ganti `DASHBOARD_PASSWORD` sebelum production!

Dashboard API endpoints yang memerlukan auth:

- `GET /api/status` — System state
- `POST /api/stream/start|stop` — Stream control
- `POST /api/emergency-stop` — Emergency kill
- `GET /api/metrics` — JSON Metrics data
- `GET /api/products` — Product list

Endpoints TANPA auth (monitoring & internal tooling):

- `GET /diagnostic/health` — Simple health check
- `GET /api/health/summary` — Health summary
- `GET /metrics` — Prometheus metrics exporter (Internal Network only recommended)
- `WS /api/ws/dashboard` — WebSocket updates

## Content Safety

- Semua output LLM melewati `SafetyFilter` sebelum TTS
- Blacklist keyword lokal (bahasa kasar, kompetitor, etc.)
- Excessive caps detection (>50% caps = flagged)
- Incident log dicatat via structlog
- Safety check WAJIB sebelum TTS synthesis

## Network Security

- HTTPS untuk semua API calls eksternal (LLM providers)
- Dashboard production wajib dipublish lewat reverse proxy dengan auth dan TLS
- Jangan expose FastAPI dashboard langsung ke internet tanpa proxy boundary
- CORS policy untuk whitelist origins (configurable via `config.yaml`)
- Rate limiting bisa ditambahkan via FastAPI middleware
- WebSocket connections untuk production sebaiknya ikut berada di belakang reverse proxy policy yang sama
- Browser disconnect tidak boleh dianggap sebagai stop signal untuk proses live yang berjalan di server

## Mock Mode Security

- Mock Mode (`MOCK_MODE=true`) aman untuk local development
- TIDAK memerlukan API keys
- TIDAK melakukan network calls
- Output adalah placeholder data saja

## Git Repository Security

**Repository**: https://github.com/dedy45/video-live-ai.git

**What is committed:**
- ✅ Source code (`src/`, `tests/`, `scripts/`)
- ✅ Documentation (`docs/`, `*.md`)
- ✅ Config templates (`.env.example`, `config.yaml`)
- ✅ Sample data (`data/sample_products.json`)

**What is NOT committed (in .gitignore):**
- ❌ `.venv/` — UV virtual environment (recreate with `uv venv`)
- ❌ `.env` — Secrets and API keys
- ❌ `models/` — Large model weights (download separately)
- ❌ `data/*.db` — Runtime database
- ❌ `data/logs/` — Application logs
- ❌ `assets/avatar/` — User-specific reference materials
- ❌ `external/livetalking/` — Git submodule (clone with `git submodule update --init`)

**Setup after clone:**
```bash
git clone https://github.com/dedy45/video-live-ai.git
cd video-live-ai
cp .env.example .env  # Edit with your API keys
uv venv
uv pip install -e ".[livetalking]"
git submodule update --init  # Clone LiveTalking
```
