# LiveTalking Model Comparison Guide

## 🎯 Available Models

LiveTalking supports multiple lip-sync models. Choose based on your GPU and quality requirements.

## 📊 Model Comparison

| Model | Quality | Speed | GPU Required | VRAM | Size | Best For |
|-------|---------|-------|--------------|------|------|----------|
| **Wav2Lip** | Good | Fast | RTX 3060+ | 6GB | 150MB | Testing, Low-end GPU |
| **MuseTalk 1.5** | Better | Medium | RTX 3080 Ti+ | 8GB | 1.5GB | Production, Quality |
| **ER-NeRF** | Best | Slow | RTX 4090 | 12GB+ | 2GB | High-end, Best quality |

## 🚀 Quick Start by Model

### 1. Wav2Lip (Fastest, Good Quality)

**Best for:** Testing, development, lower-end GPUs

**Setup:**
```bash
setup_wav2lip_model.bat
```

**Run:**
```bash
run_livetalking_web.bat
```

**Pros:**
- ✅ Fast inference (60 FPS on RTX 3060)
- ✅ Small model size (150 MB)
- ✅ Works on RTX 3060
- ✅ Quick to setup

**Cons:**
- ❌ Lower quality than MuseTalk
- ❌ Less natural facial movements

---

### 2. MuseTalk 1.5 (Better Quality) ⭐ RECOMMENDED

**Best for:** Production, live streaming, better quality

**Setup:**
```bash
setup_musetalk_model.bat
```

**Run:**
```bash
run_livetalking_musetalk.bat
```

**Pros:**
- ✅ Better lip-sync quality
- ✅ More natural facial movements
- ✅ Better expression handling
- ✅ Production-ready

**Cons:**
- ❌ Requires RTX 3080 Ti or better
- ❌ Larger model size (1.5 GB)
- ❌ Slower than Wav2Lip (42 FPS on RTX 3080 Ti)

---

### 3. ER-NeRF (Best Quality)

**Best for:** High-end production, maximum quality

**Setup:**
```bash
setup_ernerf_model.bat  # Coming soon
```

**Pros:**
- ✅ Best quality
- ✅ 3D avatar rendering
- ✅ Most realistic

**Cons:**
- ❌ Requires RTX 4090
- ❌ Slowest (30-45 FPS)
- ❌ Largest model (2 GB)
- ❌ Most complex setup

---

## 🎮 Performance Benchmarks

### Wav2Lip

| GPU | FPS | Quality | VRAM Usage |
|-----|-----|---------|------------|
| RTX 3060 | 60 | Good | 4-5 GB |
| RTX 3080 Ti | 120 | Good | 4-5 GB |
| RTX 4090 | 150+ | Good | 4-5 GB |

### MuseTalk 1.5

| GPU | FPS | Quality | VRAM Usage |
|-----|-----|---------|------------|
| RTX 3080 Ti | 42 | Better | 6-7 GB |
| RTX 3090 | 45 | Better | 6-7 GB |
| RTX 4090 | 72 | Better | 6-7 GB |

### ER-NeRF

| GPU | FPS | Quality | VRAM Usage |
|-----|-----|---------|------------|
| RTX 4090 | 30-45 | Best | 10-12 GB |

## 🔧 Setup Instructions

### For Wav2Lip

```bash
# 1. Setup model
setup_wav2lip_model.bat

# 2. Download from:
# - Quark: https://pan.quark.cn/s/83a750323ef0
# - Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ

# 3. Place wav2lip256.pth in models/ (rename to wav2lip.pth)

# 4. Run
run_livetalking_web.bat
```

### For MuseTalk 1.5

```bash
# 1. Setup model
setup_musetalk_model.bat

# 2. Choose download method:
#    - Manual from LiveTalking sources
#    - Or HuggingFace CLI (automated)

# 3. Run
run_livetalking_musetalk.bat
```

## 📁 File Structure

```
videoliveai/
├── models/
│   ├── wav2lip.pth              # Wav2Lip model
│   ├── musetalk/                # MuseTalk models
│   │   ├── *.pth
│   │   └── ...
│   ├── er-nerf/                 # ER-NeRF models
│   │   └── ...
│   └── gfpgan/                  # Enhancement (optional)
│       └── ...
├── data/
│   └── avatars/
│       ├── wav2lip256_avatar1/  # Wav2Lip avatar
│       ├── musetalk_avatar1/    # MuseTalk avatar
│       └── ernerf_avatar1/      # ER-NeRF avatar
└── ...
```

## 🎯 Which Model Should I Use?

### Use Wav2Lip if:
- ✅ You have RTX 3060 or similar
- ✅ You need fast inference
- ✅ You're testing/developing
- ✅ You want quick setup

### Use MuseTalk 1.5 if: ⭐
- ✅ You have RTX 3080 Ti or better
- ✅ You need production quality
- ✅ You want better lip-sync
- ✅ You're doing live streaming

### Use ER-NeRF if:
- ✅ You have RTX 4090
- ✅ You need maximum quality
- ✅ You want 3D avatar
- ✅ Performance is not critical

## 🔄 Switching Between Models

You can switch models by editing the run script or using different scripts:

```bash
# Wav2Lip
run_livetalking_web.bat

# MuseTalk
run_livetalking_musetalk.bat

# Manual (edit app.py command):
python app.py --model wav2lip --avatar_id wav2lip256_avatar1
python app.py --model musetalk --avatar_id musetalk_avatar1
python app.py --model ernerf --avatar_id ernerf_avatar1
```

## 📚 Download Links

### Official LiveTalking Sources
- **Quark Cloud**: https://pan.quark.cn/s/83a750323ef0
- **Google Drive**: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ

### Original Repositories
- **Wav2Lip**: https://github.com/Rudrabha/Wav2Lip
- **MuseTalk**: https://github.com/TMElyralab/MuseTalk
- **ER-NeRF**: https://github.com/Fictionarry/ER-NeRF

### HuggingFace
- **MuseTalk**: https://huggingface.co/TMElyralab/MuseTalk
- **ER-NeRF**: https://huggingface.co/Fictionarry/ER-NeRF

## 🆘 Troubleshooting

### Out of Memory Error

**Solution:** Use smaller model or reduce resolution

```bash
# In .env file:
LIVETALKING_RESOLUTION=256,256  # Reduce from 512,512
```

### Low FPS

**Solution:** 
1. Check GPU utilization: `nvidia-smi`
2. Use faster model (Wav2Lip)
3. Reduce resolution
4. Close other GPU applications

### Model Not Found

**Solution:**
```bash
# Run appropriate setup script
setup_wav2lip_model.bat
# or
setup_musetalk_model.bat
```

## 🎓 Recommendations

### For Development/Testing:
→ **Wav2Lip** (fast, easy setup)

### For Production/Streaming:
→ **MuseTalk 1.5** (best balance of quality and performance)

### For Maximum Quality:
→ **ER-NeRF** (if you have RTX 4090)

---

**Current Setup:** You can start with Wav2Lip for testing, then upgrade to MuseTalk 1.5 for production! 🚀
