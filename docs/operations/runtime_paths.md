# Runtime Paths — Source of Truth

> **Status**: Active
> **Date**: 2026-03-07

## Path Definitions

| Resource | Path | Notes |
|----------|------|-------|
| **Model root** | `external/livetalking/models/` | All runtime model weights |
| **Avatar root** | `external/livetalking/data/avatars/` | Avatar assets for rendering |
| **Config file** | `config/config.yaml` | System configuration |
| **Environment** | `.env` | API keys and runtime settings |
| **Database** | `data/videoliveai.db` | SQLite database |
| **Logs** | `data/logs/app.log` | Application logs |
| **Frontend** | `src/dashboard/frontend/` | Svelte dashboard build |

## Port Assignments

| Service | Port | Variable |
|---------|------|----------|
| **FastAPI (main app)** | `8001` | `DASHBOARD_PORT` |
| **LiveTalking engine** | `8010` | `LIVETALKING_PORT` |
| **Local LLM (Ollama)** | `11434` | `LOCAL_LLM_URL` |
| **Local Gemini Proxy** | `8091` | `LOCAL_GEMINI_URL` |

## URL Map

| URL | Purpose | Who uses it |
|-----|---------|-------------|
| `http://localhost:8001/dashboard` | Operator dashboard | Operators |
| `http://localhost:8001/docs` | API documentation | Developers |
| `http://localhost:8001/diagnostic/` | System diagnostic | Operators/Devs |
| `http://localhost:8010/webrtcapi.html` | LiveTalking debug (WebRTC) | Developers only |
| `http://localhost:8010/rtcpushapi.html` | LiveTalking debug (RTC push) | Developers only |

## Official Commands

### Setup

```bash
# Install all dependencies
uv sync --extra dev

# Copy environment template
cp .env.example .env
```

### Development

```bash
# Run in mock mode (no GPU)
MOCK_MODE=true uv run python -m src.main

# Windows equivalent
set MOCK_MODE=true && uv run python -m src.main
```

### Testing

```bash
# Run all tests
uv run pytest tests -q -p no:cacheprovider

# Run specific test file
uv run pytest tests/test_livetalking_integration.py -v

# Skip GPU integration tests
uv run pytest tests -v -m "not integration"
```

### Verification

```bash
# Pipeline verification
uv run python scripts/verify_pipeline.py --verbose

# Lint + validation
cmd /c scripts\validate.bat

# LiveTalking smoke test
uv run python scripts/smoke_livetalking.py
```

### Production

```bash
# Start full system
uv run python -m src.main

# Ubuntu server equivalent
uv sync --extra dev
uv run python -m src.main
```
