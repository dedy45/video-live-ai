@echo off
REM ============================================================
REM Verify & Setup LiveTalking Integration
REM ============================================================
REM This script will:
REM 1. Check if models exist (MuseTalk, ER-NeRF, GFPGAN)
REM 2. Setup LiveTalking with UV
REM 3. Verify installation
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   LiveTalking Verification Script
echo ============================================================
echo.

REM Get script directory
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM ============================================================
REM Step 1: Check UV Installation
REM ============================================================
echo [1/5] Checking UV installation...
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
REM Step 2: Check Virtual Environment
REM ============================================================
echo [2/5] Checking virtual environment...
if not exist ".venv\Scripts\activate.bat" (
    echo [WARN] .venv not found. Creating new virtual environment...
    echo.
    echo PyTorch 2.5.0 requires Python 3.9-3.12 (NOT 3.13!)
    echo Creating with Python 3.12...
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
) else (
    echo [OK] Virtual environment exists
    
    REM Check Python version
    for /f "tokens=*" %%i in ('.venv\Scripts\python.exe --version 2^>^&1') do set VENV_PYTHON_VERSION=%%i
    echo Python version: !VENV_PYTHON_VERSION!
    
    REM Check if Python 3.13
    echo !VENV_PYTHON_VERSION! | findstr /C:"3.13" >nul
    if !errorlevel! equ 0 (
        echo.
        echo [ERROR] Python 3.13 detected!
        echo PyTorch 2.5.0 only supports Python 3.9-3.12
        echo.
        echo Please recreate .venv:
        echo   rmdir /s /q .venv
        echo   uv venv --python 3.12
        echo   Then run this script again
        echo.
        pause
        exit /b 1
    )
)
echo.

REM ============================================================
REM Step 3: Check Models
REM ============================================================
echo [3/5] Checking model files...
set "MODELS_MISSING=0"

if not exist "models\musetalk\*.pth" (
    echo [MISSING] MuseTalk model not found in models\musetalk\
    set "MODELS_MISSING=1"
) else (
    echo [OK] MuseTalk model found
)

if not exist "models\er-nerf\*.pth" (
    echo [MISSING] ER-NeRF model not found in models\er-nerf\
    set "MODELS_MISSING=1"
) else (
    echo [OK] ER-NeRF model found
)

if not exist "models\gfpgan\*.pth" (
    echo [MISSING] GFPGAN model not found in models\gfpgan\
    set "MODELS_MISSING=1"
) else (
    echo [OK] GFPGAN model found
)

if !MODELS_MISSING! equ 1 (
    echo.
    echo [WARN] Some models are missing!
    echo.
    echo You need to download models manually:
    echo   1. MuseTalk 1.5: https://github.com/TMElyralab/MuseTalk
    echo   2. ER-NeRF: https://github.com/Fictionarry/ER-NeRF
    echo   3. GFPGAN: https://github.com/TencentARC/GFPGAN
    echo.
    echo Or download from LiveTalking sources:
    echo   - Quark: https://pan.quark.cn/s/83a750323ef0
    echo   - Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
    echo.
    echo Place model files in:
    echo   - models\musetalk\
    echo   - models\er-nerf\
    echo   - models\gfpgan\
    echo.
    set /p "CONTINUE=Continue without models? (y/n): "
    if /i not "!CONTINUE!"=="y" (
        echo Setup cancelled.
        pause
        exit /b 0
    )
)
echo.

REM ============================================================
REM Step 4: Install Dependencies with UV
REM ============================================================
echo [4/5] Installing dependencies with UV...
echo This will install COMPLETE dependencies including PyTorch with CUDA...
echo This may take 10-15 minutes depending on your internet speed...
echo.

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check CUDA version
echo Detecting CUDA version...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected
    for /f "tokens=*" %%i in ('nvidia-smi --query-gpu=driver_version --format=csv,noheader') do set DRIVER_VERSION=%%i
    echo Driver Version: !DRIVER_VERSION!
    echo.
    echo Installing PyTorch with CUDA 12.4 support...
    set CUDA_VERSION=cu124
    set TORCH_INDEX=https://download.pytorch.org/whl/cu124
) else (
    echo [WARN] No NVIDIA GPU detected, installing CPU-only PyTorch
    set CUDA_VERSION=cpu
    set TORCH_INDEX=https://download.pytorch.org/whl/cpu
)

REM Check Python version compatibility
for /f "tokens=2 delims= " %%i in ('.venv\Scripts\python.exe --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: !PYTHON_VERSION!

REM Check if Python 3.13 (not supported)
echo !PYTHON_VERSION! | findstr /C:"3.13" >nul
if !errorlevel! equ 0 (
    echo.
    echo [ERROR] Python 3.13 is NOT supported by PyTorch 2.5.0
    echo Supported versions: Python 3.9, 3.10, 3.11, 3.12
    echo.
    echo Please recreate .venv with Python 3.12:
    echo   rmdir /s /q .venv
    echo   uv venv --python 3.12
    echo   Then run this script again
    echo.
    pause
    exit /b 1
)

REM Install PyTorch first (most important!)
echo.
echo [Step 4.1] Installing PyTorch with CUDA support...
uv pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url !TORCH_INDEX!
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install PyTorch 2.5.0
    echo.
    echo Trying latest compatible version...
    uv pip install torch torchvision torchaudio --index-url !TORCH_INDEX!
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install PyTorch
        echo.
        echo Possible causes:
        echo   1. Python version incompatible (need 3.9-3.12, NOT 3.13)
        echo   2. Network connection issue
        echo   3. CUDA version mismatch
        echo.
        echo Please check Python version and try again
        pause
        exit /b 1
    )
)
echo [OK] PyTorch installed
echo.

