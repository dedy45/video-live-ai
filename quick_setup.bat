@echo off
REM Quick setup untuk videoliveai - TANPA LiveTalking dulu

echo ========================================
echo Quick Setup - VideoLiveAI
echo ========================================
echo.
echo This will setup the basic project WITHOUT LiveTalking
echo LiveTalking can be added later with setup_livetalking_uv.bat
echo.

REM Check directory
if not exist "pyproject.toml" (
    echo ERROR: Run from videoliveai folder
    pause
    exit /b 1
)

echo [1/5] Cleaning up...
if exist ".venv" (
    echo Deleting old .venv...
    rmdir /s /q .venv 2>nul
    timeout /t 1 /nobreak >nul
)
uv cache clean
echo ✓ Clean
echo.

echo [2/5] Creating UV virtual environment...
uv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create .venv
    pause
    exit /b 1
)
echo ✓ .venv created
echo.

echo [3/5] Installing CORE dependencies only...
echo (This skips LiveTalking dependencies for now)
echo.
uv pip install --no-cache -e .
if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    echo.
    echo Trying minimal install...
    uv pip install --no-cache fastapi uvicorn pydantic pydantic-settings pyyaml python-dotenv
    uv pip install --no-cache sqlalchemy aiosqlite structlog
    uv pip install --no-cache anthropic google-generativeai openai groq litellm
    uv pip install --no-cache websockets edge-tts ffmpeg-python numpy Pillow httpx
    if %errorlevel% neq 0 (
        echo ERROR: Even minimal install failed
        pause
        exit /b 1
    )
)
echo ✓ Core dependencies installed
echo.

echo [4/5] Creating necessary folders...
if not exist "models" mkdir models
if not exist "models\musetalk" mkdir models\musetalk
if not exist "models\er-nerf" mkdir models\er-nerf
if not exist "models\gfpgan" mkdir models\gfpgan
if not exist "assets\avatar" mkdir assets\avatar
if not exist "assets\voice" mkdir assets\voice
if not exist "assets\backgrounds" mkdir assets\backgrounds
if not exist "assets\products" mkdir assets\products
if not exist "data\logs" mkdir data\logs
echo ✓ Folders created
echo.

echo [5/5] Verifying setup...
uv run python -c "import sys; print('Python:', sys.executable)"
echo.
uv run python -c "import fastapi, pydantic; print('✓ Core imports work')"
if %errorlevel% neq 0 (
    echo WARNING: Some imports failed
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo What's installed:
echo - Core dependencies (FastAPI, Pydantic, etc)
echo - LLM providers (Gemini, Claude, GPT-4o, Groq)
echo - Basic utilities
echo.
echo What's NOT installed yet:
echo - LiveTalking dependencies (torch, opencv, etc)
echo - Model weights
echo.
echo Next steps:
echo.
echo 1. Test basic functionality:
echo    set MOCK_MODE=true
echo    uv run python -m src.main
echo.
echo 2. Setup LiveTalking (optional):
echo    setup_livetalking_uv.bat
echo.
echo 3. Or install LiveTalking dependencies manually:
echo    uv pip install -e ".[livetalking]"
echo.
pause
