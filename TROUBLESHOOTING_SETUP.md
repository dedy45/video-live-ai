# Troubleshooting Setup Issues

> Panduan lengkap untuk mengatasi masalah setup VideoLiveAI dengan UV

## Quick Diagnosis

Jalankan diagnostic script dulu:

```bash
diagnose_setup.bat
```

Script ini akan check:
- UV installation
- Python version
- Virtual environment status
- Disk space
- Network connectivity
- UV cache
- Conda interference

## Common Issues & Solutions

### 1. Setup Hangs at "Installing dependencies"

**Symptoms:**
```
[3/5] Installing dependencies...
⠙ ai-live-commerce==0.3.1
```
Script hang dan tidak progress.

**Causes:**
- Downloading large packages (torch ~1.5GB)
- Network timeout
- Antivirus blocking
- Disk space full

**Solutions:**

**A. Use verbose mode untuk lihat progress:**
```bash
setup_livetalking_verbose.bat
```

**B. Install step-by-step:**
```bash
# 1. Core only (fast)
quick_setup.bat

# 2. Test core
test_setup.bat

# 3. Add LiveTalking later
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
uv pip install opencv-python scikit-image scipy librosa soundfile resampy
uv pip install aiortc av imageio imageio-ffmpeg
```

**C. Use CPU-only PyTorch (smaller download):**
```bash
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

**D. Increase timeout:**
```bash
set UV_HTTP_TIMEOUT=600
uv pip install -e ".[livetalking]"
```

---

### 2. "Failed to read websockets==16.0"

**Error:**
```
Failed to read metadata from installed package `websockets==16.0`
The system cannot find the file specified. (os error 2)
```

**Cause:** Corrupt package metadata in UV cache or `.venv`

**Solution:**
```bash
simple_setup_uv.bat
```

Or manual:
```bash
rmdir /s /q .venv
uv cache clean
uv venv
uv pip install -e . --no-cache
```

---

### 3. "uv: command not found"

**Cause:** UV not installed or not in PATH

**Solution:**
```bash
pip install uv
```

Or with pipx:
```bash
pipx install uv
```

Verify:
```bash
uv --version
```

---

### 4. Using Miniconda Python Instead of UV

**Symptoms:**
```
C:\Users\Dedy\miniconda3\python.exe
```

**Cause:** `.venv` not created or not activated

**Solution:**
```bash
cd videoliveai
uv venv
uv run python -c "import sys; print(sys.executable)"
# Should show: videoliveai\.venv\Scripts\python.exe
```

See `UV_VS_CONDA_GUIDE.md` for details.

---

### 5. "Module not found" After Install

**Symptoms:**
```python
ModuleNotFoundError: No module named 'fastapi'
```

**Cause:** Dependencies not installed in `.venv`

**Solution:**
```bash
# Check Python path
uv run python -c "import sys; print(sys.executable)"

# Install dependencies
uv pip install -e .

# Verify
uv pip list | findstr fastapi
```

---

### 6. Disk Space Issues

**Error:**
```
No space left on device
```

**Check space:**
```bash
wmic logicaldisk get caption,freespace,size
```

**Requirements:**
- Core only: ~500MB
- With LiveTalking: ~5GB

**Solution:**
- Free up disk space
- Or install to different drive:
  ```bash
  set UV_CACHE_DIR=D:\uv_cache
  uv venv
  ```

---

### 7. Network Timeout

**Error:**
```
Failed to download package
Connection timeout
```

**Solutions:**

**A. Increase timeout:**
```bash
set UV_HTTP_TIMEOUT=600
uv pip install -e ".[livetalking]"
```

**B. Use mirror (China users):**
```bash
uv pip install -e . --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

**C. Download offline:**
```bash
# On machine with good internet
uv pip download -e ".[livetalking]" -d packages/

# Transfer packages/ folder to target machine
uv pip install -e ".[livetalking]" --no-index --find-links packages/
```

---

### 8. Antivirus Blocking

**Symptoms:**
- Setup hangs randomly
- "Access denied" errors
- Slow installation