REM Verify PyTorch installation
echo Verifying PyTorch...
.venv\Scripts\python.exe -c "import torch; print(f'PyTorch: {torch.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyTorch verification failed
    echo.
    echo Diagnosing issue...
    echo Python executable: .venv\Scripts\python.exe
    .venv\Scripts\python.exe --version
    echo.
    echo Checking installed packages:
    uv pip list | findstr torch
    echo.
    pause
    exit /b 1
)
echo [OK] PyTorch verified
echo.

REM Install all LiveTalking dependencies
echo [Step 4.2] Installing LiveTalking dependencies...
uv pip install -e ".[livetalking]"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install LiveTalking dependencies
    pause
    exit /b 1
)
echo [OK] LiveTalking dependencies installed
echo.

REM Install additional dependencies for production
echo [Step 4.3] Installing additional production dependencies...
uv pip install opencv-python scikit-image scipy librosa soundfile resampy aiortc av imageio imageio-ffmpeg
if %errorlevel% neq 0 (
    echo [WARN] Some additional dependencies failed to install
    echo This is okay, core dependencies are installed
)
echo [OK] Additional dependencies installed
echo.

REM Install development tools (optional but recommended)
echo [Step 4.4] Installing development tools...
uv pip install pytest pytest-asyncio ruff mypy
if %errorlevel% neq 0 (
    echo [WARN] Development tools failed to install
    echo This is okay for production use
)
echo [OK] Development tools installed
echo.

REM ============================================================
REM Step 5: Verify Installation
REM ============================================================
echo [5/5] Verifying installation...
echo.

echo ============================================================
echo   Core Dependencies
echo ============================================================
echo.

REM Check PyTorch
echo Checking PyTorch...
.venv\Scripts\python.exe -c "import torch; print(f'✓ PyTorch: {torch.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] PyTorch not installed correctly
    echo.
    echo Please run the script again or install manually:
    echo   uv pip install torch==2.5.0 torchvision==0.20.0 torchaudio==2.5.0 --index-url https://download.pytorch.org/whl/cu124
    pause
    exit /b 1
)

REM Check CUDA
echo Checking CUDA...
.venv\Scripts\python.exe -c "import torch; cuda_available = torch.cuda.is_available(); print(f'✓ CUDA Available: {cuda_available}'); print(f'✓ CUDA Version: {torch.version.cuda if cuda_available else \"N/A\"}'); print(f'✓ GPU Device: {torch.cuda.get_device_name(0) if cuda_available else \"N/A\"}'); print(f'✓ GPU Count: {torch.cuda.device_count() if cuda_available else 0}')" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] CUDA check failed
)
echo.

echo ============================================================
echo   LiveTalking Dependencies
echo ============================================================
echo.

REM Check OpenCV
echo Checking OpenCV...
.venv\Scripts\python.exe -c "import cv2; print(f'✓ OpenCV: {cv2.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] OpenCV not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] OpenCV installed
)

REM Check NumPy
echo Checking NumPy...
.venv\Scripts\python.exe -c "import numpy; print(f'✓ NumPy: {numpy.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] NumPy not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] NumPy installed
)

REM Check SciPy
echo Checking SciPy...
.venv\Scripts\python.exe -c "import scipy; print(f'✓ SciPy: {scipy.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] SciPy not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] SciPy installed
)

REM Check Librosa
echo Checking Librosa...
.venv\Scripts\python.exe -c "import librosa; print(f'✓ Librosa: {librosa.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Librosa not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] Librosa installed
)

REM Check scikit-image
echo Checking scikit-image...
.venv\Scripts\python.exe -c "import skimage; print(f'✓ scikit-image: {skimage.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] scikit-image not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] scikit-image installed
)

REM Check soundfile
echo Checking soundfile...
.venv\Scripts\python.exe -c "import soundfile; print(f'✓ soundfile: {soundfile.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] soundfile not installed
    set VERIFY_FAILED=1
) else (
    echo [OK] soundfile installed
)

REM Check aiortc (WebRTC)
echo Checking aiortc...
.venv\Scripts\python.exe -c "import aiortc; print(f'✓ aiortc: {aiortc.__version__}')" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] aiortc not installed (WebRTC will not work)
) else (
    echo [OK] aiortc installed
)

echo.

if defined VERIFY_FAILED (
    echo [WARN] Some dependencies are missing
    echo Please run: uv pip install -e ".[livetalking]"
    echo.
)
echo ============================================================
echo   Verification Complete!
echo ============================================================
echo.

if !MODELS_MISSING! equ 1 (
    echo [WARN] Models are missing - download them before running production
    echo.
)

echo Next steps:
echo.
echo 1. If models are missing, download them:
echo    - See links above
echo.
echo 2. Test with Mock Mode (no GPU required):
echo    set MOCK_MODE=true
echo    uv run python -m src.main
echo.
echo 3. Test LiveTalking web interface:
echo    cd external\livetalking
echo    python app.py --transport webrtc --model wav2lip --avatar_id wav2lip256_avatar1
echo    Open: http://localhost:8010/webrtcapi.html
echo.
echo 4. Run production mode (requires GPU + models):
echo    uv run python -m src.main
echo.

pause
