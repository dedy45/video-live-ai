# Security Policy

> **Version**: 0.4.1
> **Last Updated**: 2026-03-03 11:35
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
- Dashboard memerlukan HTTP Basic auth
- CORS policy untuk whitelist origins (configurable via `config.yaml`)
- Rate limiting bisa ditambahkan via FastAPI middleware
- WebSocket connections tanpa auth (data non-sensitif)

## Mock Mode Security

- Mock Mode (`MOCK_MODE=true`) aman untuk local development
- TIDAK memerlukan API keys
- TIDAK melakukan network calls
- Output adalah placeholder data saja
