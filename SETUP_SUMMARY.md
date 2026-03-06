# Setup Summary - VideoLiveAI

> Quick reference untuk semua setup scripts dan troubleshooting

## 🚀 Quick Start (Recommended)

```bash
# 1. Quick setup (2-5 min, no LiveTalking)
quick_setup.bat

# 2. Test installation
test_setup.bat

# 3. Run in mock mode
set MOCK_MODE=true
uv run python -m src.main
```

## 📋 All Setup Scripts

| Script | Time | Size | Purpose | When to Use |
|--------|------|------|---------|-------------|
| **quick_setup.bat** | 2-5 min | ~200MB | Core only (NO LiveTalking) | ✅ First time, testing |
| **setup_livetalking_uv.bat** | 10-20 min | ~2GB | Full setup with LiveTalking | Production ready |
| **setup_livetalking_verbose.bat** | 10-20 min | ~2GB | Debug mode with progress | Troubleshooting |
| **test_setup.bat** | 1 min | 0 | Verify installation | After setup |
| **diagnose_setup.bat** | 1 min | 0 | Full diagnostic | When setup fails |

## 🔧 Troubleshooting Tools

### If Setup Hangs

**Problem:** Script hangs at "Installing dependencies"

**Solution:**
```bash
# Option 1: Use verbose mode (see progress)
setup_livetalking_verbose.bat

# Option 2: Install step-by-step
quick_setup.bat  # Core first
uv pip install torch torchvision torchaudio  # Then PyTorch
uv pip install opencv-python scikit-image scipy  # Then others

# Option 3: Increase timeout
set UV_HTTP_TIMEOUT=600
uv pip install -e ".[livetalking]"
```

### If Setup Fails

```bash
# Step 1: Diagnose
diagnose_setup.bat

# Step 2: Check what's wrong
# - Network timeout?
# - Disk space full?
# - Antivirus blocking?
# - Conda interference?

# Step 3: See detailed solutions
# Open: TROUBLESHOOTING_SETUP.md
```

### If Installation Corrupt

```bash
# Clean install
rmdir /s /q .venv
uv cache clean
uv venv
uv pip install -e . --no-cache
```

## 📊 Setup Flow Diagram

```
START
  ↓
quick_setup.bat (2-5 min)
  ↓
test_setup.bat (verify)
  ↓
Run in MOCK_MODE (test)
  ↓
Need LiveTalking?
  ├─ No  → Done! ✓
  └─ Yes → setup_livetalking_uv.bat (10-20 min)
            ↓
          test_setup.bat (verify)
            ↓
          Download models
            ↓
          Done! ✓
```

## 🎯 What Each Script Does

### quick_setup.bat
```
1. Delete old .venv
2. Clean UV cache
3. Create fresh .venv
4. Install CORE dependencies (~200MB)
   - FastAPI, Pydantic, LiteLLM
   - LLM providers (Gemini, Claude, GPT-4o, Groq)
   - Basic utilities
5. Create folder structure
6. Verify installation
```

### setup_livetalking_uv.bat
```
1. Check UV installed
2. Create .venv (if not exists)
3. Install CORE dependencies first
4. Install LIVETALKING dependencies (~2GB)
   - PyTorch (~1.5GB)
   - OpenCV (~100MB)
   - aiortc, scipy, librosa, etc
5. Run setup script
6. Verify setup
```

### test_setup.bat
```
1. Check UV installed
2. Check .venv exists
3. Check Python path (should be .venv\Scripts\python.exe)
4. Check core packages (fastapi, pydantic, litellm)
5. Check LiveTalking packages (torch, opencv) - optional
6. Check project structure (src\main.py, config.yaml, .env)
7. Test imports (config, logging)
```

### diagnose_setup.bat
```
1. System info (OS, processor, user, directory)
2. UV info (version, location)
3. Python info (version, location)
4. Virtual environment status
5. UV lock file check
6. Disk space check
7. Network test (ping pypi.org)
8. UV cache info
9. Project files check
10. Git submodules check
11. Common issues check (conda, multiple Python)
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **SETUP_GUIDE.md** | Complete setup guide with 3 options |
| **TROUBLESHOOTING_SETUP.md** | 10+ common issues and solutions |
| **UV_VS_CONDA_GUIDE.md** | UV vs Conda explained |
| **LIVETALKING_QUICKSTART.md** | LiveTalking integration guide |
| **SETUP_SUMMARY.md** | This file - quick reference |

## ⚡ Quick Commands

```bash
# Check UV version
uv --version

# Check Python path
uv run python -c "import sys; print(sys.executable)"

# Check installed packages
uv pip list

# Check core imports
uv run python -c "import fastapi, pydantic, litellm; print('OK')"

# Check LiveTalking imports
uv run python -c "import torch, cv2; print('OK')"

# Run server in mock mode
set MOCK_MODE=true
uv run python -m src.main

# Run tests
uv run pytest tests/ -v
```

## 🐛 Common Errors

| Error | Solution |
|-------|----------|
| Setup hangs | Use `setup_livetalking_verbose.bat` |
| "Failed to read websockets" | Delete `.venv`, clean cache, reinstall |
| "uv: command not found" | `pip install uv` |
| Using miniconda Python | Create `.venv` first: `uv venv` |
| "Module not found" | Install deps: `uv pip install -e .` |
| Network timeout | Increase timeout: `set UV_HTTP_TIMEOUT=600` |
| Disk space full | Free up ~5GB space |
| Antivirus blocking | Temporarily disable or add exclusions |

## ✅ Verification Checklist

After setup, verify:

- [ ] UV installed: `uv --version`
- [ ] .venv exists: `dir .venv`
- [ ] Python path correct: `uv run python -c "import sys; print(sys.executable)"`
- [ ] Core packages: `uv run python -c "import fastapi, pydantic; print('OK')"`
- [ ] Config loads: `set MOCK_MODE=true && uv run python -c "from src.config import get_config; print('OK')"`
- [ ] Server starts: `set MOCK_MODE=true && uv run python -m src.main`
- [ ] Tests pass: `uv run pytest tests/ -v`

## 🎓 Learning Path

1. **Day 1:** Run `quick_setup.bat` → Test with `MOCK_MODE=true`
2. **Day 2:** Explore code, run tests, configure `.env`
3. **Day 3:** Run `setup_livetalking_uv.bat` → Download models
4. **Day 4:** Prepare reference video/audio → Train avatar
5. **Day 5:** Go live! 🚀

## 🆘 Getting Help

If stuck:

1. Run `diagnose_setup.bat` and check output
2. Read `TROUBLESHOOTING_SETUP.md` for your specific error
3. Check `data/logs/app.log` for errors
4. Create GitHub issue with diagnostic output

## 🔗 Links

- **Repository:** https://github.com/dedy45/video-live-ai.git
- **Issues:** https://github.com/dedy45/video-live-ai/issues
- **LiveTalking:** https://github.com/lipku/LiveTalking

---

**Start with `quick_setup.bat` for fastest setup!**

**If setup hangs, use `setup_livetalking_verbose.bat` to see progress.**

**For any issues, run `diagnose_setup.bat` first!**
