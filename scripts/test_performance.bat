@echo off
REM ============================================================
REM Test Monitor Performance
REM ============================================================

echo.
echo ============================================================
echo TESTING MONITOR PERFORMANCE
echo ============================================================
echo.

REM Check if server is running
echo Checking if server is running...
curl -s http://localhost:8001/api/status >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Server is not running!
    echo Please run: quick_restart.bat
    echo.
    pause
    exit /b 1
)

echo Server is UP!
echo.
echo Running performance test...
echo.

python test_monitor_api.py

echo.
echo ============================================================
echo TEST COMPLETE
echo ============================================================
echo.
echo Expected Results:
echo   - Brain Health: ^< 100ms (was 20,000ms)
echo   - Total Time: ^< 3s (was 30s)
echo.

pause
