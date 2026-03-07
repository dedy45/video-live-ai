# Complete Setup Guide - LiveTalking Integration

## ✅ Current Status

**Good News:** Your setup is almost complete! The server runs successfully, you just need to download the model files.

### What's Working:
- ✅ Python 3.12 installed
- ✅ Virtual environment created
- ✅ PyTorch with CUDA installed
- ✅ All dependencies installed (flask, flask_sockets, transformers, etc.)
- ✅ LiveTalking submodule cloned
- ✅ Server starts successfully
- ✅ Path handling fixed (handles `!` in folder name)

### What's Missing:
- ❌ Model files (wav2lip.pth)
- ❌ Avatar data (optional for testing)

## 🎯 Quick Fix - Download Models

### Option 1: Automated Setup (Recommended)

```bash
setup_wav2lip_model.bat
```

This script will:
1. Check if models exist in `external/livetalking/models/`
2. Copy them to `models/` if found
3. Guide you to download if not found
4. Setup avatar data

### Option 2: Manual Download

**Step 1: Download Model**

Download from LiveTalking official sources:
- **Quark Cloud**: https://pan.quark.cn/s/83a750323ef0
- **Google Drive**: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ

Files to download:
- `wav2lip256.pth` (~150 MB)

**Step 2: Place Model**

```
videoliveai/
└── models/
    └── wav2lip.pth  (rename from wav2lip256.pth)
```

**Step 3: Download Avatar (Optional)**

Download `wav2lip256_avatar1.tar.gz` and extract to:

```
videoliveai/
└── data/
    └── avatars/
        └── wav2lip256_avatar1/
```

## 🚀 Run Server

After downloading models:

```bash
run_livetalking_web.bat
```

Server will start on: http://localhost:8010

Web interfaces:
- WebRTC API: http://localhost:8010/webrtcapi.html
- RTC Push: http://localhost:8010/rtcpushapi.html
- Chat: http://localhost:8010/chat.html
- Dashboard: http://localhost:8010/dashboard.html

## 📋 Complete File Structure

```
videoliveai/
├── .venv/                          # Virtual environment ✅
│   └── Scripts/
│       └── python.exe              # Python 3.12 ✅
├── models/                         # Model files
│   ├── wav2lip.pth                 # ❌ NEED TO DOWNLOAD
│   ├── musetalk/                   # Optional
│   ├── er-nerf/                    # Optional
│   └── gfpgan/                     # Optional
├── data/
│   └── avatars/
│       └── wav2lip256_avatar1/     # ❌ OPTIONAL
├── external/
│   └── livetalking/                # ✅ Cloned
│       ├── app.py                  # ✅ Main server
│       ├── models/                 # May contain models
│       └── data/                   # May contain avatars
├── run_livetalking_web.bat         # ✅ Fixed
├── setup_wav2lip_model.bat         # ✅ New helper script
└── ...
```

## 🔍 Troubleshooting

### Error: FileNotFoundError: './models/wav2lip.pth'

**Cause:** Model file not downloaded

**Solution:**
```bash
# Run setup script
setup_wav2lip_model.bat

# Or download manually and place in models/
```

### Server starts but no video

**Cause:** Avatar data missing (optional)

**Solution:**
- Download `wav2lip256_avatar1.tar.gz`
- Extract to `data/avatars/`
- Or use custom video/image

### Path issues with `!` character

**Status:** ✅ FIXED

The script now uses `setlocal disabledelayedexpansion` to properly handle the `!` character in the folder name `!fast-track-income`.

## 📊 Model Information

### Wav2Lip Model

| Property | Value |
|----------|-------|
| File | wav2lip.pth |
| Size | ~150 MB |
| Purpose | Lip-sync animation |
| Required | Yes |
| GPU | RTX 3060+ recommended |

### Avatar Data

| Property | Value |
|----------|-------|
| File | wav2lip256_avatar1.tar.gz |
| Size | ~500 MB |
| Purpose | Reference video/audio |
| Required | No (can use custom) |
| Format | Video + audio files |

## 🎯 Next Steps

1. ✅ **Download Model**
   ```bash
   setup_wav2lip_model.bat
   ```

2. ✅ **Run Server**
   ```bash
   run_livetalking_web.bat
   ```

3. ✅ **Test Web Interface**
   - Open: http://localhost:8010/webrtcapi.html
   - Click "Start"
   - Enter text to test

4. ✅ **Download Avatar (Optional)**
   - For full functionality
   - Or use custom video/image

## 📚 All Available Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `install_full_dependencies.bat` | Install all dependencies | First time setup |
| `install_livetalking_deps.bat` | Install LiveTalking deps | If flask_sockets missing |
| `setup_wav2lip_model.bat` | Setup models | After dependencies installed |
| `run_livetalking_web.bat` | Run server | After models downloaded |
| `test_livetalking_deps.bat` | Test dependencies | Verify installation |
| `fix_python_version.bat` | Fix Python 3.13 issue | If Python version error |
| `quick_fix_flask.bat` | Quick fix Flask deps | If flask_sockets missing |

## ✨ Summary

**You're 95% done!** Just need to:

1. Download `wav2lip.pth` (~150 MB)
2. Place in `models/` folder
3. Run `run_livetalking_web.bat`

The server will start and you can test the web interface!

---

**Need help?** Run `setup_wav2lip_model.bat` for guided setup! 🚀
