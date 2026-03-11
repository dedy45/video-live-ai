@echo off
REM ========================================
REM Apply Groq + Gemini Only Configuration
REM ========================================
REM
REM This script will:
REM 1. Clean Windows environment variables
REM 2. Stop old server
REM 3. Clear caches
REM 4. Rebuild frontend
REM 5. Start new server
REM 6. Verify configuration
REM
REM Expected result:
REM - Active: groq (default)
REM - Healthy: 2/2 (groq, gemini)
REM - Dashboard loads in ~2 seconds
REM ========================================

echo.
echo ========================================
echo GROQ + GEMINI ONLY CONFIGURATION
echo ========================================
echo.
echo This will configure the system to use:
echo   - Groq (default, fastest)
echo   - Gemini (backup)
echo.
echo All other providers will be disabled.
echo.
pause

REM Step 1: Clean Windows environment variables
echo.
echo [1/6] Cleaning Windows environment variables...
setx ANTHROPIC_API_KEY "" >nul 2>&1
echo       [OK] Removed ANTHROPIC_API_KEY override

REM Step 2: Stop old server
echo.
echo [2/6] Stopping old server...
taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo       [OK] Server stopped

REM Step 3: Clear caches
echo.
echo [3/6] Clearing caches...
if exist "src\dashboard\frontend\.svelte-kit" (
    rmdir /s /q "src\dashboard\frontend\.svelte-kit"
    echo       [OK] Cleared Svelte cache
)
if exist "src\dashboard\frontend\build" (
    rmdir /s /q "src\dashboard\frontend\build"
    echo       [OK] Cleared build cache
)
if exist "__pycache__" (
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    echo       [OK] Cleared Python cache
)

REM Step 4: Rebuild frontend
echo.
echo [4/6] Rebuilding frontend...
cd src\dashboard\frontend
call npm run build >nul 2>&1
if errorlevel 1 (
    echo       [ERROR] Frontend build failed!
    cd ..\..\..
    pause
    exit /b 1
)
cd ..\..\..
echo       [OK] Frontend rebuilt

REM Step 5: Start server
echo.
echo [5/6] Starting server...
start /B python -m src.dashboard.main > tmp-dashboard-8011.log 2>&1
timeout /t 5 /nobreak >nul
echo       [OK] Server started

REM Step 6: Verify configuration
echo.
echo [6/6] Verifying configuration...
timeout /t 3 /nobreak >nul
python verify_config.py

echo.
echo ========================================
echo CONFIGURATION APPLIED!
echo ========================================
echo.
echo Next steps:
echo   1. Open dashboard: http://localhost:8001/dashboard/#/monitor
echo   2. Verify "Active: groq" (not "unknown")
echo   3. Verify "Healthy: 2/2"
echo   4. Test with "Test Brain" button
echo.
echo Expected performance:
echo   - Brain Health: ^< 100ms
echo   - Dashboard load: ~2 seconds
echo.
pause
