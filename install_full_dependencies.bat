@echo off
REM ============================================================
REM Full Dependencies Installation with UV
REM ============================================================
REM This script installs ALL dependencies for LiveTalking
REM including PyTorch with CUDA support
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   Full Dependencies Installation
echo ============================================================
echo.
echo This will install:
echo   - PyTorch 2.5.0 with CUDA 12.4
echo   - TorchVision 0.20.0
echo   - TorchAudio 2.5.0
echo   - OpenCV
echo   - SciPy, NumPy, Librosa
echo   - scikit-image, soundfile
echo   - aiortc (WebRTC)
echo   - All LiveTalking dependencies
echo.
echo Estimated download: ~5-8 GB
echo Estimated time: 10-20 minutes
echo.

set /p "CONTINUE=Continue with full installation? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo Installation cancelled.
    pause
    exit /b 0
)

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM ============================================================
REM Step 1: Check UV
REM ============================================================
echo.
echo [1/7] Checking UV installation...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] UV not found! Please install UV first:
    echo   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)
echo [OK] UV is installed
echo.

REM ============================================================
REM Step 2: Check Python Version & Create Virtual Environment
REM ============================================================
echo [2/7] Checking Python version and setting up virtual environment...

REM Check if .venv exists and get its Python version
if exist ".venv\Scripts\python.exe" (
    echo Checking existing virtual environment...
    for /f "tokens=*" %%i in ('.venv\Scripts\python.exe --version 2^>^&1') do set VENV_PYTHON_VERSION=%%i
    echo Current venv: !VENV_PYTHON_VERSION!
    
    REM Check if it's Python 3.13 (not supported by PyTorch 2.5.0)
    echo !VENV_PYTHON_VERSION! | findstr /C:"3.13" >nul
    if !errorlevel! equ 0 (
        echo.
        echo [WARN] Python 3.13 detected in existing .venv
        echo PyTorch 2.5.0 only supports Python 3.9-3.12
        echo.
        set /p "RECREATE=Recreate .venv with Python 3.12? (y/n): "
        if /i "!RECREATE!"=="y" (
            echo Removing old .venv...
            rmdir /s /q .venv
            echo Creating new .venv with Python 3.12...
            uv venv --python 3.12
            if !errorlevel! neq 0 (
                echo [ERROR] Failed to create virtual environment with Python 3.12
                echo.
                echo Trying Python 3.11...
                uv venv --python 3.11
                if !errorlevel! neq 0 (
                    echo [ERROR] Failed to create virtual environment with Python 3.11
                    echo.
                    echo Trying Python 3.10...
                    uv venv --python 3.10
                    if !errorlevel! neq 0 (
                        echo [ERROR] Failed to create virtual environment
                        pause
                        exit /b 1
                    )
                )
            )
            echo [OK] Virtual environment recreated
        ) else (
            echo [ERROR] Cannot proceed with Python 3.13
            echo Please recreate .venv with Python 3.12 or lower
            pause
            exit /b 1
        )
    ) else (
        echo [OK] Virtual environment exists with compatible Python version
    )
) else (
    echo Creating new virtual environment with Python 3.12...
    uv venv --python 3.12
    if %errorlevel% neq 0 (
        echo [WARN] Python 3.12 not found, trying 3.11...
        uv venv --python 3.11
        if %errorlevel% neq 0 (
            echo [WARN] Python 3.11 not found, trying 3.10...
            uv venv --python 3.10
            if %errorlevel% neq 0 (
                echo [ERROR] Failed to create virtual environment
                echo Please install Python 3.10, 3.11, or 3.12
                pause
                exit /b 1
            )
        )
    )
    echo [OK] Virtual environment created
)
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM ============================================================
REM Step 3: Detect CUDA
REM ============================================================
echo [3/7] Detecting CUDA...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=name --format=csv,noheader') do set GPU_NAME=%%i
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=driver_version --format=csv,noheader') do set DRIVER_VERSION=%%i
    echo GPU: !GPU_NAME!
    echo Driver: !DRIVER_VERSION!
    echo.
    echo Will install PyTorch with CUDA 12.4 support
    set CUDA_VERSION=cu124
    set TORCH_INDEX=https://download.pytorch.org/whl/cu124
) else (
    echo [WARN] No NVIDIA GPU detected
    echo Will install CPU-only PyTorch
    set CUDA_VERSION=cpu
    set TORCH_INDEX=https://download.pytorch.org/whl/cpu
)
echo.

REM ============================================================
REM Step 4: Install PyTorch
REM ============================================================
echo [4/7] Installing PyTorch with CUDA support...
echo This is the largest download (~2-3 GB)...
echo.

REM Check Python version in venv
for /f "tokens=2 delims= " %%i in ('.venv\Scripts\python.exe --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version in venv: !PYTHON_VERSION!

REM Check if Python 3.13
echo !PYTHON_VERSION! | findstr /C:"3.13" >nul
if !errorlevel! equ 0 (
    echo.
    echo [ERROR] Python 3.13 is not supported by PyTorch 2.5.0
    echo PyTorch 2.5.0 supports: Python 3.9, 3.10, 3.11, 3.12
    echo.
    echo Please recreate .venv with Python 3.12:
    echo   rmdir /s /q .venv
    echo   uv venv --python 3.12
    echo.
    pause
    exit /b 1
)

echo Installing PyTorch 2.5.0...
uv pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url !TORCH_INDEX!
if %errorlevel% neq 0 (
    echo [WARN] Failed to install PyTorch 2.5.0
    echo.
    echo Trying latest compatible version...
    uv pip install torch torchvision torchaudio --index-url !TORCH_INDEX!
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyTorch
        echo.
        echo Possible causes:
        echo   1. Python version incompatible (need 3.9-3.12)
        echo   2. Network connection issue
        echo   3. CUDA version mismatch
        echo.
        echo Manual installation:
        echo   call .venv\Scripts\activate.bat
        echo   uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
        echo.
        pause
        exit /b 1
    )
)

