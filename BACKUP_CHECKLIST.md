# Backup Checklist - VideoLiveAI (UV Project)

## ✅ Yang HARUS Di-commit ke Git

### 1. Source Code
- ✅ `src/` - Semua source code
- ✅ `tests/` - Test suite
- ✅ `scripts/` - Setup & utility scripts
- ✅ `config/` - Configuration templates

### 2. Configuration Files
- ✅ `pyproject.toml` - Dependencies (UV)
- ✅ `.env.example` - Environment template
- ❌ `.env` - JANGAN commit (ada API keys!)
- ✅ `docker-compose.yml` - Docker setup
- ✅ `Dockerfile` - Container definition
- ✅ `prometheus.yml` - Monitoring config

### 3. Documentation
- ✅ `README.md` - Main documentation
- ✅ `AGENTS.md` - Agent documentation
- ✅ `PROJECT_SUMMARY.md` - Project summary
- ✅ `LIVETALKING_QUICKSTART.md` - LiveTalking guide
- ✅ `docs/` - All documentation

### 4. Git Configuration
- ✅ `.gitignore` - Ignore rules
- ✅ `.dockerignore` - Docker ignore
- ✅ `.github/` - GitHub workflows (CI/CD)

### 5. Scripts & Utilities
- ✅ `*.bat` - Windows batch scripts
- ✅ `*.sh` - Shell scripts
- ✅ `*.py` - Python scripts

### 6. Asset Structure (Empty folders with .gitkeep)
- ✅ `assets/avatar/.gitkeep`
- ✅ `assets/voice/.gitkeep`
- ✅ `assets/backgrounds/.gitkeep`
- ✅ `assets/products/.gitkeep`
- ✅ `data/.gitkeep`
- ✅ `data/logs/.gitkeep`
- ✅ `models/.gitkeep`

## ❌ Yang TIDAK Boleh Di-commit

### 1. UV Virtual Environment
- ❌ `.venv/` - Virtual environment (bisa 500MB+)
- ❌ `uv.lock` - Lock file (auto-generated)
- ❌ `.uv/` - UV cache

**Kenapa?** Setiap developer bisa recreate dengan `uv pip install -e .`

### 2. Python Cache
- ❌ `__pycache__/` - Python bytecode
- ❌ `*.pyc`, `*.pyo` - Compiled Python
- ❌ `.pytest_cache/` - Pytest cache
- ❌ `.ruff_cache/` - Ruff linter cache
- ❌ `.hypothesis/` - Hypothesis test cache

### 3. Environment & Secrets
- ❌ `.env` - Contains API keys!
- ❌ `*.key`, `*.pem` - Private keys
- ❌ `secrets/` - Secret files

**PENTING:** Jangan pernah commit API keys!

### 4. Model Weights (BESAR!)
- ❌ `models/` - Model weights (bisa 5GB+)
- ❌ `*.pt`, `*.pth` - PyTorch models
- ❌ `*.ckpt` - Checkpoints
- ❌ `*.safetensors` - Safetensors format
- ❌ `*.bin` - Binary models

**Kenapa?** Terlalu besar untuk Git. Download terpisah atau gunakan Git LFS.

### 5. Runtime Data
- ❌ `data/*.db` - SQLite databases
- ❌ `data/logs/` - Log files
- ❌ `data/cache/` - Cache files
- ❌ `*.log` - Log files

### 6. User Assets (Bisa Besar)
- ❌ `assets/avatar/*.mp4` - Reference videos (500MB+)
- ❌ `assets/avatar/*.jpg`, `*.png` - Avatar images
- ❌ `assets/voice/*.wav` - Voice samples
- ❌ `assets/products/*.jpg` - Product images (ratusan file)

**Kenapa?** User-specific dan bisa sangat besar.

