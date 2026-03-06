# Setup Guide - VideoLiveAI

## 🎯 Setup Options

Ada 3 cara setup, pilih sesuai kebutuhan:

### Option 1: Quick Setup (RECOMMENDED untuk mulai)

Setup basic project TANPA LiveTalking dulu.

```bash
cd videoliveai
quick_setup.bat
```

**Installs**:
- ✅ Core dependencies (FastAPI, Pydantic)
- ✅ LLM providers (Gemini, Claude, GPT-4o, Groq)
- ✅ Basic utilities
- ❌ LiveTalking dependencies (torch, opencv) - SKIP

**Use case**: Test project dulu, tambah LiveTalking nanti

### Option 2: Full Setup dengan LiveTalking

Setup lengkap termasuk LiveTalking.

```bash
cd videoliveai
setup_livetalking_uv.bat
```

**Installs**:
- ✅ Core dependencies
- ✅ LLM providers
- ✅ LiveTalking dependencies (torch, opencv, aiortc)
- ✅ Clone LiveTalking submodule

**Use case**: Langsung pakai LiveTalking untuk avatar

### Option 3: Fix Corrupt Environment

Jika ada error atau environment corrupt.

```bash
cd videoliveai
simple_setup_uv.bat
```

**Does**:
- ✅ Delete corrupt .venv
- ✅ Clean UV cache
- ✅ Fresh install dengan --no-cache

**Use case**: Fix websockets error atau corrupt packages

## 📋 Setup Flow Diagram

```
Start
  ↓
Want LiveTalking now?
  ├─ No  → quick_setup.bat (fast, basic)
  │         ↓
  │       Test project
  │         ↓
  │       Add LiveTalking later? → setup_livetalking_uv.bat
  │
  └─ Yes → setup_livetalking_uv.bat (full)
            ↓
          Download models
            ↓
          Prepare references
            ↓
          Go live!
```

## 🚀 Quick Start (Recommended Path)

### Step 1: Basic Setup

```bash
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
quick_setup.bat
```

### Step 2: Test Basic Functionality

```bash
set MOCK_MODE=true
uv run python -m src.main
```

### Step 3: Add LiveTalking (Optional)

```bash
setup_livetalking_uv.bat
```

## 🔧 What Each Script Does

### quick_setup.bat

```
1. Delete old .venv
2. Clean UV cache
3. Create fresh .venv
4. Install CORE dependencies only
5. Create folder structure
6. Verify installation
```

**Time**: ~2-5 minutes
**Size**: ~200MB

### setup_livetalking_uv.bat

```
1. Check UV installed
2. Create .venv (if not exists)
3. Install dependencies (including LiveTalking)
4. Run setup script
5. Verify setup
```

**Time**: ~10-20 minutes (depends on network)
**Size**: ~2GB (with torch, opencv)

### simple_setup_uv.bat

```
1. Delete corrupt .venv
2. Clean UV cache
3. Create fresh .venv
4. Install with --no-cache
5. Verify
```

**Time**: ~5-10 minutes
**Size**: ~200MB

## ❓ Which Script to Use?

### Use quick_setup.bat if:
- ✅ First time setup
- ✅ Want to test project quickly
- ✅ Don't need LiveTalking yet
- ✅ Limited bandwidth/time

### Use setup_livetalking_uv.bat if:
- ✅ Need LiveTalking now
- ✅ Have good internet connection
- ✅ Have 8GB+ VRAM GPU
- ✅ Ready to download models

### Use simple_setup_uv.bat if:
- ✅ Getting websockets error
- ✅ Environment is corrupt
- ✅ Packages not installing
- ✅ Need fresh start

## 🐛 Troubleshooting

### Error: "Failed to read websockets"

```bash
simple_setup_uv.bat
```

### Error: "Cannot delete .venv"

Close all:
- VS Code
- Terminals
- Python processes

Then try again.

### Error: "uv: command not found"

```bash
pip install uv
```

### Error: "LiveTalking submodule not found"

This is okay! quick_setup.bat works without it.

To add later:
```bash
git submodule update --init
setup_livetalking_uv.bat
```

### Setup Hangs at "Installing dependencies"

**Cause:** Downloading large packages (torch ~1.5GB)

**Solutions:**
1. Use verbose mode: `setup_livetalking_verbose.bat`
2. Install step-by-step: `quick_setup.bat` first, then add LiveTalking
3. Increase timeout: `set UV_HTTP_TIMEOUT=600`

### For Complete Troubleshooting

See `TROUBLESHOOTING_SETUP.md` for detailed solutions to all common issues.

Or run diagnostic:
```bash
diagnose_setup.bat
```

## ✅ Verification

After setup, verify:

```bash
# Check Python path
uv run python -c "import sys; print(sys.executable)"
# Should be: videoliveai\.venv\Scripts\python.exe

# Check imports
uv run python -c "import fastapi, pydantic; print('OK')"

# Run main
set MOCK_MODE=true
uv run python -m src.main
```

## 📊 Comparison

| Feature | quick_setup | setup_livetalking | simple_setup |
|---------|-------------|-------------------|--------------|
| **Time** | 2-5 min | 10-20 min | 5-10 min |
| **Size** | ~200MB | ~2GB | ~200MB |
| **LiveTalking** | ❌ No | ✅ Yes | ❌ No |
| **Use case** | Quick start | Full setup | Fix errors |

## 🎯 Recommended Workflow

```bash
# Day 1: Quick start
quick_setup.bat
set MOCK_MODE=true
uv run python -m src.main

# Day 2: Test features
# Develop, test, configure

# Day 3: Add LiveTalking
setup_livetalking_uv.bat
# Download models
# Prepare references

# Day 4: Go live!
uv run python -m src.main
```

## 📚 Additional Resources

- **TROUBLESHOOTING_SETUP.md** - Complete troubleshooting guide (10+ common issues)
- **UV_VS_CONDA_GUIDE.md** - UV vs Conda explained
- **LIVETALKING_QUICKSTART.md** - LiveTalking setup
- **README.md** - Main documentation

## 🔧 Diagnostic Tools

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `test_setup.bat` | Verify installation | After setup, before running |
| `diagnose_setup.bat` | Full diagnostic | When setup fails or hangs |
| `setup_livetalking_verbose.bat` | Debug mode setup | Troubleshooting LiveTalking install |

---

**Start with `quick_setup.bat` for fastest setup!**

**If setup hangs, see `TROUBLESHOOTING_SETUP.md` for solutions.**
