# LiveTalking Integration - Quick Start Guide

## Apa yang Sudah Dibuat?

Integrasi LiveTalking ke dalam `videoliveai` sudah siap dengan struktur berikut:

```
videoliveai/
├── src/face/
│   ├── pipeline.py              # Existing (MuseTalk basic)
│   └── livetalking_adapter.py   # NEW - LiveTalking wrapper
├── scripts/
│   └── setup_livetalking.py     # NEW - Setup automation
├── tests/
│   └── test_livetalking_integration.py  # NEW - Tests
└── external/                    # Will be created
    └── livetalking/             # Git submodule
```

## Langkah-Langkah Setup (5 Menit)

### 1. Install LiveTalking (Otomatis)

```bash
cd C:\Users\dedy\Documents\!fast-track-income\videoliveai
python scripts/setup_livetalking.py
```

Script ini akan:
- Clone LiveTalking sebagai git submodule
- Install dependencies
- Create folder untuk models
- Update .env dengan config LiveTalking

### 2. Test dengan Mock Mode (Tanpa GPU)

```bash
set MOCK_MODE=true
uv run pytest tests/test_livetalking_integration.py -v
```

Ini akan test integrasi tanpa butuh GPU atau model weights.

### 3. Prepare Reference Materials

Untuk production, Anda butuh:

**Reference Video (5 menit):**
- Record video wajah Anda berbicara
- Resolusi minimal 512x512
- Format: MP4
- Simpan di: `assets/avatar/reference.mp4`

**Reference Audio (3-10 detik):**
- Record suara Anda berbicara
- Format: WAV
- Simpan di: `assets/avatar/reference.wav`

### 4. Download Model Weights

```bash
# MuseTalk 1.5 (~1.5GB)
# Download dari: https://github.com/TMElyralab/MuseTalk/releases

# ER-NeRF (~2GB)
# Download dari: https://github.com/Fictionarry/ER-NeRF

# GFPGAN (~1.5GB)
# Download dari: https://github.com/TencentARC/GFPGAN/releases
```

Simpan di folder:
- `models/musetalk/`
- `models/er-nerf/`
- `models/gfpgan/`

### 5. Test End-to-End

```bash
# Test dengan mock mode dulu
set MOCK_MODE=true
uv run python -m src.main

# Jika berhasil, test dengan GPU
set MOCK_MODE=false
uv run python -m src.main
```

## Cara Menggunakan di Code

### Option A: Ganti Face Pipeline (Recommended)

Edit `src/main.py` atau file orchestrator:

```python
# BEFORE (MuseTalk basic)
from src.face.pipeline import AvatarPipeline

# AFTER (LiveTalking)
from src.face.livetalking_adapter import LiveTalkingPipeline as AvatarPipeline
```

### Option B: Conditional Switch

```python
from src.config import get_config

config = get_config()

if config.get("livetalking_enabled", False):
    from src.face.livetalking_adapter import LiveTalkingPipeline
    pipeline = LiveTalkingPipeline()
else:
    from src.face.pipeline import AvatarPipeline
    pipeline = AvatarPipeline()
```

## Konfigurasi (.env)

```bash
# Enable LiveTalking
LIVETALKING_ENABLED=true

# Reference files
LIVETALKING_REFERENCE_VIDEO=assets/avatar/reference.mp4
LIVETALKING_REFERENCE_AUDIO=assets/avatar/reference.wav

# Streaming options
LIVETALKING_USE_WEBRTC=false  # For browser
LIVETALKING_USE_RTMP=true     # For TikTok/Shopee

# Performance
LIVETALKING_FPS=30
LIVETALKING_RESOLUTION=512,512
```

## Testing Strategy

### Level 1: Unit Tests (No GPU)
```bash
set MOCK_MODE=true
pytest tests/test_livetalking_integration.py -v -m "not integration"
```

### Level 2: Integration Tests (With GPU)
```bash
pytest tests/test_livetalking_integration.py -v
```

### Level 3: End-to-End Test
```bash
uv run python -m src.main
# Check dashboard: http://localhost:8000
```

## Troubleshooting

### Error: "LiveTalking not found"
```bash
git submodule update --init --recursive
```

### Error: "Reference video missing"
- Pastikan file ada di `assets/avatar/reference.mp4`
- Atau gunakan `MOCK_MODE=true` untuk testing

### Error: "GPU out of memory"
- Turunkan resolusi: `LIVETALKING_RESOLUTION=256,256`
- Turunkan FPS: `LIVETALKING_FPS=25`
- Atau gunakan `MOCK_MODE=true`

### Error: "Models not found"
- Download models manual (lihat step 4)
- Atau skip untuk testing dengan mock mode

## Performance Expectations

### Mock Mode (No GPU)
- Latency: ~100ms
- Quality: Low (dummy frames)
- Use case: Development/testing

### Production Mode (RTX 3060+)
- Latency: ~2-3 seconds
- FPS: 30-60fps
- Quality: Hyper-realistic
- Use case: Live streaming

## Next Steps

1. **Test Mock Mode** - Pastikan integrasi jalan tanpa GPU
2. **Prepare References** - Record video & audio
3. **Download Models** - Get model weights
4. **Train Avatar** - Run ER-NeRF training
5. **Go Live** - Start streaming!

## Comparison: MuseTalk vs LiveTalking

| Feature | MuseTalk (Basic) | LiveTalking |
|---------|------------------|-------------|
| Real-time | ⚠️ Partial | ✅ 60fps |
| RTMP Built-in | ❌ No | ✅ Yes |
| WebRTC | ❌ No | ✅ Yes |
| Enhancement | Manual GFPGAN | ✅ Built-in |
| Production Ready | ⚠️ Demo | ✅ Yes |
| Setup Complexity | Low | Medium |

## Support

Jika ada masalah:
1. Check logs: `data/logs/app.log`
2. Run diagnostic: `curl http://localhost:8000/diagnostic/health`
3. Check GPU: `nvidia-smi`
4. Test mock mode: `set MOCK_MODE=true`

## Resources

- LiveTalking Repo: https://github.com/lipku/LiveTalking
- MuseTalk: https://github.com/TMElyralab/MuseTalk
- ER-NeRF: https://github.com/Fictionarry/ER-NeRF
- GFPGAN: https://github.com/TencentARC/GFPGAN
