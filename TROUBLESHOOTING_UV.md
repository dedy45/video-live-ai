# Troubleshooting UV Setup Issues

## 🔴 Error: Failed to read `websockets==16.0`

### Masalah

```
Failed to read metadata from installed package `websockets==16.0`
Failed to open file: C:\...\websockets-16.0.dist-info\METADATA
The system cannot find the file specified. (os error 2)
```

### Penyebab

1. **Corrupt package metadata** - Package ter-install sebagian atau corrupt
2. **UV cache corrupt** - Cache UV menyimpan metadata yang rusak
3. **Interrupted installation** - Install sebelumnya ter-interrupt

### ✅ Solusi 1: Simple Setup (RECOMMENDED)

```bash
cd videoliveai
simple_setup_uv.bat
```

Script ini akan:
1. Delete `.venv` yang corrupt
2. Clean UV cache
3. Create fresh `.venv`
4. Install dengan `--no-cache` (avoid corrupt cache)

### ✅ Solusi 2: Manual Fix

```bash
# 1. Delete corrupt .venv
cd videoliveai
rmdir /s /q .venv

# 2. Clean UV cache
uv cache clean

# 3. Create fresh venv
uv venv

# 4. Install WITHOUT cache
uv pip install --no-cache -e .
```

### ✅ Solusi 3: Minimal Install (Jika masih error)

```bash
# 1. Clean setup
cd videoliveai
rmdir /s /q .venv
uv cache clean
uv venv

# 2. Install minimal dependencies only
uv pip install --no-cache fastapi uvicorn pydantic python-dotenv

# 3. Test
set MOCK_MODE=true
uv run python -m src.main

# 4. Install additional packages as needed
uv pip install --no-cache websockets
uv pip install --no-cache edge-tts
# etc...
```

## 🔴 Error: Cannot delete .venv

### Masalah

```
ERROR: Cannot delete .venv
Access denied or file in use
```

### Penyebab

- Python process masih running
- VS Code atau IDE masih menggunakan .venv
- Terminal masih di dalam .venv

### ✅ Solusi

```bash
# 1. Close semua:
# - VS Code
# - Terminal yang activate .venv
# - Python processes

# 2. Check processes
tasklist | findstr python

# 3. Kill if needed
taskkill /F /IM python.exe

# 4. Try delete again
rmdir /s /q .venv
```

## 🔴 Error: uv: command not found

### Masalah

```
'uv' is not recognized as an internal or external command
```

### Penyebab

UV not installed or not in PATH

### ✅ Solusi

```bash
# Install UV
pip install uv

# Or with conda
conda install -c conda-forge uv

# Verify
uv --version
```

## 🔴 Error: Python version mismatch

### Masalah

```
ERROR: Requires Python >=3.10, but found 3.9
```

### Penyebab

System Python too old

### ✅ Solusi

```bash
# Create venv with specific Python version
uv venv --python 3.13

# Or specify Python path
uv venv --python C:\Python313\python.exe
```

## 🔴 Error: Package conflicts

### Masalah

```
ERROR: Cannot install package-a and package-b
Conflicting dependencies
```

### Penyebab

Dependency version conflicts

### ✅ Solusi

```bash
# 1. Check conflicts
uv pip check

# 2. Install without dependencies first
uv pip install --no-deps package-name

# 3. Install dependencies manually
uv pip install dependency1 dependency2
```

## 🔴 Error: Slow installation

### Masalah

Installation takes forever or hangs

### Penyebab

- Large packages (torch, opencv)
- Slow network
- Building from source

### ✅ Solusi

```bash
# 1. Use --no-cache to avoid cache issues
uv pip install --no-cache package-name

# 2. Install pre-built wheels
uv pip install --only-binary :all: package-name

# 3. Increase timeout
uv pip install --timeout 300 package-name
```

## 🔴 Error: Import errors after install

### Masalah

```python
ModuleNotFoundError: No module named 'package'
```

### Penyebab

- Wrong Python interpreter
- Package not installed in active venv

### ✅ Solusi

```bash
# 1. Verify Python path
uv run python -c "import sys; print(sys.executable)"
# Should be: videoliveai\.venv\Scripts\python.exe

# 2. Verify package installed
uv pip list | findstr package-name

# 3. Reinstall if needed
uv pip install --force-reinstall package-name
```

## 📋 Diagnostic Commands

### Check UV Setup

```bash
# UV version
uv --version

# Python version in venv
uv run python --version

# Python path
uv run python -c "import sys; print(sys.executable)"

# Installed packages
uv pip list

# Check for issues
uv pip check
```

### Check Environment

```bash
# Current directory
pwd

# Check .venv exists
dir .venv

# Check pyproject.toml exists
dir pyproject.toml

# Check UV cache
uv cache dir
```

## 🎯 Best Practices

### DO ✅

1. **Always clean cache** when having issues
   ```bash
   uv cache clean
   ```

2. **Use --no-cache** for problematic packages
   ```bash
   uv pip install --no-cache package-name
   ```

3. **Delete .venv** when corrupt
   ```bash
   rmdir /s /q .venv
   uv venv
   ```

4. **Verify Python path** after setup
   ```bash
   uv run python -c "import sys; print(sys.executable)"
   ```

### DON'T ❌

1. **Don't mix conda and UV**
   ```bash
   # ❌ WRONG
   conda activate base
   uv pip install package
   ```

2. **Don't install globally**
   ```bash
   # ❌ WRONG
   pip install package  # Goes to conda/system
   
   # ✅ CORRECT
   uv pip install package  # Goes to .venv
   ```

3. **Don't ignore errors**
   - If install fails, check error message
   - Don't just retry without fixing

## 🚀 Quick Fix Flowchart

```
Error occurred?
    ↓
Delete .venv
    ↓
Clean UV cache (uv cache clean)
    ↓
Create fresh venv (uv venv)
    ↓
Install with --no-cache
    ↓
Still error?
    ↓
Try minimal install
    ↓
Still error?
    ↓
Check Python version
    ↓
Check disk space
    ↓
Check antivirus blocking
```

## 📞 Getting Help

If still having issues:

1. **Check logs**
   ```bash
   # UV logs
   uv pip install --verbose package-name
   ```

2. **Check system**
   ```bash
   # Disk space
   dir C:\
   
   # Python version
   python --version
   
   # UV version
   uv --version
   ```

3. **Try alternative**
   ```bash
   # Use pip directly in venv
   .venv\Scripts\activate
   pip install package-name
   ```

## 🎉 Success Checklist

After setup, verify:

- [ ] `.venv` folder exists
- [ ] Python path is `.venv\Scripts\python.exe`
- [ ] Can import packages: `uv run python -c "import fastapi"`
- [ ] Can run main: `uv run python -m src.main`
- [ ] No error messages

---

**Use `simple_setup_uv.bat` for automatic fix!**
