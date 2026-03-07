# LiveTalking Runtime Contract

> **Status**: Active
> **Date**: 2026-03-07

## Engine Entry Point

| Property | Value |
|----------|-------|
| **Startup file** | `external/livetalking/app.py` (NOT `server.py`) |
| **Framework** | Flask + aiohttp + aiortc |
| **Default port** | `8010` (`--listenport 8010`) |
| **Process type** | Standalone subprocess |

## Supported Transport Modes

| Transport | Flag | Use Case |
|-----------|------|----------|
| `webrtc` | `--transport webrtc` | Browser preview, low-latency |
| `rtmp` | `--transport rtmp` | TikTok/Shopee streaming |
| `rtcpush` | `--transport rtcpush` | Server-side RTC push |

## Supported Models

| Model | Flag | Avatar ID Example | VRAM Required |
|-------|------|-------------------|---------------|
| `wav2lip` | `--model wav2lip` | `wav2lip256_avatar1` | ~4GB |
| `musetalk` | `--model musetalk` | `musetalk_avatar1` | ~8GB (RTX 3080 Ti+) |
| `ultralight` | `--model ultralight` | varies | ~2GB |

## Required Model Paths (Option A — inside vendor dir)

| Model | Path |
|-------|------|
| Wav2Lip weights | `external/livetalking/models/wav2lip.pth` |
| MuseTalk weights | `external/livetalking/models/musetalk/*.pth` |
| GFPGAN weights | `external/livetalking/models/gfpgan/` |

## Required Avatar Paths

| Avatar | Path |
|--------|------|
| Wav2Lip default | `external/livetalking/data/avatars/wav2lip256_avatar1/` |
| MuseTalk default | `external/livetalking/data/avatars/musetalk_avatar1/` |
| Coordinates file | `external/livetalking/data/avatars/<id>/coords.pkl` |

## Launch Command Templates

### WebRTC + Wav2Lip (basic)
```bash
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1 --listenport 8010
```

### WebRTC + MuseTalk (better quality)
```bash
python app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar1 --listenport 8010
```

### RTMP + Wav2Lip (streaming to TikTok)
```bash
python app.py --transport rtmp --push_url "rtmp://push.tiktokcdn.com/live/KEY" --model wav2lip --avatar_id wav2lip256_avatar1
```

## Vendor Debug Pages

| URL | Purpose |
|-----|---------|
| `http://localhost:8010/webrtcapi.html` | WebRTC test interface |
| `http://localhost:8010/rtcpushapi.html` | RTC push test |
| `http://localhost:8010/dashboard.html` | Vendor dashboard (debug only) |
| `http://localhost:8010/echoapi.html` | Echo test |
| `http://localhost:8010/chat.html` | Chat test |

## Key Dependencies (LiveTalking side)

- torch, torchvision, torchaudio (CUDA)
- flask, flask_sockets
- aiohttp, aiohttp_cors
- aiortc, av
- soundfile, resampy, edge_tts
- opencv-python-headless
- librosa, ffmpeg-python
- einops, diffusers, accelerate, transformers, omegaconf
