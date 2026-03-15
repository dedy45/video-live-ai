# VideoLiveAI - AI Live Commerce Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/package%20manager-UV-orange.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered live commerce platform for automated livestreaming on TikTok and Shopee, built around a Python control plane plus a vendor avatar sidecar.

## 🎯 Features

- **Multi-LLM Brain**: Gemini, Claude, GPT-4o, Groq with intelligent routing
- **Voice Layer**: Fish-Speech local sidecar direct-test path verified locally, Edge-TTS emergency fallback available, with GPT-SoVITS/CosyVoice adapter paths for external TTS servers
- **Avatar Runtime**: LiveTalking sidecar with MuseTalk as the only acceptance path, Wav2Lip as secondary fallback only, and ER-NeRF/GFPGAN kept as target-only tracks
- **Real-time Streaming**: RTMP to TikTok/Shopee, WebRTC for browser
- **Live Session Q&A**: dashboard chat ingest, auto-pause, answer draft, and resume flow for operator-assisted live sessions
- **Commerce Management**: Product catalog, order tracking, analytics
- **State Machine Orchestrator**: SELLING → REACTING → ENGAGING → IDLE

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [UV package manager](https://github.com/astral-sh/uv)
- NVIDIA GPU with 8GB+ VRAM (for production)
- FFmpeg

### Installation

```bash
# Clone repository
git clone https://github.com/dedy45/video-live-ai.git
cd video-live-ai

# Install dependencies with UV
uv sync --extra dev

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Production-first bootstrap from zero
uv run python scripts/manage.py setup all
```

### Test with Mock Mode (No GPU Required)

```bash
# Windows
uv run python scripts/manage.py serve --mock

# Linux/Mac
uv run python scripts/manage.py serve --mock
```

### Dashboard

| URL | Purpose | Who |
|-----|---------|-----|
| `http://localhost:8001/dashboard` | **Operator dashboard** (primary UI in local lab) | Operators |
| `http://SERVER_IP_OR_DOMAIN/dashboard` | **Server-hosted ops controller** for production/browser access | Operators |
| `http://localhost:8001/docs` | API documentation | Developers |
| `http://localhost:8001/diagnostic/` | System diagnostics | Operators/Devs |
| `http://localhost:8010/*.html` | LiveTalking debug pages | Developers only |

> **Rule:** `/dashboard` stays the only operator UI. In production it is hosted on the server behind a reverse proxy, and browser disconnects must not stop the live process. Vendor pages at port 8010 stay debug tools only.

Official operator workflow surfaces:

- `Setup & Validasi`
- `Produk & Penawaran`
- `Avatar & Suara`
- `Streaming & Platform`
- `Konsol Live`
- `Monitor & Insiden`

Standalone production entrypoints remain supported for focused debugging and operator drills:

- `/dashboard/setup.html`
- `/dashboard/products.html`
- `/dashboard/performer.html`
- `/dashboard/stream.html`
- `/dashboard/monitor.html`

`Validation` and `Diagnostics` are no longer standalone operator pages. They now live inside the `Setup & Validasi` and `Monitor & Insiden` surfaces.

### Operator Model

The dashboard architecture is now an **operational evolution**, not a rewrite:

- FastAPI remains the control plane
- Fish-Speech remains the voice sidecar
- LiveTalking / MuseTalk remains the face sidecar
- `/dashboard` remains the single operator UI
- what changes is the runtime model: from a localhost-oriented operator shell to a **server-hosted ops controller** reachable via browser, IP, or domain
- server execution continues even if the operator laptop disconnects or dies

### Local Operator Commands

Canonical cross-platform operator CLI:

```bash
uv run python scripts/manage.py setup all
uv run python scripts/manage.py setup fish-speech
uv run python scripts/manage.py start fish-speech
uv run python scripts/manage.py start livetalking --mode musetalk
uv run python scripts/manage.py status all
uv run python scripts/manage.py status fish-speech
uv run python scripts/manage.py health
uv run python scripts/manage.py validate tests
uv run python scripts/manage.py validate livetalking
uv run python scripts/manage.py validate fish-speech
uv run python scripts/manage.py serve --mock
uv run python scripts/manage.py serve --real
uv run python scripts/manage.py open performer
uv run python scripts/manage.py open monitor
```

Windows convenience wrapper:

```bat
scripts\menu.bat
```

`menu.bat` is only a Windows launcher. The real command path stays `uv run python scripts/manage.py ...`, so the same operational flow works on Ubuntu without batch files.

For direct ad hoc LiveTalking commands outside `manage.py`, use `uv run --extra livetalking ...` so UV keeps the vendor runtime packages loaded.

Canonical sidecar paths:

- `external/livetalking/`
- `external/fish-speech/upstream/`
- `external/fish-speech/checkpoints/`
- `external/fish-speech/runtime/`
- `external/fish-speech/runtime/.venv/` managed by `uv` for the voice sidecar only

### Current Milestone Status

- Latest targeted dashboard verification (`2026-03-13`):
  - `uv run pytest tests/test_brain.py tests/test_dashboard.py tests/test_control_plane.py -q -p no:cacheprovider` -> `101 passed`
  - `cd src/dashboard/frontend && npm test -- --run src/tests/AIBrainPage.test.ts src/tests/live-console-panel.test.ts` -> `8 passed`
  - `cd src/dashboard/frontend && npm run build` -> PASS
  - Browser smoke on `http://127.0.0.1:8001/dashboard/?v=20260313b#/` in `MOCK_MODE=true` -> `Director Runtime` shows `SELLING` before simulated chat, `PAUSED` after `Kirim Chat Simulasi`, and `POST /api/live-session/stop` returns `/api/pipeline/state` to `IDLE`
- Face milestone: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK` -> `LOCAL VERIFIED`
- Audio milestone: `LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH` -> `LOCAL VERIFIED` for direct local test
- Frontend verification: `cd src/dashboard/frontend && npm run test` -> `67 passed` across `19` test files
- Frontend build: `cd src/dashboard/frontend && npm run build` -> PASS
- Fresh verification: `uv run pytest tests -q -p no:cacheprovider` -> `255 passed, 1 skipped`
- Pipeline verification: `uv run python scripts/verify_pipeline.py` -> `11/11 layers passed`
- MuseTalk assets: `uv run --extra livetalking python scripts/setup_musetalk_assets.py --sync-only` -> `Models ready: True`, `Avatar ready: True`
- Official face operator slice: `uv run python scripts/manage.py serve --real` + engine start/validation resolve to `musetalk / musetalk_avatar1` with `fallback_active=false`
- Audio readiness gate: `uv run python scripts/check_real_mode_readiness.py --json` -> `READY FOR REAL MODE`
- Audio prerequisite validation: `uv run python scripts/manage.py validate fish-speech` -> PASS
- Fish-Speech bootstrap: `uv run python scripts/manage.py setup fish-speech` -> PASS; pinned checkout `v1.5.1`, canonical checkpoints, and dedicated sidecar UV env are now hydrated locally
- Audio smoke validation: `MOCK_MODE=false uv run python -c "..."` -> PASS with `voice_runtime_mode=fish_speech_local`, `resolved_engine=fish_speech`, `fallback_active=false`
- Verified local audio smoke latency on this GTX 1650 setup is now around `20.9s` after the dedicated CUDA sidecar env fix; still functionally verified, but not yet live-latency-ready
- Next-phase work: latency reduction / chunking discipline, humanization minimum, then RTMP dry-run and short real live test

## 📊 Architecture

```
┌─────────────────────────────────────┐
│  Brain: Multi-LLM (Gemini/Claude)   │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Voice: FishSpeech / Edge-TTS       │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Face: LiveTalking Sidecar          │
│  ├── MuseTalk (acceptance path)     │
│  ├── Wav2Lip (secondary fallback)   │
│  └── ER-NeRF / GFPGAN (target only) │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Stream: RTMP → TikTok/Shopee       │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Chat: Real-time monitoring         │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Commerce: Product & Analytics      │
└─────────────────────────────────────┘
```

## 🎨 Project Structure

```
videoliveai/
├── src/
│   ├── brain/          # LLM orchestration
│   ├── voice/          # TTS engines
│   ├── face/           # Avatar rendering
│   ├── stream/         # RTMP streaming
│   ├── chat/           # Live chat monitoring
│   ├── commerce/       # Product management
│   └── orchestrator/   # State machine
├── config/             # Configuration files
├── scripts/            # Setup & utility scripts
├── tests/              # Test suite
├── models/             # Model weights (download separately)
├── assets/             # Avatar, voice, products
└── data/               # Database & logs
```

## 🔧 Configuration

### Environment Variables

Key configurations in `.env`:

```bash
# LLM API Keys
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key

# Streaming
TIKTOK_RTMP_URL=rtmp://push.tiktokcdn.com/live/
TIKTOK_STREAM_KEY=your_key
SHOPEE_RTMP_URL=your_url
SHOPEE_STREAM_KEY=your_key

# LiveTalking
LIVETALKING_ENABLED=true
LIVETALKING_REFERENCE_VIDEO=assets/avatar/reference.mp4
LIVETALKING_REFERENCE_AUDIO=assets/avatar/reference.wav

# System
MOCK_MODE=false
GPU_DEVICE=cuda:0
GPU_VRAM_BUDGET_MB=20000
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Frontend operator surfaces
cd src/dashboard/frontend && npm run test
cd src/dashboard/frontend && npm run build

# Run specific test
uv run pytest tests/test_livetalking_integration.py -v

# Skip GPU tests
uv run pytest tests/ -v -m "not integration"

# Vendor runtime smoke
uv run python scripts/manage.py validate livetalking

# Quick validation (Windows)
uv run python scripts/manage.py validate fish-speech
```

## 📚 Documentation

- [Docs Index](docs/README.md)
- [Architecture](docs/architecture.md)
- [Task Status](docs/task_status.md)
- [LiveTalking Quick Start](docs/guides/LIVETALKING_QUICKSTART.md)
- [Runtime Model Comparison](docs/guides/MODEL_COMPARISON.md)

## 🎯 LiveTalking Integration

This project uses **LiveTalking** as a vendor sidecar for avatar rendering and realtime output.

Current vendor copy is best treated as:

- **MuseTalk** for the primary lip-sync path
- **Wav2Lip** as a secondary fallback path that does not count as milestone completion
- **Ultralight** as a low-resource option
- **WebRTC / rtcpush / virtualcam** for vendor-side output

`ER-NeRF` and `GFPGAN` still appear in project target docs, but should not be assumed active in the current vendor runtime.

See [docs/guides/LIVETALKING_QUICKSTART.md](docs/guides/LIVETALKING_QUICKSTART.md) for the current integration boundary.

### Dedicated LiveTalking Runtime

For local browser preview, do **not** rely on the main app `.venv` for the vendor sidecar.

Use a dedicated sidecar interpreter and point the manager at it:

```bash
LIVETALKING_PYTHON_EXE=.venv-livetalking/Scripts/python.exe
LIVETALKING_MODEL=wav2lip
LIVETALKING_AVATAR_ID=wav2lip256_avatar1
LIVETALKING_STARTUP_TIMEOUT_SEC=60
```

Verified local preview pages:

- `http://127.0.0.1:8010/webrtcapi.html`
- `http://127.0.0.1:8010/rtcpushapi.html`

`rtcpushapi.html` now falls back to direct WebRTC preview when no local relay exists on `:1985`, which makes it usable for Windows + TikTok LIVE Studio capture without SRS.

For the operator-facing browser path, `http://127.0.0.1:8001/dashboard/performer.html` now exposes a richer Voice Lab control plane:

- `Generate Audio`: choose `Indonesia` or `English`, select a quick clone or studio voice, tune `style / stability / similarity`, then choose the `Tujuan output`:
  - `Simpan Audio Lokal` keeps the synth result in the local artifact store.
  - `Kirim ke Avatar Live` sends the same synth result to the active avatar session while still storing the local `.wav`.
- `Manajer File Lokal`: the same `Suara` workspace now shows storage summary, artifact folder path, newest result, local playback, direct download, and delete actions without switching to another internal tab.
- `Quick Clone`: manage many fast reference clones with clear operator guidance about clean audio, transcript quality, and bilingual readiness.
- `Studio Voice`: create a single bilingual production voice profile per host character.
- `Training Jobs`: queue studio-voice training jobs directly from the dashboard; the backend blocks them automatically while a live session is active.
- The seeded default clone is now normalized as bilingual `id/en`, so the dashboard language selector and backend profile metadata stay aligned on fresh and legacy local databases.

The browser-verified attach flow still follows the same rule:

- `Kirim ke Avatar Live`: start `webrtcapi.html` from the `Preview` tab, let the dashboard sync the vendor `sessionid`, then generate and attach audio from the unified `Suara` workspace.

Current local attach verification is on the `wav2lip` preview path. Treat `MuseTalk` as a separate heavier validation track, not as implied proof that the day-1 attach lab is already covered.

## 🔥 Performance

### Mock Mode (Development)
- Latency: ~100ms
- No GPU required
- Use for testing & development

### Production Mode (RTX 3060+)
- Latency: 2-3 seconds end-to-end
- FPS: 30-60fps
- Resolution: 512x512 (scalable to 1024x1024)
- Quality: Hyper-realistic (Tier A)

## 🛠️ Tech Stack

- **Package Manager**: UV (not conda!)
- **Backend**: Python 3.10+, FastAPI, asyncio
- **LLM**: LiteLLM (multi-provider)
- **TTS**: FishSpeech / Edge-TTS active, GPT-SoVITS / CosyVoice via external adapters
- **Avatar**: LiveTalking sidecar (MuseTalk acceptance path, Wav2Lip/Ultralight fallback-capable, ER-NeRF/GFPGAN target-only)
- **Streaming**: FFmpeg, RTMP
- **Database**: SQLite (aiosqlite)
- **Monitoring**: Prometheus, Structlog
- **Testing**: Pytest, Hypothesis

## 📦 Dependencies Management

This project uses **UV** (not conda):

```bash
# Base dev env
uv sync --extra dev

# Managed LiveTalking env
uv sync --extra dev --extra livetalking

# Direct ad hoc command with vendor extra
uv run --extra livetalking python scripts/smoke_livetalking.py

# Add new dependency
uv pip install package-name

# Update dependencies
uv pip install --upgrade package-name

# Export requirements
uv pip freeze > requirements.txt
```

## 🚨 Troubleshooting

### GPU Out of Memory
```bash
# Reduce resolution
LIVETALKING_RESOLUTION=256,256

# Or use mock mode
MOCK_MODE=true
```

### LiveTalking Not Found
```bash
git submodule update --init --recursive
```

### Tests Failing
```bash
# Check logs
cat data/logs/app.log

# Run diagnostic
curl http://localhost:8001/diagnostic/health
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LiveTalking](https://github.com/lipku/LiveTalking) - Real-time avatar rendering
- [MuseTalk](https://github.com/TMElyralab/MuseTalk) - Lip-sync technology
- [ER-NeRF](https://github.com/Fictionarry/ER-NeRF) - 3D avatar rendering
- [GFPGAN](https://github.com/TencentARC/GFPGAN) - Face enhancement
- [fishspeech](https://github.com/fishaudio/fish-speech) - Voice cloning

## 📞 Support

- Issues: [GitHub Issues](https://github.com/dedy45/video-live-ai/issues)
- Documentation: [Wiki](https://github.com/dedy45/video-live-ai/wiki)

## 🗺️ Roadmap

- [ ] Multi-language support (ID, EN, CN)
- [ ] Facebook Live integration
- [ ] YouTube Live integration
- [ ] Advanced analytics dashboard
- [ ] A/B testing for sales scripts
- [ ] Voice emotion fine-tuning
- [ ] Custom avatar training pipeline
- [ ] Mobile app for monitoring

---

**Made with ❤️ for AI-powered live commerce**
