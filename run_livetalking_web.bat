@echo off
REM ============================================================
REM Run LiveTalking Web Interface
REM ============================================================
setlocal disabledelayedexpansion

echo.
echo ============================================================
echo   LiveTalking Web Interface
echo ============================================================
echo.

REM Get script directory
pushd "%~dp0"
set "PROJECT_ROOT=%CD%\"
popd

echo Project root: %PROJECT_ROOT%
echo.

REM Check if LiveTalking exists
if not exist "%PROJECT_ROOT%external\livetalking\app.py" (
    echo [ERROR] LiveTalking not found!
    echo.
    echo Please run setup first:
    echo   git submodule update --init --recursive
    echo.
    pause
    exit /b 1
)

REM Change to LiveTalking directory
cd /d "%PROJECT_ROOT%external\livetalking"

REM Check if model exists
if not exist "models\wav2lip.pth" (
    echo [ERROR] Model file not found: models\wav2lip.pth
    echo.
    echo Run setup script first:
    echo   cd external\livetalking
    echo   python setup_models.py
    echo.
    echo Or download manually from:
    echo   https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
    echo.
    pause
    exit /b 1
)

REM Check if avatar data exists
if not exist "data\avatars\wav2lip256_avatar1\coords.pkl" (
    echo [ERROR] Avatar data not found: data\avatars\wav2lip256_avatar1\
    echo.
    echo Run setup script first:
    echo   cd external\livetalking
    echo   python setup_models.py
    echo.
    pause
    exit /b 1
)

REM Quick dependency check
python -c "import torch, soundfile, edge_tts, aiortc, av" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Missing Python dependencies!
    echo.
    echo Install required packages:
    echo   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    echo   pip install soundfile resampy edge_tts opencv-python-headless aiohttp_cors aiortc av flask_sockets librosa ffmpeg-python einops diffusers accelerate transformers omegaconf
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Starting LiveTalking Server
echo ============================================================
echo.
echo Server will run on: http://localhost:8010
echo.
echo Available web interfaces:
echo   - WebRTC API:  http://localhost:8010/webrtcapi.html
echo   - Dashboard:   http://localhost:8010/dashboard.html
echo   - Echo API:    http://localhost:8010/echoapi.html
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

REM Run LiveTalking server
python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1 --listenport 8010

REM Alternative commands (uncomment to use):
REM python app.py --transport webrtc --model musetalk --avatar_id avator_1 --listenport 8010
REM python app.py --transport rtmp --push_url "rtmp://push.tiktokcdn.com/live/YOUR_KEY" --model wav2lip --avatar_id wav2lip256_avatar1

echo.
echo Server stopped.
cd /d "%PROJECT_ROOT%"
pause
