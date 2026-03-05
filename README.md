# VideoLiveAI - AI Live Commerce Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![UV](https://img.shields.io/badge/package%20manager-UV-orange.svg)](https://github.com/astral-sh/uv)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

AI-powered live commerce platform for automated livestreaming with hyper-realistic AI avatars on TikTok and Shopee.

## 🎯 Features

- **Multi-LLM Brain**: Gemini, Claude, GPT-4o, Groq with intelligent routing
- **Voice Cloning**: CosyVoice 2 & Edge-TTS for natural speech
- **Hyper-Realistic Avatar**: LiveTalking integration (MuseTalk 1.5 + ER-NeRF + GFPGAN)
- **Real-time Streaming**: RTMP to TikTok/Shopee, WebRTC for browser
- **Live Chat Integration**: Real-time comment monitoring and response
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
uv pip install -e ".[livetalking]"

# Copy environment file
cp .env.example .env
# Edit .env with your API keys
```

### Test with Mock Mode (No GPU Required)

```bash
# Windows
set MOCK_MODE=true
uv run python -m src.main

# Linux/Mac
MOCK_MODE=true uv run python -m src.main
```

### Production Mode

```bash
# Setup LiveTalking integration
python scripts/setup_livetalking.py

# Run production
uv run python -m src.main
```

## 📊 Architecture

```
┌─────────────────────────────────────┐
│  Brain: Multi-LLM (Gemini/Claude)   │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Voice: CosyVoice 2 / Edge-TTS      │
└──────────────┬──────────────────────┘
               │
┌──────────────┴──────────────────────┐
│  Face: LiveTalking (60fps)          │
│  ├── MuseTalk 1.5 (lip-sync)        │
│  ├── ER-NeRF (3D avatar)            │
│  └── GFPGAN (enhancement)           │
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

# Run specific test
uv run pytest tests/test_livetalking_integration.py -v

# Skip GPU tests
uv run pytest tests/ -v -m "not integration"

# Quick test with batch file (Windows)
test_livetalking.bat
```

## 📚 Documentation

- [LiveTalking Quick Start](LIVETALKING_QUICKSTART.md)
- [Integration Plan](docs/02-LIVE-STREAMING-AI/tech-stack/INTEGRATION_PLAN.md)
- [Final Stack Decision](docs/02-LIVE-STREAMING-AI/tech-stack/FINAL_STACK_DECISION.md)
- [Project Summary](PROJECT_SUMMARY.md)
- [Agents Documentation](AGENTS.md)

## 🎯 LiveTalking Integration

This project uses **LiveTalking** for hyper-realistic avatar rendering:

- **Real-time 60fps** rendering
- **95%+ realism** - viewers can't distinguish from real humans
- **RTMP/WebRTC native** streaming
- **Production-ready** for 24/7 livestreaming

See [LIVETALKING_QUICKSTART.md](LIVETALKING_QUICKSTART.md) for setup instructions.

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
- **TTS**: CosyVoice 2, Edge-TTS
- **Avatar**: LiveTalking (MuseTalk 1.5, ER-NeRF, GFPGAN)
- **Streaming**: FFmpeg, RTMP
- **Database**: SQLite (aiosqlite)
- **Monitoring**: Prometheus, Structlog
- **Testing**: Pytest, Hypothesis

## 📦 Dependencies Management

This project uses **UV** (not conda):

```bash
# Install dependencies
uv pip install -e ".[livetalking]"

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
curl http://localhost:8000/diagnostic/health
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
- [CosyVoice](https://github.com/FunAudioLLM/CosyVoice) - Voice cloning

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