**Solution:**
1. Temporarily disable antivirus
2. Add exclusions:
   - `videoliveai\.venv\`
   - `%LOCALAPPDATA%\uv\`
   - `uv.exe`
   - `python.exe`

---

### 9. UV Lock File Out of Sync

**Error:**
```
The lockfile is out of date
```

**Solution:**
```bash
uv lock
uv sync
```

Or force update:
```bash
uv lock --upgrade
```

---

### 10. Git Submodule Not Found

**Error:**
```
LiveTalking submodule not found
```

**Solution:**
```bash
git submodule update --init --recursive
```

Or clone manually:
```bash
git clone https://github.com/lipku/LiveTalking.git external/livetalking
```

---

## Setup Scripts Comparison

| Script | Purpose | Time | Size | Use When |
|--------|---------|------|------|----------|
| `quick_setup.bat` | Core only | 2-5 min | ~200MB | First time, testing |
| `setup_livetalking_uv.bat` | Full setup | 10-20 min | ~2GB | Need LiveTalking |
| `setup_livetalking_verbose.bat` | Debug mode | 10-20 min | ~2GB | Troubleshooting |
| `simple_setup_uv.bat` | Clean install | 5-10 min | ~200MB | Fix corruption |
| `test_setup.bat` | Verify only | 1 min | 0 | Check status |
| `diagnose_setup.bat` | Diagnostic | 1 min | 0 | Find issues |

## Recommended Setup Flow

### For First Time Users:

```bash
# Step 1: Quick setup (fast, no LiveTalking)
quick_setup.bat

# Step 2: Test
test_setup.bat

# Step 3: Run in mock mode
set MOCK_MODE=true
uv run python -m src.main

# Step 4: Add LiveTalking when ready
setup_livetalking_uv.bat
```

### If Setup Fails:

```bash
# Step 1: Diagnose
diagnose_setup.bat

# Step 2: Clean install
simple_setup_uv.bat

# Step 3: Verify
test_setup.bat
```

### For Slow Internet:

```bash
# Step 1: Core only
quick_setup.bat

# Step 2: Install LiveTalking deps one by one
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install torchvision torchaudio
uv pip install opencv-python
uv pip install scikit-image scipy librosa soundfile resampy
uv pip install aiortc av imageio imageio-ffmpeg
```

## Manual Installation (If All Else Fails)

```bash
# 1. Create venv manually
python -m venv .venv

# 2. Activate
.venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install core
pip install -e .

# 5. Install LiveTalking (optional)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install opencv-python scikit-image scipy librosa soundfile resampy
pip install aiortc av imageio imageio-ffmpeg

# 6. Verify
python -c "import fastapi, torch; print('OK')"
```

## Getting Help

If none of the above works:

1. Run `diagnose_setup.bat` and save output
2. Check `data/logs/app.log` for errors
3. Create GitHub issue with:
   - Diagnostic output
   - Error messages
   - OS version
   - Python version
   - UV version

## Environment Variables

Useful UV environment variables:

```bash
# Increase timeout (default: 30s)
set UV_HTTP_TIMEOUT=600

# Change cache location
set UV_CACHE_DIR=D:\uv_cache

# Use mirror
set UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# Verbose output
set UV_VERBOSE=1

# No cache
set UV_NO_CACHE=1
```

## Verification Checklist

After setup, verify:

- [ ] UV installed: `uv --version`
- [ ] .venv exists: `dir .venv`
- [ ] Python path correct: `uv run python -c "import sys; print(sys.executable)"`
- [ ] Core packages: `uv run python -c "import fastapi, pydantic; print('OK')"`
- [ ] Config loads: `set MOCK_MODE=true && uv run python -c "from src.config import get_config; print('OK')"`
- [ ] Server starts: `set MOCK_MODE=true && uv run python -m src.main`

## Performance Tips

- Use `--no-cache` for clean installs
- Use `--verbose` to see progress
- Install core first, then LiveTalking
- Use CPU-only PyTorch if no GPU
- Close other programs during install
- Disable antivirus temporarily

---

**Still stuck? Run `diagnose_setup.bat` and check the output carefully!**
