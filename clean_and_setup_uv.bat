@echo off
REM Clean dan setup fresh UV environment untuk videoliveai

echo ========================================
echo Clean and Setup UV Environment
echo ========================================
echo.

REM Check if in correct directory
if not exist "pyproject.toml" (
    echo ERROR: Must run from videoliveai folder
    echo Current: %CD%
    pause
    exit /b 1
)

echo [1/5] Checking current setup...
echo.

if exist ".venv" (
    echo Found existing .venv folder
    echo Size:
    dir .venv /s | find "File(s)"
    echo.
    
    set /p CLEAN="Delete existing .venv and start fresh? (y/n): "
    if /i "%CLEAN%"=="y" (
        echo Deleting .venv...
        rmdir /s /q .venv
        echo ✓ Deleted
    ) else (
        echo Keeping existing .venv
    )
) else (
    echo No existing .venv found
)
echo.

echo [2/5] Creating fresh UV virtual environment...
uv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create .venv
    pause
    exit /b 1
)
echo ✓ Created .venv
echo.

echo [3/5] Verifying Python path...
uv run python -c "import sys; print('Python:', sys.executable)"
echo.

echo [4/5] Installing dependencies...
echo This will install to .venv (NOT conda!)
echo.
uv pip install -e ".[livetalking]"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed
echo.

echo [5/5] Verifying installation...
echo.
echo Installed packages:
uv pip list | findstr /i "torch opencv aiortc"
echo.

echo Python location:
uv run python -c "import sys; print(sys.executable)"
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo UV virtual environment is ready at:
echo   %CD%\.venv
echo.
echo To use:
echo   uv run python script.py
echo   uv run pytest tests/
echo   uv run python -m src.main
echo.
echo To activate manually:
echo   .venv\Scripts\activate
echo.
echo Next steps:
echo 1. Test: test_livetalking.bat
echo 2. Setup LiveTalking: setup_livetalking_uv.bat
echo.
pause
