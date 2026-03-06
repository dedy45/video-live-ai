# UV vs Conda - Panduan Lengkap

## ❓ Kenapa UV Menggunakan Miniconda Python?

Ketika Anda menjalankan `uv run python`, UV mencari Python interpreter dengan urutan:

1. `.venv/Scripts/python.exe` (UV virtual environment) - **PRIORITAS TERTINGGI**
2. System Python (dari PATH)
3. Conda Python (jika ada di PATH)

**Masalah Anda**: UV tidak menemukan `.venv` atau `.venv` belum dibuat, jadi fallback ke miniconda Python.

## 🔧 Solusi: Gunakan UV Virtual Environment

### Cara 1: Otomatis dengan Batch File (RECOMMENDED)

```bash
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
setup_livetalking_uv.bat
```

Script ini akan:
1. Check UV installed
2. Create `.venv` jika belum ada
3. Install dependencies ke `.venv`
4. Run setup dengan UV Python (bukan conda)

### Cara 2: Manual Step-by-Step

```bash
# 1. Masuk ke folder videoliveai
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai

# 2. Create UV virtual environment
uv venv

# 3. Install dependencies
uv pip install -e ".[livetalking]"

# 4. Run script dengan UV
uv run python scripts/setup_livetalking.py
```

### Cara 3: Activate Virtual Environment Manual

```bash
# 1. Masuk ke folder videoliveai
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai

# 2. Create venv jika belum ada
uv venv

# 3. Activate venv
.venv\Scripts\activate

# 4. Install dependencies
pip install -e ".[livetalking]"

# 5. Run script (sekarang pakai .venv Python)
python scripts/setup_livetalking.py
```

## 🎯 Verifikasi Python yang Digunakan

### Check Python Path

```bash
# Dengan UV
uv run python -c "import sys; print(sys.executable)"

# Output yang BENAR:
# C:\Users\dedy\Documents\!fast-track-income\videoliveai\.venv\Scripts\python.exe

# Output yang SALAH (conda):
# C:\Users\Dedy\miniconda3\python.exe
```

### Check Virtual Environment

```bash
# Check jika .venv ada
dir .venv

# Check packages installed
uv pip list
```

## 🚨 Common Errors & Solutions

### Error 1: "can't open file ... No such file or directory"

**Penyebab**: Path salah atau tidak di folder yang benar

**Solusi**:
```bash
# Check current directory
pwd

# Harus di: C:\Users\dedy\Documents\!fast-track-income\videoliveai
# Jika tidak, cd ke folder yang benar:
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
```

### Error 2: "Using miniconda3\python.exe"

**Penyebab**: `.venv` belum dibuat atau tidak terdeteksi

**Solusi**:
```bash
# Create .venv
uv venv

# Verify .venv created
dir .venv

# Run dengan UV
uv run python scripts/setup_livetalking.py
```

### Error 3: "Module not found"

**Penyebab**: Dependencies belum diinstall di `.venv`

**Solusi**:
```bash
# Install dependencies
uv pip install -e ".[livetalking]"

# Verify installed
uv pip list
```

## 📊 UV vs Conda Comparison

| Aspek | UV | Conda |
|-------|----|----|
| **Speed** | ⚡ Sangat cepat (Rust) | 🐌 Lambat (Python) |
| **Size** | 📦 Kecil (~50MB) | 📦 Besar (~500MB) |
| **Isolation** | ✅ Per-project (.venv) | ⚠️ Global atau per-env |
| **Python Version** | ✅ Bisa pilih | ✅ Bisa pilih |
| **Package Source** | PyPI | Conda channels |
| **Lock File** | uv.lock | environment.yml |

## 🎯 Best Practice untuk Project Ini

### 1. Selalu Gunakan UV

```bash
# BENAR ✅
uv run python script.py
uv pip install package

# SALAH ❌
python script.py  # Bisa pakai conda Python
pip install package  # Bisa install ke conda
```

### 2. Check Virtual Environment

```bash
# Sebelum run apapun, pastikan .venv ada
dir .venv

# Jika tidak ada, create:
uv venv
```

### 3. Jangan Mix UV dan Conda

```bash
# JANGAN lakukan ini:
conda activate base
uv run python script.py  # Confusing!

# LAKUKAN ini:
# Jangan activate conda
# Langsung pakai UV
uv run python script.py
```

## 🔄 Migration dari Conda ke UV

Jika Anda terbiasa dengan conda:

| Conda Command | UV Equivalent |
|---------------|---------------|
| `conda create -n env` | `uv venv` |
| `conda activate env` | `.venv\Scripts\activate` |
| `conda install package` | `uv pip install package` |
| `conda list` | `uv pip list` |
| `python script.py` | `uv run python script.py` |

## 📁 Struktur Project dengan UV

```
videoliveai/
├── .venv/                    # UV virtual environment (JANGAN commit!)
│   ├── Scripts/
│   │   └── python.exe        # UV Python (bukan conda!)
│   └── Lib/
├── pyproject.toml            # Dependencies definition
├── uv.lock                   # Lock file (auto-generated)
└── scripts/
    └── setup_livetalking.py  # Run dengan: uv run python scripts/...
```

## ✅ Quick Check

Jalankan ini untuk verify setup:

```bash
cd videoliveai

# 1. Check UV version
uv --version

# 2. Check .venv exists
dir .venv

# 3. Check Python path (harus .venv, bukan conda)
uv run python -c "import sys; print(sys.executable)"

# 4. Check packages installed
uv pip list
```

## 🎉 Summary

**Masalah**: UV menggunakan conda Python karena `.venv` belum dibuat

**Solusi**: 
1. Create `.venv` dengan `uv venv`
2. Install dependencies dengan `uv pip install -e .`
3. Run script dengan `uv run python script.py`

**Best Practice**: Selalu gunakan `uv run` atau activate `.venv` sebelum run script

---

**Gunakan `setup_livetalking_uv.bat` untuk setup otomatis yang benar!**
