# AI Live Commerce Platform — Architecture

> **Version**: 0.4.1
> **Last Updated**: 2026-03-03 11:35
> **Updated By**: Agent (Antigravity)

## System Overview

AI Live Commerce Platform menggunakan arsitektur **7-layer** yang dirancang untuk live streaming commerce otomatis dengan AI avatar. Sistem dilengkapi with Dashboard API, Analytics Engine, Centralized Health System, dan Robust Resilience Layer.

## Layer Architecture

```
┌─────────────────────────────────────────────────┐
│          DASHBOARD (REST API + WebSocket)        │
│  13 endpoints | Svelte UI | Analytics           │
├─────────────────────────────────────────────────┤
│              ORCHESTRATOR (State Machine)        │
│  SELLING ↔ REACTING ↔ ENGAGING                  │
├─────────────────────────────────────────────────┤
│  Layer 1: INTELLIGENCE (LiteLLM Brain)           │
│  LiteLLM → Gemini|Claude|GPT-4o|Groq|Chutes   │
│  Local Gemini Proxy (8091) | Ollama (11434)     │
├─────────────────────────────────────────────────┤
│  Layer 2: VOICE (TTS Engines)                   │
│  Fish Speech (GPU) | Edge TTS (cloud backup)    │
├─────────────────────────────────────────────────┤
│  Layer 3: FACE (Avatar Rendering)               │
│  MuseTalk | GFPGAN | Temporal Smoother          │
├─────────────────────────────────────────────────┤
│  Layer 4: COMPOSITION (Video Compositor)        │
│  FFmpeg 7-layer composition | NVENC encoding    │
├─────────────────────────────────────────────────┤
│  Layer 5: STREAMING (RTMP Manager)              │
│  FFmpeg RTMP | Auto-reconnect | Multi-platform  │
├─────────────────────────────────────────────────┤
│  Layer 6: INTERACTION (Chat Monitoring)         │
│  TikTok + Shopee (Observer) | Priority Queue    │
├─────────────────────────────────────────────────┤
│  Layer 7: COMMERCE (Product + Analytics)        │
│  ProductManager | ScriptEngine | AnalyticsEngine│
└─────────────────────────────────────────────────┘
```

## Cross-Cutting Concerns & Resilience

```
┌──────────────────────────────────────┐
│  CONFIG     │ YAML + .env + Pydantic │
│  DATABASE   │ SQLite (WAL mode)      │
│  OBSERVE    │ structlog, Sentry, Prometheus  │
│  RESILIENCE │ Circuit Breaker, Async Retry   │
│  RESOURCES  │ GPU Memory Manager (6-levels)  │
│  HEALTH     │ Centralized Manager    │
│  MOCK MODE  │ GPU-less development   │
│  VALIDATORS │ Asset validation       │
│  ANALYTICS  │ P50/P95 + ring buffer  │
└──────────────────────────────────────┘
```

## Key Design Decisions

| Decision        | Choice                                   | Rationale                     |
| --------------- | ---------------------------------------- | ----------------------------- |
| Package Manager | UV                                       | Fast, reproducible builds     |
| Rendering       | Hybrid (Pre-rendered + Real-time)        | GPU efficiency                |
| Architecture    | Pure Python (no ComfyUI)                 | Better debugging              |
| Development     | Distributed (Local → Remote GPU)         | Cost savings                  |
| Avatar Layout   | Smart Anchor (30%) + Product Focus (60%) | Viewer attention              |
| LLM Fast Path   | Groq (sub-100ms)                         | Ultra-fast chat responses     |
| LLM Backend     | **LiteLLM** (proven, 100+ providers)     | Replace all custom adapters   |
| Dashboard       | HTML/JS (zero-dep)                       | No build step needed          |
| Analytics       | Ring buffer (deque)                      | O(1) memory-bounded metrics   |
| Health          | Centralized HealthManager                | Timeout per check, concurrent |

## LiteLLM Brain — Provider Configuration

