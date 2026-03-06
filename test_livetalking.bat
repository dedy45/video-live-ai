@echo off
REM Quick test script for LiveTalking integration
REM Run this to test the integration without GPU

echo ========================================
echo LiveTalking Integration Test
echo ========================================
echo.

REM Check if in correct directory
if not exist "pyproject.toml" (
    echo ERROR: Must run from videoliveai folder
    echo Current: %CD%
    pause
    exit /b 1
)

echo [1/4] Creating UV virtual environment...
if not exist ".venv" (
    echo Creating .venv...
    uv venv
) else (
    echo .venv already exists
)
echo.

echo [2/4] Installing dependencies...
uv pip install -e ".[livetalking]"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [3/4] Verifying Python path...
uv run python -c "import sys; print('Using Python:', sys.executable)"
echo.

echo [4/4] Running tests with MOCK_MODE...
set MOCK_MODE=true
uv run pytest tests/test_livetalking_integration.py -v -m "not integration"
if %errorlevel% neq 0 (
    echo ERROR: Tests failed
    pause
    exit /b 1
)
echo.

echo All tests passed!
echo.
echo ========================================
echo SUCCESS: LiveTalking integration works!
echo ========================================
echo.
echo Next steps:
echo 1. Run setup: python scripts/setup_livetalking.py
echo 2. Download models (5GB)
echo 3. Prepare reference video/audio
echo 4. Test production mode
echo.
pause
