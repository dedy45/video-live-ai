# Fish-Speech S2-Pro Upgrade Status

## Tanggal: 15 Maret 2026

## Status Saat Ini: LOADING S2-PRO MODEL (GPU MODE)

### ✅ Yang Sudah Selesai

1. **PyTorch CUDA di VideoLiveAI Control Plane**
   - Status: ✅ BERHASIL
   - PyTorch 2.10.0+cu126 terinstall dengan benar
   - CUDA Available: True
   - Device: NVIDIA GeForce GTX 1650 (4GB VRAM)
   - Lokasi: `videoliveai/.venv/`

2. **Fish-Speech Repository & Model**
   - Status: ✅ BERHASIL
   - Branch: main (latest, S2-Pro support)
   - Commit: 1618b7b (updated from v1.5.1)
   - Model S2-Pro: ✅ Downloaded (~11GB)
   - Lokasi: `external/fish-speech/checkpoints/s2-pro/`
   - Files: config.json, codec.pth, model.safetensors.index.json, tokenizer files

3. **Upgrade Scripts**
   - ✅ `scripts/upgrade-to-s2.ps1` - PowerShell script untuk Windows
   - ✅ `scripts/upgrade-to-s2.sh` - Bash script untuk Linux
   - ✅ `scripts/test-s2-indonesia.py` - Test cases bahasa Indonesia

### ✅ Yang Sudah Selesai (Lanjutan)

5. **Fish-Speech Dependencies Update**
   - Status: ✅ BERHASIL
   - Installed: descript-audiotools 0.7.2 (untuk S2-Pro)
   - Updated: fish-speech 2.0.0, transformers 4.57.3
   - PyTorch CUDA: 2.5.1+cu121 (reinstalled after dependency update)

### 🔄 Sedang Berjalan

**Fish-Speech S2-Pro Server Loading**
- Status: 🔄 LOADING MODEL
- Terminal ID: 9
- Device: cuda:0 (GPU mode)
- Model: DualARModelArgs (36 layers, 2560 dim, 155776 vocab)
- Progress: Loading safetensors ke GPU (proses bisa 2-5 menit)
- Port: 8080 (belum responding, masih loading)

### 🔄 Next Steps

#### Immediate (Untuk Testing)

1. **Tunggu Fish-Speech Server Selesai Loading**
   ```powershell
   # Cek status server
   cd external/fish-speech
   # Tunggu sampai muncul "Application startup complete"
   ```

2. **Test Server Health**
   ```powershell
   curl http://127.0.0.1:8080/v1/health
   ```

3. **Restart VideoLiveAI Dashboard**
   ```powershell
   cd videoliveai
   uv run python scripts/manage.py start app
   ```

4. **Test Generate Audio dari Dashboard**
   - Buka: http://127.0.0.1:8001/dashboard/#/performer
   - Tab: Suara
   - Input teks Indonesia: "Halo, selamat datang di toko kami"
   - Klik: Generate

#### Long-term (Untuk Production)

1. **Fix PyTorch CUDA di Fish-Speech venv**
   
   **Option A: Manual pip install (bypass UV)**
   ```powershell
   cd external/fish-speech
   .venv\Scripts\activate
   pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu126
   ```

   **Option B: Edit pyproject.toml**
   ```toml
   [tool.uv.sources]
   torch = { index = "pytorch-cu126" }
   torchaudio = { index = "pytorch-cu126" }
   
   [[tool.uv.index]]
   name = "pytorch-cu126"
   url = "https://download.pytorch.org/whl/cu126"
   ```

2. **Restart Server dengan GPU**
   ```powershell
   # Stop current CPU server
   # Start with GPU
   cd external/fish-speech
   uv run python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path checkpoints/s2-pro --decoder-checkpoint-path checkpoints/s2-pro --device cuda:0
   ```

### 📊 Performance Expectations

| Mode | Inference Time | VRAM Usage | Notes |
|------|---------------|------------|-------|
| CPU | ~30-60 detik/kalimat | 0 MB | Sangat lambat, hanya untuk testing |
| GPU (4GB) | ~3-5 detik/kalimat | ~3.5 GB | Optimal untuk testing lokal |
| GPU (8GB+) | ~2-3 detik/kalimat | ~4-6 GB | Optimal untuk production |

### 🎯 Testing Checklist

- [ ] Fish-Speech server berhasil start di port 8080
- [ ] Health check `/v1/health` return 200 OK
- [ ] Dashboard detect Fish-Speech server (status: "Siap")
- [ ] Generate audio bahasa Indonesia berhasil
- [ ] Audio output terdengar natural (bukan robot)
- [ ] Emotion tags `[excited]`, `[whisper]` berfungsi
- [ ] Latency acceptable (<10 detik untuk CPU, <5 detik untuk GPU)

### 📝 Test Cases Indonesia

```python
# Basic
"Halo, selamat datang di toko kami."

# With emotion
"[excited] Wah, ada promo spesial hari ini!"

# Whisper
"[whisper] Psst, stok tinggal sedikit ya."

# Professional
"[professional broadcast tone] Selamat malam pemirsa, berikut produk unggulan kami."

# Mixed emotions
"[excited] Halo semuanya! [whisper] Hari ini ada kejutan spesial loh."
```

### 🐛 Known Issues

1. **PyTorch CUDA Installation in Fish-Speech venv**
   - UV tidak install versi CUDA dengan benar
   - Workaround: Manual pip install atau edit pyproject.toml

2. **Slow Model Loading on CPU**
   - S2-Pro model sangat besar (~10GB)
   - Loading di CPU bisa 5-10 menit
   - Solusi: Gunakan GPU mode

3. **VRAM Limitation (4GB)**
   - GTX 1650 hanya 4GB VRAM
   - Cukup untuk testing tapi tidak optimal
   - Production perlu GPU 8GB+

### 📞 Support Commands

```powershell
# Check if server is running
Get-Process python* | Where-Object {$_.Path -like "*fish-speech*"}

# Check port 8080
netstat -ano | findstr :8080

# View server logs (if running in background)
# Use Kiro's getProcessOutput tool with terminalId: 4

# Stop server
# Use Kiro's controlPwshProcess tool with action: stop, terminalId: 4

# Restart server
cd external/fish-speech
uv run python -m tools.api_server --listen 0.0.0.0:8080 --llama-checkpoint-path checkpoints/s2-pro --decoder-checkpoint-path checkpoints/s2-pro --device cpu
```

### 🔗 References

- Fish-Speech S2-Pro: https://github.com/fishaudio/fish-speech
- Model: https://huggingface.co/fishaudio/s2-pro
- Docs: https://speech.fish.audio/
- PyTorch CUDA: https://pytorch.org/get-started/locally/

---

**Last Updated**: 2026-03-15 23:28 WIB
**Updated By**: Kiro AI Assistant
