@echo off
REM ========================================
REM Clean Environment & Restart Server
REM ========================================

echo.
echo ========================================
echo CLEANING ENVIRONMENT VARIABLES
echo ========================================
echo.

REM Remove Windows environment variable overrides
setx ANTHROPIC_API_KEY "" >nul 2>&1
echo [OK] Removed ANTHROPIC_API_KEY

echo.
echo ========================================
echo STOPPING OLD SERVER
echo ========================================
echo.

taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Server stopped

echo.
echo ========================================
echo STARTING NEW SERVER
echo ========================================
echo.

start /B python src/main.py > tmp-dashboard-8011.log 2>&1
timeout /t 8 /nobreak >nul
echo [OK] Server started

echo.
echo ========================================
echo TESTING API
echo ========================================
echo.

timeout /t 3 /nobreak >nul
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8001/api/brain/health' -Method GET -TimeoutSec 15 | Select-Object -ExpandProperty Content | ConvertFrom-Json | ConvertTo-Json -Depth 3"

echo.
echo ========================================
echo CHECKING LOGS
echo ========================================
echo.

powershell -Command "Select-String -Path 'tmp-dashboard-8011.log' -Pattern 'adapter_loaded|adapter_skipped|adapters_build_complete' | Select-Object -Last 10"

echo.
echo ========================================
echo DONE!
echo ========================================
echo.
echo Open dashboard: http://localhost:8001/dashboard/#/monitor
echo.
pause
