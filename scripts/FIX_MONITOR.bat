@echo off
REM ============================================================
REM MASTER SCRIPT - Fix Monitor Dashboard Performance
REM ============================================================

echo.
echo ============================================================
echo FIX MONITOR DASHBOARD - COMPLETE SOLUTION
echo ============================================================
echo.
echo This script will:
echo   1. Stop old server
echo   2. Clear all caches
echo   3. Rebuild frontend
echo   4. Start new server
echo   5. Test performance
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause >nul

REM ── Step 1: Kill old server ────────────────────────────────
echo.
echo [1/5] Stopping old server...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo      Done!

REM ── Step 2: Clear caches ───────────────────────────────────
echo [2/5] Clearing caches...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" >nul 2>&1
del /s /q *.pyc >nul 2>&1
if exist "src\dashboard\frontend\node_modules\.vite" rd /s /q "src\dashboard\frontend\node_modules\.vite" >nul 2>&1
echo      Done!

REM ── Step 3: Rebuild frontend ───────────────────────────────
echo [3/5] Rebuilding frontend...
cd src\dashboard\frontend
call npm run build >nul 2>&1
cd ..\..\..
echo      Done!

REM ── Step 4: Start server in background ─────────────────────
echo [4/5] Starting server in background...
start /B python src\main.py > tmp-server-output.log 2>&1
echo      Waiting 10 seconds for server to start...
timeout /t 10 /nobreak >nul
echo      Done!

REM ── Step 5: Test performance ───────────────────────────────
echo [5/5] Testing performance...
echo.
python test_monitor_api.py

echo.
echo ============================================================
echo FIX COMPLETE!
echo ============================================================
echo.
echo Server is running in background.
echo Dashboard: http://localhost:8001/dashboard/#/monitor
echo.
echo To stop server: taskkill /F /IM python.exe
echo To view logs: type tmp-server-output.log
echo.
echo Expected performance:
echo   - Brain Health: ^< 100ms (was 20,000ms)
echo   - Total load: ^< 3s (was 30s)
echo.

pause
