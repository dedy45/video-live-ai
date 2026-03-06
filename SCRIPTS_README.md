# Setup Scripts Guide

> Complete guide to all batch files in videoliveai/

## 📁 Script Categories

### 🚀 Setup Scripts (Start Here!)

| Script | Purpose | Time | Use When |
|--------|---------|------|----------|
| `quick_setup.bat` | Fast setup without LiveTalking | 2-5 min | ✅ **First time setup** |
| `setup_livetalking_uv.bat` | Full setup with LiveTalking | 10-20 min | Need production avatar |
| `setup_livetalking_verbose.bat` | Debug mode with progress | 10-20 min | Troubleshooting install |

### 🔍 Diagnostic Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `test_setup.bat` | Verify installation | Pass/Fail for each component |
| `diagnose_setup.bat` | Full system diagnostic | Comprehensive system info |

### 🛠️ Utility Scripts (Legacy/Deprecated)

| Script | Status | Replacement |
|--------|--------|-------------|
| `clean_and_setup_uv.bat` | ⚠️ Legacy | Use `quick_setup.bat` |
| `restart_dashboard.bat` | ⚠️ Legacy | Use `uv run python -m src.main` |

## 🎯 Recommended Workflow

### For New Users:

```bash
# Step 1: Quick setup (core only)
quick_setup.bat

# Step 2: Verify installation
test_setup.bat

# Step 3: Test in mock mode
set MOCK_MODE=true
uv run python -m src.main

# Step 4: Add LiveTalking when ready
setup_livetalking_uv.bat
```

### If Setup Fails:

```bash
# Step 1: Diagnose
diagnose_setup.bat

# Step 2: Read error messages carefully

# Step 3: Check troubleshooting guide
# Open: TROUBLESHOOTING_SETUP.md

# Step 4: Try verbose mode
setup_livetalking_verbose.bat
```

## 📖 Script Details

### quick_setup.bat

**What it does:**
1. Deletes old `.venv` (clean slate)
2. Cleans UV cache
3. Creates fresh `.venv`
4. Installs CORE dependencies only (~200MB)
5. Creates folder structure
6. Verifies installation

**Installs:**
- FastAPI, Pydantic, LiteLLM
- LLM providers (Gemini, Claude, GPT-4o, Groq)
- Basic utilities (websockets, edge-tts, etc)

**Does NOT install:**
- PyTorch (~1.5GB)
- OpenCV (~100MB)
- LiveTalking dependencies

**Use when:**
- First time setup
- Want to test project quickly
- Don't need LiveTalking yet
- Limited bandwidth/time

---

### setup_livetalking_uv.bat

**What it does:**
1. Checks UV installed
2. Creates `.venv` (if not exists)
3. Installs CORE dependencies first
4. Installs LIVETALKING dependencies (~2GB)
5. Runs setup script
6. Verifies setup

**Installs:**
- Everything from `quick_setup.bat`
- PyTorch (~1.5GB)
- TorchVision, TorchAudio
- OpenCV (~100MB)
- aiortc, av (WebRTC)
- scipy, librosa, soundfile, resampy
- imageio, imageio-ffmpeg

**Use when:**
- Need LiveTalking for production
- Have good internet connection
- Have 8GB+ VRAM GPU
- Ready to download models

---

### setup_livetalking_verbose.bat

**What it does:**
- Same as `setup_livetalking_uv.bat`
- But shows ALL output (verbose mode)
- Asks for confirmation before big downloads
- Shows progress for each package

**Use when:**
- Setup hangs and you want to see what's happening
- Troubleshooting installation issues
- Want to see download progress
- Debugging network problems

---

### test_setup.bat

**What it does:**
1. Checks UV installed
2. Checks `.venv` exists
3. Verifies Python path (should be `.venv\Scripts\python.exe`)
4. Tests core package imports (fastapi, pydantic, litellm)
5. Tests LiveTalking package imports (torch, opencv) - optional
6. Checks project structure (src\main.py, config.yaml, .env)
7. Tests module imports (config, logging)

**Use when:**
- After running setup
- Before running server
- To verify installation is correct
- To check what's installed

---

### diagnose_setup.bat

**What it does:**
1. Shows system info (OS, processor, user, directory)
2. Shows UV info (version, location)
3. Shows Python info (version, location)
4. Checks virtual environment status
5. Checks UV lock file
6. Checks disk space
7. Tests network (ping pypi.org)
8. Shows UV cache info
9. Checks project files
10. Checks git submodules
11. Checks for common issues (conda, multiple Python)

**Use when:**
- Setup fails or hangs
- Need to troubleshoot
- Before asking for help
- To gather system info

## 🔧 Environment Variables

Useful for troubleshooting:

```bash
# Increase timeout (default: 30s)
set UV_HTTP_TIMEOUT=600

# Change cache location
set UV_CACHE_DIR=D:\uv_cache

# Use mirror (China users)
set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Verbose output
set UV_VERBOSE=1

# No cache
set UV_NO_CACHE=1
```

## 📚 Related Documentation

- **SETUP_GUIDE.md** - Complete setup guide with 3 options
- **SETUP_SUMMARY.md** - Quick reference for all scripts
- **TROUBLESHOOTING_SETUP.md** - 10+ common issues and solutions
- **UV_VS_CONDA_GUIDE.md** - UV vs Conda explained
- **LIVETALKING_QUICKSTART.md** - LiveTalking integration guide

## 🆘 Common Issues

### Setup hangs at "Installing dependencies"

**Solution:** Use `setup_livetalking_verbose.bat` to see progress

### "Failed to read websockets"

**Solution:** Delete `.venv`, clean cache, reinstall

### "uv: command not found"

**Solution:** `pip install uv`

### Using miniconda Python

**Solution:** Create `.venv` first: `uv venv`

### Network timeout

**Solution:** `set UV_HTTP_TIMEOUT=600`

## ✅ Quick Verification

After setup, run these commands:

```bash
# 1. Check UV
uv --version

# 2. Check Python path
uv run python -c "import sys; print(sys.executable)"
# Should show: videoliveai\.venv\Scripts\python.exe

# 3. Check core imports
uv run python -c "import fastapi, pydantic, litellm; print('OK')"

# 4. Check LiveTalking imports (if installed)
uv run python -c "import torch, cv2; print('OK')"

# 5. Run test script
test_setup.bat
```

## 🎓 Learning Path

1. **Day 1:** `quick_setup.bat` → `test_setup.bat` → Run in MOCK_MODE
2. **Day 2:** Explore code, run tests, configure `.env`
3. **Day 3:** `setup_livetalking_uv.bat` → Download models
4. **Day 4:** Prepare reference materials → Train avatar
5. **Day 5:** Go live! 🚀

---

**Start with `quick_setup.bat` for fastest setup!**

**Use `test_setup.bat` to verify installation.**

**Run `diagnose_setup.bat` if you encounter issues.**
