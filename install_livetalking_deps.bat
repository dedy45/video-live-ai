@echo off
REM ============================================================
REM Install LiveTalking Dependencies
REM ============================================================
REM This script installs all dependencies required by LiveTalking
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Install LiveTalking Dependencies
echo ============================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM Check if venv exists
if not exist ".venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: install_full_dependencies.bat first
    pause
    exit /b 1
)

REM Activate venv
call .venv\Scripts\activate.bat

echo Installing LiveTalking dependencies...
echo.

REM Check if LiveTalking requirements.txt exists
if exist "external\livetalking\requirements.txt" (
    echo [1/2] Installing from LiveTalking requirements.txt...
    uv pip install -r external\livetalking\requirements.txt
    if %errorlevel% neq 0 (
        echo [WARN] Some dependencies failed to install
        echo Continuing with manual installation...
    )
) else (
    echo [WARN] LiveTalking requirements.txt not found
    echo Make sure LiveTalking submodule is cloned:
    echo   git submodule update --init --recursive
)

echo.
echo [2/2] Installing critical missing dependencies...

REM Install Flask and related
echo Installing Flask ecosystem...
uv pip install flask flask-sockets flask-cors

REM Install transformers and AI models
echo Installing transformers...
uv pip install transformers==4.46.2

REM Install TTS
echo Installing TTS engines...
uv pip install edge-tts azure-cognitiveservices-speech

REM Install WebRTC and networking
echo Installing WebRTC and networking...
uv pip install aiortc aiohttp-cors websockets==12.0

REM Install additional tools
echo Installing additional tools...
uv pip install gradio-client omegaconf diffusers accelerate

REM Install face and audio processing
echo Installing face and audio processing...
uv pip install face-alignment python-speech-features numba

REM Install visualization
echo Installing visualization...
uv pip install matplotlib rich dearpygui tensorboardX

REM Install 3D processing
echo Installing 3D processing...
uv pip install trimesh PyMCubes

REM Install ML tools
echo Installing ML tools...
uv pip install torch-ema lpips==0.1.3 einops configargparse

REM Install data processing
echo Installing data processing...
uv pip install pandas scikit-learn tqdm packaging

echo.
echo ============================================================
echo   Verification
echo ============================================================
echo.

echo Checking critical dependencies...
.venv\Scripts\python.exe -c "import flask; print(f'✓ Flask: {flask.__version__}')"
.venv\Scripts\python.exe -c "import flask_sockets; print('✓ flask_sockets: installed')"
.venv\Scripts\python.exe -c "import transformers; print(f'✓ transformers: {transformers.__version__}')"
.venv\Scripts\python.exe -c "import edge_tts; print('✓ edge_tts: installed')"
.venv\Scripts\python.exe -c "import aiortc; print(f'✓ aiortc: {aiortc.__version__}')"

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.

echo LiveTalking dependencies installed successfully!
echo.
echo Next steps:
echo   1. Download models: download_models_guide.bat
echo   2. Run web interface: run_livetalking_web.bat
echo   3. Test: http://localhost:8010/webrtcapi.html
echo.

pause
