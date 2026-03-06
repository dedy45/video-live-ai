@echo off
REM Setup LiveTalking dengan UV (bukan conda!)
REM Script ini memastikan menggunakan UV virtual environment

echo ========================================
echo LiveTalking Setup dengan UV
echo ========================================
echo.

REM Check jika sudah di folder videoliveai
if not exist "pyproject.toml" (
    echo ERROR: Harus dijalankan dari folder videoliveai
    echo Current directory: %CD%
    echo.
    echo Cara pakai:
    echo   cd videoliveai
    echo   setup_livetalking_uv.bat
    pause
    exit /b 1
)

echo [1/5] Checking UV installation...
uv --version
if %errorlevel% neq 0 (
    echo ERROR: UV not installed
    echo Install with: pip install uv
    pause
    exit /b 1
)
echo.

echo [2/5] Creating UV virtual environment...
if not exist ".venv" (
    echo Creating new .venv...
    uv venv
) else (
    echo .venv already exists
)
echo.

echo [3/5] Installing dependencies...
uv pip install -e ".[livetalking]"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [4/5] Running setup script with UV...
echo Using UV Python (NOT conda!)
echo.
echo NOTE: This will setup folders and check dependencies
echo LiveTalking submodule will be cloned if not present
echo.
uv run python scripts/setup_livetalking.py --skip-models
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Setup script had issues
    echo This is okay if LiveTalking submodule is not cloned yet
    echo.
    echo You can:
    echo 1. Continue with basic setup
    echo 2. Clone LiveTalking manually: git submodule update --init
    echo 3. Run this script again after cloning
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        pause
        exit /b 1
    )
)
echo.

echo [5/5] Verifying setup...
if exist "external\livetalking" (
    echo ✓ LiveTalking submodule exists
) else (
    echo ⚠ LiveTalking submodule not found
)

if exist "models" (
    echo ✓ Models folder exists
) else (
    echo ⚠ Models folder not found
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Download models (5GB)
echo 2. Prepare reference video/audio
echo 3. Test: test_livetalking.bat
echo.
pause
