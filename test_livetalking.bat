@echo off
REM Quick test script for LiveTalking integration
REM Run this to test the integration without GPU

echo ========================================
echo LiveTalking Integration Test
echo ========================================
echo.

echo [1/3] Installing dependencies...
uv pip install -e ".[livetalking]"
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

echo [2/3] Running tests with MOCK_MODE...
set MOCK_MODE=true
uv run pytest tests/test_livetalking_integration.py -v -m "not integration"
if %errorlevel% neq 0 (
    echo ERROR: Tests failed
    pause
    exit /b 1
)
echo.

echo [3/3] All tests passed!
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