echo [OK] PyTorch installed
echo.

REM Verify PyTorch
echo Verifying PyTorch installation...
.venv\Scripts\python.exe -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA Available: {torch.cuda.is_available()}')"
if %errorlevel% neq 0 (
    echo [ERROR] PyTorch verification failed
    echo Trying to diagnose...
    echo.
    echo Checking Python path:
    .venv\Scripts\python.exe -c "import sys; print(sys.executable)"
    echo.
    echo Checking installed packages:
    uv pip list | findstr torch
    echo.
    pause
    exit /b 1
)
echo [OK] PyTorch verified
echo.

REM ============================================================
REM Step 5: Install Core Dependencies
REM ============================================================
echo [5/7] Installing core dependencies...
echo.

echo Installing OpenCV...
uv pip install opencv-python>=4.9.0
echo.

echo Installing NumPy and SciPy...
uv pip install numpy>=1.26.0 scipy>=1.12.0
echo.

echo Installing scikit-image...
uv pip install scikit-image>=0.22.0
echo.

echo Installing audio libraries...
uv pip install librosa>=0.10.0 soundfile>=0.12.0 resampy>=0.4.0
echo.

echo Installing image processing...
uv pip install Pillow>=10.2.0 imageio>=2.33.0 imageio-ffmpeg>=0.4.9
echo.

echo [OK] Core dependencies installed
echo.

REM ============================================================
REM Step 6: Install WebRTC and Streaming
REM ============================================================
echo [6/7] Installing WebRTC and streaming dependencies...
echo.

echo Installing aiortc (WebRTC)...
uv pip install aiortc>=1.6.0 av>=11.0.0
if %errorlevel% neq 0 (
    echo [WARN] aiortc installation failed
    echo WebRTC features may not work
    echo This is okay if you only use RTMP streaming
)
echo.

echo Installing FFmpeg wrapper...
uv pip install ffmpeg-python>=0.2.0
echo.

echo [OK] Streaming dependencies installed
echo.

REM ============================================================
REM Step 7: Install Project Dependencies
REM ============================================================
echo [7/7] Installing project dependencies...
echo.

echo Installing main project dependencies...
uv pip install -e ".[livetalking,dev]"
if %errorlevel% neq 0 (
    echo [WARN] Some project dependencies failed
    echo Trying without dev dependencies...
    uv pip install -e ".[livetalking]"
)

echo.
echo Installing LiveTalking specific dependencies...
if exist "external\livetalking\requirements.txt" (
    echo Found LiveTalking requirements.txt
    uv pip install -r external\livetalking\requirements.txt
    if %errorlevel% neq 0 (
        echo [WARN] Some LiveTalking dependencies failed to install
        echo This is okay, core dependencies are installed
    )
) else (
    echo [WARN] LiveTalking requirements.txt not found
    echo Installing common LiveTalking dependencies manually...
    uv pip install flask flask-sockets transformers edge-tts aiohttp-cors gradio-client azure-cognitiveservices-speech
)

echo [OK] Project dependencies installed
echo.

REM ============================================================
REM Verification
REM ============================================================
echo.
echo ============================================================
echo   Verifying Installation
echo ============================================================
echo.

echo Checking all dependencies...
echo.

.venv\Scripts\python.exe -c "import torch; print(f'✓ PyTorch: {torch.__version__}')"
.venv\Scripts\python.exe -c "import torch; print(f'✓ CUDA: {torch.cuda.is_available()}')"
.venv\Scripts\python.exe -c "import torch; cuda_available = torch.cuda.is_available(); print(f'✓ GPU: {torch.cuda.get_device_name(0) if cuda_available else \"N/A\"}')"
.venv\Scripts\python.exe -c "import cv2; print(f'✓ OpenCV: {cv2.__version__}')"
.venv\Scripts\python.exe -c "import numpy; print(f'✓ NumPy: {numpy.__version__}')"
.venv\Scripts\python.exe -c "import scipy; print(f'✓ SciPy: {scipy.__version__}')"
.venv\Scripts\python.exe -c "import librosa; print(f'✓ Librosa: {librosa.__version__}')"
.venv\Scripts\python.exe -c "import skimage; print(f'✓ scikit-image: {skimage.__version__}')"
.venv\Scripts\python.exe -c "import soundfile; print(f'✓ soundfile: {soundfile.__version__}')"
.venv\Scripts\python.exe -c "import PIL; print(f'✓ Pillow: {PIL.__version__}')"

echo.
echo Checking optional dependencies...
.venv\Scripts\python.exe -c "import aiortc; print(f'✓ aiortc: {aiortc.__version__}')" 2>nul || echo [WARN] aiortc not installed
.venv\Scripts\python.exe -c "import av; print(f'✓ av: {av.__version__}')" 2>nul || echo [WARN] av not installed

echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.

echo All dependencies have been installed successfully!
echo.
echo Installed packages:
uv pip list | findstr /i "torch opencv numpy scipy librosa"
echo.

echo Next steps:
echo   1. Download models: download_models_guide.bat
echo   2. Test installation: run_livetalking_web.bat
echo   3. Run production: uv run python -m src.main
echo.

pause
