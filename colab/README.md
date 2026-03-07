# LiveTalking Verification — Google Colab Notebooks

Folder ini berisi 4 notebook Colab untuk verifikasi setiap komponen LiveTalking stack secara terpisah di GPU cloud.

## Kenapa Colab?

LiveTalking butuh **NVIDIA GPU dengan 8GB+ VRAM** untuk inference. Colab menyediakan GPU T4 (16GB) gratis — cukup untuk verifikasi semua komponen.

## Urutan Testing

| # | Notebook | Komponen | Waktu | GPU Min |
|---|----------|----------|-------|---------|
| 1 | `01_MuseTalk_LipSync.ipynb` | MuseTalk 1.5 lip-sync | 10-15 min | T4 |
| 2 | `02_ER_NeRF_Avatar3D.ipynb` | ER-NeRF avatar 3D | 15-20 min | T4 |
| 3 | `03_GFPGAN_Enhancement.ipynb` | GFPGAN face enhance | 5-10 min | T4 |
| 4 | `04_LiveTalking_FullStack.ipynb` | LiveTalking server | 15-20 min | T4 |

## Cara Pakai

1. Buka notebook di Google Colab (klik kanan > Open with > Google Colab)
2. Pastikan GPU aktif: **Runtime > Change runtime type > GPU (T4)**
3. Jalankan cell satu per satu dari atas ke bawah
4. Setiap notebook punya **verification output** di akhir

## Expected Output per Notebook

### 01 — MuseTalk
- Video `.mp4` dengan bibir bergerak sinkron audio
- Benchmark: FPS dan realtime ratio

### 02 — ER-NeRF
- Module load verification (CUDA extensions)
- Training command reference

### 03 — GFPGAN
- Before/after face enhancement comparison
- Batch benchmark: FPS throughput

### 04 — LiveTalking Full Stack
- Server start verification
- Full stack readiness checklist (8 checks)
- RTMP streaming reference

## Setelah Verifikasi Berhasil

Copy hasil ke videoliveai lokal:

```bash
# Models
cp -r models/* /path/to/videoliveai/models/

# Avatar data
cp -r data/avatars/* /path/to/videoliveai/data/avatars/

# Aktifkan di .env
LIVETALKING_ENABLED=true
MOCK_MODE=false
```
