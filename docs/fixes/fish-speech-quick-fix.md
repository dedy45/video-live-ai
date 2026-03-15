# Fish-Speech Quick Fix - Gunakan v1.5 Dulu

## Tanggal: 15 Maret 2026, 23:33 WIB

## Masalah

S2-Pro model terlalu besar (~10GB) dan loading di CPU GTX 1650 4GB sangat lambat (>10 menit) bahkan kadang stuck.

## Solusi Cepat: Rollback ke v1.5

Fish-Speech v1.5 sudah pernah jalan dengan baik dan lebih ringan. Mari gunakan itu dulu untuk testing.

### Step 1: Stop S2-Pro Server

```powershell
# Server sedang jalan di Terminal ID: 5
# Akan di-stop otomatis saat rollback
```

### Step 2: Restore v1.5 dari Backup

```powershell
cd C:\Users\dedy\Documents\!fast-track-income\external

# Rename S2-Pro ke backup
Rename-Item fish-speech fish-speech-s2-pro-backup

# Restore v1.5
Copy-Item fish-speech-v1.5-backup-20260315-201917 fish-speech -Recurse
```

### Step 3: Start Fish-Speech v1.5 Server

```powershell
cd fish-speech
uv run python -m tools.api_server --listen 0.0.0.0:8080
```

## Kenapa v1.5 Lebih Baik untuk Sekarang?

| Aspek | v1.5 | S2-Pro |
|-------|------|--------|
| Model Size | ~2GB | ~10GB |
| Loading Time (CPU) | 1-2 menit | 10+ menit |
| Inference Speed (CPU) | 10-15 detik | 30-60 detik |
| Bahasa Indonesia | ✅ Bagus | ✅ Lebih Bagus |
| Emotion Tags | ❌ Tidak ada | ✅ Ada |
| VRAM 4GB | ✅ Cukup | ⚠️ Tight |

## Upgrade ke S2-Pro Nanti

Setelah pindah ke server production dengan GPU 8GB+:

```bash
cd external/fish-speech
git fetch origin
git checkout main  # S2-Pro
uv sync
uv run huggingface-cli download fishaudio/s2-pro --local-dir checkpoints/s2-pro
uv run python -m tools.api_server --listen 0.0.0.0:8080 \
    --llama-checkpoint-path checkpoints/s2-pro \
    --decoder-checkpoint-path checkpoints/s2-pro/codec.pth \
    --device cuda:0
```

## Testing Checklist v1.5

- [ ] Server start dalam <2 menit
- [ ] Port 8080 listening
- [ ] Health check OK: `curl http://127.0.0.1:8080/v1/health`
- [ ] Dashboard detect server
- [ ] Generate audio Indonesia berhasil
- [ ] Audio quality bagus (natural, bukan robot)
- [ ] Latency <15 detik per kalimat

## Catatan Penting

- v1.5 TIDAK support emotion tags seperti `[excited]`, `[whisper]`
- v1.5 tetap bagus untuk bahasa Indonesia
- Untuk production dengan emotion tags, perlu GPU 8GB+ dan S2-Pro
- Saat ini fokus testing functionality dulu, emotion tags nanti

---

**Status**: RECOMMENDED untuk testing lokal dengan GTX 1650 4GB
**Next**: Setelah deploy ke server GPU 8GB+, upgrade ke S2-Pro
