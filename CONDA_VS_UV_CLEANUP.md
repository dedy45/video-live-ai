# Conda vs UV - Cleanup & Setup Guide

## 🔍 Analisis Conda Base Environment

Saya sudah check conda base environment Anda:

### ✅ Good News: Conda Base Bersih!

Packages yang ter-install di conda base:
- ❌ **torch** - TIDAK ada
- ❌ **opencv** - TIDAK ada  
- ❌ **aiortc** - TIDAK ada
- ❌ **librosa** - TIDAK ada
- ❌ **soundfile** - TIDAK ada

**Kesimpulan**: Conda base environment Anda bersih. Tidak ada packages besar dari LiveTalking yang ter-install.

### 📊 Packages di Conda Base

Yang ada di conda base (normal packages):
- Python 3.13.11
- conda, pip, setuptools
- Development tools (pytest, mypy, ruff)
- ML tools (mlflow, pandas, numpy, scikit-learn)
- API tools (fastapi, httpx, requests)
- Database tools (sqlalchemy)

**Total**: ~200 packages (normal untuk conda base)

## 🎯 Kenapa UV Menggunakan Conda Python?

Ketika Anda run `uv run python scripts/setup_livetalking.py`, UV mencari Python dengan urutan:

1. **`.venv/Scripts/python.exe`** (UV virtual environment) ← PRIORITAS
2. System Python (dari PATH)
3. Conda Python (jika ada di PATH)

**Yang terjadi**: UV tidak menemukan `.venv`, jadi fallback ke conda Python.

## ✅ Solusi: Setup UV Environment yang Benar

### Option 1: Otomatis dengan Script (RECOMMENDED)

```bash
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
clean_and_setup_uv.bat
```

Script ini akan:
1. Delete `.venv` lama (jika ada)
2. Create fresh `.venv` dengan UV
3. Install dependencies ke `.venv`
4. Verify Python path (harus `.venv`, bukan conda)

### Option 2: Manual Step-by-Step

```bash
# 1. Masuk ke folder videoliveai
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai

# 2. Delete .venv lama (jika ada)
rmdir /s /q .venv

# 3. Create fresh UV venv
uv venv

# 4. Verify Python path
uv run python -c "import sys; print(sys.executable)"
# Output harus: C:\...\videoliveai\.venv\Scripts\python.exe

# 5. Install dependencies
uv pip install -e ".[livetalking]"

# 6. Verify packages
uv pip list
```

## 🧹 Apakah Perlu Clean Conda?

### ❌ TIDAK Perlu Uninstall dari Conda

**Alasan**:
1. Conda base Anda sudah bersih (tidak ada packages LiveTalking)
2. Packages di conda base tidak mengganggu UV
3. Conda base berguna untuk project lain

### ✅ Yang Perlu Dilakukan

1. **Create UV virtual environment** di videoliveai
2. **Install packages ke `.venv`** (bukan conda)
3. **Selalu gunakan `uv run`** untuk run script

## 📋 Checklist Setup yang Benar

### Before (Salah)
```bash
# ❌ SALAH - Tidak ada .venv
cd videoliveai
uv run python scripts/setup_livetalking.py
# Result: Menggunakan conda Python
```

### After (Benar)
```bash
# ✅ BENAR - Ada .venv
cd videoliveai
uv venv                                    # Create .venv
uv pip install -e ".[livetalking]"        # Install ke .venv
uv run python scripts/setup_livetalking.py # Pakai .venv Python
# Result: Menggunakan UV Python
```

## 🔍 Cara Verify Setup Benar

### 1. Check .venv Exists

```bash
cd videoliveai
dir .venv
# Harus ada folder .venv
```

### 2. Check Python Path

```bash
uv run python -c "import sys; print(sys.executable)"

# Output yang BENAR:
# C:\Users\dedy\Documents\!fast-track-income\videoliveai\.venv\Scripts\python.exe

# Output yang SALAH:
# C:\Users\Dedy\miniconda3\python.exe
```

### 3. Check Packages Location

```bash
uv pip list
# Harus show packages di .venv, bukan conda
```

## 🎯 Best Practice

### DO ✅

```bash
# Selalu dari folder videoliveai
cd videoliveai

# Gunakan uv run
uv run python script.py
uv run pytest tests/
uv run python -m src.main

# Atau activate .venv
.venv\Scripts\activate
python script.py
```

### DON'T ❌

```bash
# Jangan activate conda
conda activate base  # ❌

# Jangan run tanpa uv atau .venv
python script.py  # ❌ Bisa pakai conda Python

# Jangan install ke conda
pip install package  # ❌ Install ke conda
```

## 📊 Comparison

| Aspect | Conda Base | UV .venv |
|--------|-----------|----------|
| **Location** | C:\Users\Dedy\miniconda3 | videoliveai\.venv |
| **Packages** | ~200 (global) | ~50 (project-specific) |
| **Size** | ~500MB | ~200MB |
| **Isolation** | ❌ Global | ✅ Per-project |
| **Speed** | 🐌 Slow | ⚡ Fast |
| **For videoliveai** | ❌ Don't use | ✅ Use this |

## 🚀 Quick Start (Fresh Setup)

```bash
# 1. Clean start
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
clean_and_setup_uv.bat

# 2. Test
test_livetalking.bat

# 3. Setup LiveTalking
setup_livetalking_uv.bat
```

## 📚 Scripts Available

1. **check_and_clean_conda.bat** - Check conda base (informational)
2. **clean_and_setup_uv.bat** - Clean & setup UV venv (recommended)
3. **setup_livetalking_uv.bat** - Setup LiveTalking dengan UV
4. **test_livetalking.bat** - Test integration

## ✅ Summary

**Conda Base**: Bersih, tidak perlu uninstall apapun

**Yang Perlu Dilakukan**:
1. Create `.venv` dengan `uv venv`
2. Install dependencies dengan `uv pip install -e .`
3. Selalu gunakan `uv run` atau activate `.venv`

**Result**: UV akan menggunakan `.venv` Python, bukan conda Python

---

**Run `clean_and_setup_uv.bat` untuk setup yang benar!**
