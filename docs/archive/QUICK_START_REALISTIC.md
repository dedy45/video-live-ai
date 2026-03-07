# 🚀 Quick Start - REALISTIC Edition

**Reality Check**: Sistem ini BELUM production-ready. Dokumen ini untuk development & testing.

---

## ⚠️ BEFORE YOU START

### What Works NOW
- ✅ Config loading
- ✅ Database setup
- ✅ LLM routing (multi-provider)
- ✅ Voice synthesis (EdgeTTS)
- ✅ Mock mode (no GPU)
- ✅ Dashboard API

### What DOESN'T Work
- ❌ Face rendering (NotImplementedError)
- ❌ LiveTalking integration (skeleton only)
- ❌ RTMP streaming (not connected)
- ❌ End-to-end flow (incomplete)

### Timeline to Working System
- **Mock mode testing**: Available now
- **Basic integration**: 2 weeks
- **LiveTalking integration**: 4-6 weeks
- **Production ready**: 8 weeks

---

## 🎯 OPTION 1: Test Mock Mode (5 Minutes)

**What This Does**: Test architecture tanpa GPU, semua components di-mock

### Step 1: Install
```bash
cd videoliveai
uv pip install -e ".[dev]"
```

### Step 2: Configure
```bash
cp .env.example .env
# Edit .env:
# - Set MOCK_MODE=true
# - Add at least one LLM API key (optional)
```

### Step 3: Run
```bash
set MOCK_MODE=true
set LOG_LEVEL=DEBUG
uv run python -m src.main
```

### Step 4: Test
```bash
# Open browser: http://localhost:8000

# Test health
curl http://localhost:8000/diagnostic/health

# Test LLM stats
curl http://localhost:8000/api/llm/stats
```

### Expected Result
- ✅ Server starts
- ✅ Health check passes
- ✅ Dashboard accessible
- ⚠️ Face rendering returns mock frames
- ⚠️ No actual video generation

---

## 🎯 OPTION 2: Test Individual Components (30 Minutes)

**What This Does**: Test each layer secara isolated

### Test 1: Config Loading
```bash
cd videoliveai
uv run python -c "
from src.config import load_config
config = load_config()
print(f'✅ Config loaded: {config.app.name} v{config.app.version}')
"
```

### Test 2: Database
```bash
uv run python -c "
from src.data.database import init_database, check_database_health
init_database()
health = check_database_health()
print(f'✅ Database: {health}')
"
```

### Test 3: LLM Router
```bash
uv run python -c "
from src.brain.router import LLMRouter
router = LLMRouter()
print(f'✅ LLM Adapters: {list(router.adapters.keys())}')
"
```

### Test 4: Voice Engine
```bash
uv run python -c "
import asyncio
from src.voice.engine import VoiceRouter

async def test():
    voice = VoiceRouter()
    result = await voice.synthesize('Hello world')
    print(f'✅ Voice: {len(result.audio_data)} bytes, {result.duration_ms}ms')

asyncio.run(test())
"
```

### Test 5: Face Pipeline (Will Show Limitation)
```bash
set MOCK_MODE=true
uv run python -c "
import asyncio
from src.face.livetalking_adapter import LiveTalkingPipeline

async def test():
    pipeline = LiveTalkingPipeline()
    audio = b'fake audio'
    frames = []
    async for frame in pipeline.render(audio, 1000.0):
        frames.append(frame)
        if len(frames) >= 3:
            break
    print(f'✅ Face (mock): {len(frames)} frames')

asyncio.run(test())
"
```

---

## 🎯 OPTION 3: Run LiveTalking Standalone (1 Hour)

**What This Does**: Test LiveTalking secara terpisah dari videoliveai

### Prerequisites
- GPU dengan CUDA
- 10GB+ disk space
- Python 3.10+

### Step 1: Setup LiveTalking
```bash
cd videoliveai/external/livetalking

# Install dependencies
pip install -r requirements.txt

# Download models (manual - see LiveTalking README)
# - MuseTalk model
# - Face detection model
# - Audio processor model
```

### Step 2: Prepare Avatar
```bash
# Create avatar directory
mkdir -p data/avatars/test_avatar

# Add files:
# - full_imgs/ (extracted frames from reference video)
# - coords.pkl (face landmarks)
# - latents.pt (MuseTalk latents)
# - reference.wav (voice sample)
```

### Step 3: Run Server
```bash
python app.py \
  --model musetalk \
  --avatar_id test_avatar \
  --tts edgetts \
  --listenport 8010
```