### 7. IDE & OS Files
- ❌ `.vscode/` - VS Code settings
- ❌ `.idea/` - PyCharm settings
- ❌ `.kiro/` - Kiro IDE settings
- ❌ `.DS_Store` - macOS
- ❌ `Thumbs.db` - Windows

### 8. External Dependencies
- ❌ `external/livetalking/` - Git submodule (tracked separately)

## 📊 Estimasi Ukuran

### Yang Di-commit (~50MB)
```
src/                    ~5MB   (source code)
tests/                  ~2MB   (test files)
docs/                   ~3MB   (documentation)
config/                 ~1MB   (configs)
scripts/                ~1MB   (scripts)
.github/                ~500KB (workflows)
pyproject.toml          ~5KB
README.md               ~20KB
Other files             ~1MB
```

### Yang TIDAK Di-commit (~10GB+)
```
.venv/                  ~500MB  (UV virtual env)
models/                 ~5GB    (model weights)
assets/avatar/          ~1GB    (reference videos)
assets/products/        ~500MB  (product images)
data/                   ~100MB  (databases & logs)
__pycache__/            ~50MB   (Python cache)
external/livetalking/   ~2GB    (submodule)
```

## 🔄 Cara Recreate Environment

Setelah clone repository, developer lain bisa recreate dengan:

```bash
# 1. Clone repository
git clone https://github.com/dedy45/video-live-ai.git
cd video-live-ai

# 2. Install UV (jika belum)
pip install uv

# 3. Create virtual environment & install dependencies
uv pip install -e ".[livetalking]"

# 4. Copy environment file
cp .env.example .env
# Edit .env dengan API keys masing-masing

# 5. Setup LiveTalking (optional)
python scripts/setup_livetalking.py

# 6. Download models (manual atau script)
# Models tidak di-commit, harus download terpisah

# 7. Prepare assets (user-specific)
# Record reference video & audio
```

## 🎯 Git LFS (Optional untuk Assets Besar)

Jika ingin commit assets besar (reference video, models), gunakan Git LFS:

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.mp4"
git lfs track "*.pth"
git lfs track "*.ckpt"

# Commit .gitattributes
git add .gitattributes
git commit -m "Add Git LFS tracking"
```

**Note:** Git LFS berbayar untuk storage besar. Lebih baik download terpisah.

## 📦 Alternative: External Storage

Untuk model weights & assets besar:

1. **Google Drive / Dropbox**
   - Upload models & assets
   - Share link di README
   - Developer download manual

2. **Hugging Face Hub**
   - Upload models ke Hugging Face
   - Download via `huggingface_hub`

3. **AWS S3 / Cloud Storage**
   - Upload ke cloud storage
   - Download via script

## ✅ Pre-commit Checklist

Sebelum commit, pastikan:

- [ ] `.env` tidak ter-commit (check dengan `git status`)
- [ ] Tidak ada API keys di code
- [ ] `.venv/` tidak ter-commit
- [ ] `models/` tidak ter-commit
- [ ] Test pass: `pytest tests/ -v`
- [ ] Linter pass: `ruff check src/`
- [ ] Documentation updated

## 🚨 Jika Accidentally Commit Secrets

Jika tidak sengaja commit `.env` atau API keys:

```bash
# 1. Remove from Git history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 2. Force push (HATI-HATI!)
git push origin --force --all

# 3. ROTATE API KEYS IMMEDIATELY!
# Semua API keys yang ter-commit harus diganti!
```

## 📝 Summary

**Commit:**
- ✅ Source code
- ✅ Configuration templates
- ✅ Documentation
- ✅ Scripts
- ✅ Empty folder structure

**Jangan Commit:**
- ❌ `.venv/` (UV virtual environment)
- ❌ `.env` (secrets)
- ❌ `models/` (terlalu besar)
- ❌ `assets/` (user-specific)
- ❌ `data/` (runtime generated)
- ❌ Cache files

**Prinsip:** Commit hanya yang diperlukan untuk recreate project, bukan runtime artifacts atau user-specific data.
