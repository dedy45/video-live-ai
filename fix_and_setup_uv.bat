@echo off
REM Fix corrupt packages dan setup UV environment yang bersih

echo ========================================
echo Fix and Setup UV Environment
echo ========================================
echo.

REM Check if in correct directory
if not exist "pyproject.toml" (
    echo ERROR: Must run from videoliveai folder
    echo Current: %CD%
    pause
    exit /b 1
)

echo [1/6] Cleaning up corrupt environment...
echo.

if exist ".venv" (
    echo Deleting corrupt .venv...
    rmdir /s /q .venv
    if exist ".venv" (
        echo WARNING: Could not delete .venv completely
        echo Please close any programs using .venv and try again
        pause
        exit /b 1
    )
    echo ✓ Deleted corrupt .venv
) else (
    echo No existing .venv found
)
echo.

echo [2/6] Cleaning UV cache...
echo This fixes corrupt package metadata
echo.
uv cache clean
echo ✓ Cache cleaned
echo.

echo [3/6] Creating fresh UV virtual environment...
uv venv --python 3.13
if %errorlevel% neq 0 (
    echo ERROR: Failed to create .venv
    echo.
    echo Trying with system Python...
    uv venv
    if %errorlevel% neq 0 (
        echo ERROR: Still failed
        pause
        exit /b 1
    )
)
echo ✓ Created fresh .venv
echo.

echo [4/6] Verifying Python path...
uv run python -c "import sys; print('Python:', sys.executable)"
echo.

echo [5/6] Installing dependencies (this may take a few minutes)...
echo.
echo Installing core dependencies first...
uv pip install --no-cache fastapi uvicorn pydantic pydantic-settings pyyaml python-dotenv
if %errorlevel% neq 0 (
    echo ERROR: Failed to install core dependencies
    pause
    exit /b 1
)
echo ✓ Core dependencies installed
echo.

echo Installing project dependencies...
uv pip install --no-cache -e .
if %errorlevel% neq 0 (
    echo ERROR: Failed to install project dependencies
    echo.
    echo Trying alternative method...
    uv pip install --no-cache --no-deps -e .
    uv pip install --no-cache websockets>=12.0
    uv pip install --no-cache TikTokLive>=6.0.0
    uv pip install --no-cache edge-tts>=6.1.0
    uv pip install --no-cache ffmpeg-python>=0.2.0
    uv pip install --no-cache numpy>=1.26.0
    uv pip install --no-cache Pillow>=10.2.0
    uv pip install --no-cache httpx>=0.27.0
    uv pip install --no-cache sqlalchemy>=2.0.25
    uv pip install --no-cache aiosqlite>=0.19.0
    uv pip install --no-cache structlog>=24.1.0
    uv pip install --no-cache anthropic>=0.18.0
    uv pip install --no-cache google-generativeai>=0.4.0
    uv pip install --no-cache openai>=1.12.0
    uv pip install --no-cache groq>=0.5.0
    uv pip install --no-cache litellm>=1.40.0
)
echo ✓ Project dependencies installed
echo.

echo [6/6] Verifying installation...
echo.
echo Checking critical packages...
uv pip list | findstr /i "fastapi pydantic websockets"
echo.

echo Python location:
uv run python -c "import sys; print(sys.executable)"
echo.

echo Testing imports...
uv run python -c "import fastapi; import pydantic; import websockets; print('✓ All imports successful')"
if %errorlevel% neq 0 (
    echo WARNING: Some imports failed
    echo This might be okay if you're not using those features
)
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo UV virtual environment is ready at:
echo   %CD%\.venv
echo.
echo To use:
echo   uv run python -m src.main
echo   uv run pytest tests/
echo.
echo Next steps:
echo 1. Test: set MOCK_MODE=true ^&^& uv run python -m src.main
echo 2. Run tests: test_livetalking.bat
echo.
pause