### Step 4: Test
```bash
# Open browser: http://localhost:8010/dashboard.html

# Or test API:
curl -X POST http://localhost:8010/human \
  -H "Content-Type: application/json" \
  -d '{"sessionid": 0, "type": "echo", "text": "Hello world"}'
```

### Expected Result
- ✅ Server starts
- ✅ Dashboard accessible
- ✅ Can send text
- ✅ Video generates
- ⚠️ NOT integrated dengan videoliveai

---

## 🎯 OPTION 4: Development Setup (2 Hours)

**What This Does**: Setup untuk development & contribution

### Step 1: Clone & Install
```bash
git clone <your-repo-url> videoliveai
cd videoliveai

# Create virtual environment
uv venv --python 3.10

# Install with dev dependencies
uv pip install -e ".[dev,livetalking]"
```

### Step 2: Setup Pre-commit Hooks
```bash
pre-commit install
```

### Step 3: Run Tests
```bash
# This will fail because tests don't exist yet
pytest tests/ -v

# Create first test
mkdir -p tests/unit
cat > tests/unit/test_config.py << 'EOF'
from src.config import load_config

def test_config_loads():
    config = load_config()
    assert config.app.name == "AI Live Commerce"
EOF

# Run again
pytest tests/unit/test_config.py -v
```

### Step 4: Setup IDE
```bash
# VS Code settings
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true
}
EOF
```

---

## 🚨 TROUBLESHOOTING

### Issue: "Module not found"
```bash
# Solution: Install dependencies
uv pip install -e ".[dev]"

# Or specific package
uv pip install <package-name>
```

### Issue: "CUDA not available"
```bash
# Check CUDA
python -c "import torch; print(torch.cuda.is_available())"

# If False, use mock mode
set MOCK_MODE=true
```

### Issue: "Port already in use"
```bash
# Find process
netstat -ano | findstr :8000

# Kill process (Windows)
taskkill /PID <pid> /F

# Or use different port
set DASHBOARD_PORT=8001
```

### Issue: "Config file not found"
```bash
# Create default config
mkdir -p config
cat > config/config.yaml << 'EOF'
app:
  name: "AI Live Commerce"
  version: "0.3.1"
  env: "development"
EOF
```

### Issue: "Database locked"
```bash
# Remove lock
rm data/commerce.db-journal

# Or recreate database
rm data/commerce.db
uv run python -c "from src.data.database import init_database; init_database()"
```

---

## 📊 WHAT TO EXPECT

### Mock Mode Performance
- Startup: ~5 seconds
- LLM response: 1-3 seconds (depends on provider)
- TTS: 0.5-1 second (EdgeTTS)
- Face rendering: Instant (mock frames)
- Total latency: 2-5 seconds

### Production Mode (When Implemented)
- Startup: ~30 seconds (model loading)
- LLM response: 1-3 seconds
- TTS: 0.5-1 second
- Face rendering: 0.8-1.5 seconds (GPU)
- Total latency: 2.5-5.5 seconds

---

## 🎯 NEXT STEPS

### After Mock Mode Works
1. Read `CARA_TEST_SEKARANG.md` untuk detailed analysis
2. Read `ACTION_ITEMS_PRIORITIZED.md` untuk development plan
3. Start implementing missing pieces
4. Create tests as you go

### If You Want to Contribute
1. Pick an issue from `ACTION_ITEMS_PRIORITIZED.md`
2. Create feature branch
3. Implement + test
4. Submit PR
5. Celebrate! 🎉

---

## 💡 TIPS

1. **Start with mock mode** - Don't need GPU untuk development
2. **Test incrementally** - One component at a time
3. **Write tests** - Before implementing features
4. **Document as you go** - Future you will thank you
5. **Ask for help** - Don't struggle alone
6. **Be patient** - This is complex system, takes time

---

## 📚 DOCUMENTATION

- `CARA_TEST_SEKARANG.md` - Detailed technical analysis
- `INTEGRASI_LIVETALKING_SUMMARY.md` - Integration status & gaps
- `ACTION_ITEMS_PRIORITIZED.md` - 8-week development plan
- `COLAB_TESTING_STRATEGY.md` - GPU testing on Colab
- `README.md` - Project overview

---

## 🎉 CONCLUSION

**Reality**: Sistem ini masih dalam development. Mock mode works, production mode needs work.

**Timeline**: 
- Mock testing: Now
- Basic integration: 2 weeks
- Production ready: 8 weeks

**Recommendation**: Start dengan mock mode, understand architecture, then contribute to implementation.

**Remember**: Quality > Speed. Better to build it right than build it fast.