> **LiteLLM** (https://github.com/BerriAI/litellm) adalah universal LLM proxy yang menggantikan semua custom adapter.
> Satu `LiteLLMAdapter` class untuk semua provider — reliable, proven, no more "Sistem sedang sibuk".

### Provider Table

| Name | LiteLLM Model String | Endpoint | Env Var | Task Priority |
|------|---------------------|----------|---------|--------------|
| `gemini` | `gemini/gemini-2.0-flash` | Google API | `GEMINI_API_KEY` | Chat, Emotion |
| `claude` | `anthropic/claude-sonnet-4-5` | Anthropic API | `ANTHROPIC_API_KEY` | Script |
| `gpt4o` | `openai/gpt-4o-mini` | OpenAI API | `OPENAI_API_KEY` | Emotion, Safety |
| `groq` | `groq/llama-3.3-70b-versatile` | Groq API | `GROQ_API_KEY` | Chat (fastest) |
| `chutes` | `openai/MiniMaxAI/MiniMax-M2.5` | `https://llm.chutes.ai/v1` | `CHUTES_API_TOKEN` | Script, QA |
| `gemini_local_pro` | `openai/gemini-3.1-pro-high` | `http://127.0.0.1:8091/v1` | `LOCAL_GEMINI_API_KEY` | Script, Safety (FREE) |
| `gemini_local_flash` | `openai/gemini-3-flash` | `http://127.0.0.1:8091/v1` | `LOCAL_GEMINI_API_KEY` | Chat, Filler (FREE) |
| `local` | `openai/qwen2.5:7b` | `http://localhost:11434/v1` | `LOCAL_API` | Filler (FREE) |

### Routing Table (Task → Provider Chain)

| Task | Priority Chain |
|------|---------------|
| `CHAT_REPLY` | groq → gemini_local_flash → gemini → chutes → gpt4o → local |
| `SELLING_SCRIPT` | gemini_local_pro → chutes → claude → gpt4o → gemini |
| `HUMOR` | groq → gemini_local_flash → gemini → chutes → local |
| `PRODUCT_QA` | gemini_local_pro → chutes → gemini → groq → gpt4o |
| `EMOTION_DETECT` | groq → gemini_local_flash → gpt4o → chutes → gemini |
| `FILLER` | local → gemini_local_flash → groq → gemini |
| `SAFETY_CHECK` | gemini_local_pro → gpt4o → chutes → gemini |

### Key Files
- `src/brain/adapters/litellm_adapter.py` — Universal LiteLLM adapter
- `src/brain/router.py` — Routing table + fallback chain + budget tracking

## Startup Sequence

```
1. Config Loader (.env + config.yaml)
2. Structured Logging (structlog)
3. Database Init (SQLite WAL)
4. Mock Mode Check
5. Health Manager Registration
6. Commerce Components (ProductManager, AffiliateTracker)
7. Analytics Engine
8. Dashboard API (13 REST + 2 WS)
9. Static File Serving (/dashboard)
10. Diagnostic Endpoint (/diagnostic)
11. FastAPI App Ready
```

## API Endpoints

| Method | Path                          | Auth | Description              |
| ------ | ----------------------------- | ---- | ------------------------ |
| GET    | `/`                           | ✗    | Root info + links        |
| GET    | `/diagnostic/`                | ✗    | Full system diagnostic   |
| GET    | `/diagnostic/health`          | ✗    | Simple health check      |
| GET    | `/diagnostic/health/detailed` | ✗    | Per-component health     |
| GET    | `/api/status`                 | ✓    | System state             |
| GET    | `/api/metrics`                | ✓    | Latency P50/P95, revenue |
| GET    | `/api/products`               | ✓    | Product list             |
| POST   | `/api/products/{id}/switch`   | ✓    | Switch product           |
| GET    | `/api/chat/recent`            | ✓    | Recent chat events       |
| POST   | `/api/stream/start`           | ✓    | Start stream             |
| POST   | `/api/stream/stop`            | ✓    | Stop stream              |
| POST   | `/api/emergency-stop`         | ✓    | Emergency kill           |
| POST   | `/api/emergency-reset`        | ✓    | Recover from emergency   |
| GET    | `/api/health/summary`         | ✗    | Public health            |
| GET    | `/api/analytics/revenue`      | ✓    | Revenue report           |
| WS     | `/api/ws/dashboard`           | ✗    | Real-time metrics (1s)   |
| WS     | `/api/ws/chat`                | ✗    | Real-time chat           |
| GET    | `/dashboard`                  | ✗    | Interactive UI           |
| GET    | `/docs`                       | ✗    | Swagger API docs         |

## Directory Structure

```
videoliveai/
├── src/
│   ├── brain/              # Layer 1: Intelligence
│   │   ├── adapters/       # Gemini, Claude, GPT4o, Groq, Local
│   │   ├── router.py       # Task-based routing + fallback
│   │   ├── persona.py      # AI host personality
│   │   └── safety.py       # Content safety filter
│   ├── voice/              # Layer 2: Voice
│   │   └── engine.py       # FishSpeech + EdgeTTS + cache + router
│   ├── face/               # Layer 3: Face
│   │   └── pipeline.py     # MuseTalk + GFPGAN + smoother
│   ├── composition/        # Layer 4: Composition
│   │   └── compositor.py   # FFmpeg 7-layer filter graph
│   ├── stream/             # Layer 5: Streaming
│   │   └── rtmp.py         # RTMP + auto-reconnect
│   ├── chat/               # Layer 6: Interaction
│   │   └── monitor.py      # Platform Abstraction + connectors
│   ├── commerce/           # Layer 7: Commerce
│   │   ├── manager.py      # Products + scripts + affiliate
│   │   └── analytics.py    # Metrics engine (P50/P95)
│   ├── orchestrator/       # State Machine
│   │   └── state_machine.py
│   ├── config/             # Pydantic config loader
│   ├── utils/              # Logging, mock, validators, health
│   ├── data/               # SQLite database + schema
│   ├── dashboard/          # REST API + frontend
│   │   ├── api.py          # 13 REST + 2 WS endpoints
│   │   ├── diagnostic.py   # Health diagnostic
│   │   └── frontend/       # HTML/JS dashboard UI
│   └── main.py             # Entry point
├── tests/                  # 7 test files, ~66 tests
├── scripts/                # verify_pipeline.py
├── docs/                   # Architecture, workflow, changelogs
├── config.yaml             # System configuration
├── .env.example            # Environment template
└── pyproject.toml          # UV package manager
```
