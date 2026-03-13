# LiveTalking Browser Preview Runbook

> Last verified on Windows local lab: 2026-03-14
> Control plane: `http://127.0.0.1:8001/dashboard`
> Vendor preview port: `http://127.0.0.1:8010`

## Goal

Make the LiveTalking browser preview usable as a source for TikTok LIVE Studio capture:

- `http://localhost:8010/webrtcapi.html`
- `http://localhost:8010/rtcpushapi.html`

This runbook is now grounded in the implementation that is actually verified in this repo.

## What Is Verified

- The dashboard control plane can start LiveTalking from `/api/engine/livetalking/start`.
- LiveTalking can run from a dedicated sidecar interpreter instead of the main app `.venv`.
- `webrtcapi.html` delivers direct browser preview with live `audio + video` tracks.
- `rtcpushapi.html` is reachable and now falls back to direct WebRTC preview when local relay `:1985` is not available.
- The dashboard `Avatar & Suara -> Preview` tab embeds the vendor preview successfully.
- The dashboard `Avatar & Suara -> Suara` tab now works as a two-mode Voice Lab:
  - `Standalone Fish TTS` generates audio directly from a web prompt.
  - `Attach ke Avatar` syncs the preview `sessionid` from `webrtcapi.html` back into the dashboard and sends audio to the active avatar session.

## What Is Not Verified

- Real TikTok ingest automation from the dashboard.
- Local SRS/WHIP/WHEP relay on port `1985`.
- Headless Ubuntu OBS automation end-to-end.
- MuseTalk attach mode end-to-end on the dedicated sidecar env. The currently verified attach path is `wav2lip`.

For local Windows testing, the correct target is:

`videoliveai -> dashboard -> browser preview -> TikTok LIVE Studio manual capture`

## Recommended Local Mode

Use `wav2lip` for preview bring-up because startup is materially faster and lighter than `musetalk`.

Recommended runtime settings:

```env
LIVETALKING_PYTHON_EXE=.venv-livetalking\Scripts\python.exe
LIVETALKING_MODEL=wav2lip
LIVETALKING_AVATAR_ID=wav2lip256_avatar1
LIVETALKING_STARTUP_TIMEOUT_SEC=60
```

## One-Time Setup

### 1. Create the dedicated sidecar env

Use Python `3.10`.

Windows example:

```powershell
C:\Users\dedy\miniconda3\envs\qntdev\python.exe -m venv .venv-livetalking
.\.venv-livetalking\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
.\.venv-livetalking\Scripts\python.exe -m pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124
.\.venv-livetalking\Scripts\python.exe -m pip install -r .\external\livetalking\requirements.txt
```

Ubuntu equivalent:

```bash
python3.10 -m venv .venv-livetalking
. .venv-livetalking/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124
python -m pip install -r external/livetalking/requirements.txt
```

### 2. Ensure vendor assets exist

Required minimum for the verified fast-preview path:

- `external/livetalking/models/wav2lip.pth`
- `external/livetalking/data/avatars/wav2lip256_avatar1/`

## Start Flow

### 1. Start the control plane

```powershell
$env:MOCK_MODE='false'
$env:DASHBOARD_HOST='127.0.0.1'
$env:DASHBOARD_PORT='8001'
$env:LIVETALKING_PYTHON_EXE=(Resolve-Path .\.venv-livetalking\Scripts\python.exe)
$env:LIVETALKING_MODEL='wav2lip'
$env:LIVETALKING_AVATAR_ID='wav2lip256_avatar1'
$env:LIVETALKING_STARTUP_TIMEOUT_SEC='60'
.\.venv\Scripts\python.exe -m src.main
```

### 2. Start LiveTalking from the dashboard or API

API:

```powershell
Invoke-WebRequest -Method Post http://127.0.0.1:8001/api/engine/livetalking/start -UseBasicParsing
```

Expected behavior:

- manager waits until port `8010` is reachable
- response reports `state=running`
- `http://127.0.0.1:8001/api/engine/livetalking/debug-targets` returns `reachable=true` for `webrtcapi` and `rtcpushapi`

## Preview URLs

### Direct WebRTC

`http://localhost:8010/webrtcapi.html`

Use this when you want the most direct preview path.

Behavior verified:

- click `Start`
- browser receives live `audio + video`
- page returns a non-zero `sessionid`

### RTC Push Compatibility Page

`http://localhost:8010/rtcpushapi.html`

Behavior in the current local lab:

- page first checks local relay `http://localhost:1985/rtc/v1/whep/?app=live&stream=livestream`
- if relay is absent, page automatically falls back to direct WebRTC preview
- status banner changes to `fallback`
- browser still receives live `audio + video`

This means the page is usable locally even without SRS.

## Dashboard Voice Lab Validation

The current day-1 operator workflow is:

1. Open `http://127.0.0.1:8001/dashboard/performer.html`.
2. In `Preview`, open the embedded `webrtcapi.html` vendor page and click `Start`.
3. Wait for the operator receipt `Session preview tersinkron ke Voice Lab`.
4. Switch to `Suara`.
5. For raw TTS testing, keep mode `Standalone Fish TTS` and click `Generate Audio`.
6. For avatar attach testing, switch to `Attach ke Avatar`, confirm `Attach session = Terhubung`, then click `Generate & Attach`.

Expected results:

- `Standalone Fish TTS` stores a generation entry with `attached_to_avatar=false`.
- `Attach ke Avatar` stores a generation entry with `attached_to_avatar=true` and a non-empty `avatar_session_id`.
- The attach flow is driven from the dashboard control plane; the vendor page only supplies the live preview session id.

## TikTok LIVE Studio Usage

For local Windows testing, use browser capture rather than fighting RTMP key access.

Recommended operator flow:

1. Start LiveTalking from the dashboard.
2. Open `webrtcapi.html` or `rtcpushapi.html`.
3. Click `Start`.
4. Confirm the preview has active audio and video.
5. In TikTok LIVE Studio, add:
   - `Window Capture` for the browser preview
   - matching desktop/app audio capture for the preview window
6. Go live from TikTok LIVE Studio manually.

## Notes About `rtcpush`

`rtcpushapi.html` being usable locally does **not** mean a real WHIP/WHEP relay exists.

Current truth:

- local Windows lab: `rtcpushapi.html` works through fallback
- real rtcpush relay: still requires an actual service on `:1985`

If you later want real relay semantics, deploy SRS or another compatible WHIP/WHEP server and keep the same page.

## Operator Checks

Useful endpoints:

```powershell
Invoke-WebRequest http://127.0.0.1:8001/api/engine/livetalking/config -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8001/api/engine/livetalking/status -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8001/api/engine/livetalking/debug-targets -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8010/webrtcapi.html -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:8010/rtcpushapi.html -UseBasicParsing
```

## Known Constraints

- The main app `.venv` in this repo can carry `PYTHONHOME` from the `uv` runtime. The manager now strips that before spawning the sidecar.
- `wav2lip` is the verified fast preview path. `musetalk` remains heavier and slower to warm up.
- `webrtcapi.html` now includes a local preview-session bridge and a cache-busted `client.js` reference so the dashboard still receives `sessionid` updates even if the browser had an older vendor script cached.
- Voice sidecar latency and TikTok ingest automation are separate tracks.
