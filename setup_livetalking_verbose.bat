@echo off
REM Setup LiveTalking dengan UV - VERBOSE MODE untuk debugging
REM Script ini menampilkan semua output untuk troubleshooting

echo ========================================
echo LiveTalking Setup - VERBOSE MODE
echo ========================================
echo.

REM Check jika sudah di folder videoliveai
if not exist "pyproject.toml" (
    echo ERROR: Harus dijalankan dari folder videoliveai
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo [1/6] Checking UV installation...
uv --version
if %errorlevel% neq 0 (
    echo ERROR: UV not installed
    echo Install with: pip install uv
    pause
    exit /b 1
)
echo.

echo [2/6] Checking UV lock file...
uv lock --check
if %errorlevel% neq 0 (
    echo WARNING: Lock file out of sync
    echo Updating lock file...
    uv lock
)
echo.

echo [3/6] Creating UV virtual environment...
if not exist ".venv" (
    echo Creating new .venv...
    uv venv --verbose
) else (
    echo .venv already exists
)
echo.

echo [4/6] Installing CORE dependencies (fast)...
echo Packages: fastapi, pydantic, litellm, etc (~200MB)
echo.
uv pip install -e . --verbose
if %errorlevel% neq 0 (
    echo ERROR: Failed to install core dependencies
    pause
    exit /b 1
)
echo.
echo Core dependencies installed successfully!
echo.

echo [5/6] Installing LIVETALKING dependencies (slow)...
echo.
echo WARNING: This downloads ~2GB of packages:
echo   - torch (~1.5GB)
echo   - torchvision (~500MB)
echo   - opencv-python (~100MB)
echo   - aiortc, av, scipy, librosa, etc
echo.
echo Estimated time: 5-15 minutes (depends on internet speed)
echo.
set /p CONTINUE="Continue with LiveTalking install? (y/n): "
if /i not "%CONTINUE%"=="y" (
    echo.
    echo Skipping LiveTalking dependencies
    echo You can install later with: uv pip install -e ".[livetalking]"
    goto :verify
)
echo.
echo Starting download... (this will take a while)
echo.
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 --verbose
if %errorlevel% neq 0 (
    echo ERROR: Failed to install PyTorch
    echo Try: uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    pause
    exit /b 1
)
echo.
echo PyTorch installed! Now installing other LiveTalking deps...
echo.
uv pip install opencv-python scikit-image scipy librosa soundfile resampy aiortc av imageio imageio-ffmpeg --verbose
if %errorlevel% neq 0 (
    echo ERROR: Failed to install other dependencies
    pause
    exit /b 1
)
echo.

:verify
echo [6/6] Verifying installation...
echo.
uv run python -c "import sys; print('Python:', sys.executable)"
uv run python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
uv run python -c "import pydantic; print('Pydantic:', pydantic.__version__)"
echo.
set /p CHECK_TORCH="Check PyTorch installation? (y/n): "
if /i "%CHECK_TORCH%"=="y" (
    uv run python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Installed packages:
uv pip list | findstr /i "torch fastapi pydantic opencv"
echo.
echo Next steps:
echo 1. Clone LiveTalking: git submodule update --init
echo 2. Download models (see LIVETALKING_QUICKSTART.md)
echo 3. Test: uv run python -m src.main
echo.
pause
