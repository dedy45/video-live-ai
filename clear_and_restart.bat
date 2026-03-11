@echo off
REM ============================================================
REM Clear Cache and Restart Server Script
REM ============================================================

echo.
echo ============================================================
echo CLEARING CACHE AND RESTARTING SERVER
echo ============================================================
echo.

REM ── Step 1: Kill old Python processes ──────────────────────
echo [1/6] Stopping old Python processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM pythonw.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo      Done!

REM ── Step 2: Clear Python cache ─────────────────────────────
echo [2/6] Clearing Python __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc >nul 2>&1
echo      Done!

REM ── Step 3: Clear browser cache (optional) ─────────────────
echo [3/6] Clearing browser cache...
REM Chrome cache
if exist "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" (
    rd /s /q "%LOCALAPPDATA%\Google\Chrome\User Data\Default\Cache" >nul 2>&1
)
REM Edge cache
if exist "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" (
    rd /s /q "%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Cache" >nul 2>&1
)
echo      Done!

REM ── Step 4: Clear frontend build cache ─────────────────────
echo [4/6] Clearing frontend build cache...
if exist "src\dashboard\frontend\node_modules\.vite" (
    rd /s /q "src\dashboard\frontend\node_modules\.vite"
)
if exist "src\dashboard\frontend\.svelte-kit" (
    rd /s /q "src\dashboard\frontend\.svelte-kit"
)
echo      Done!

REM ── Step 5: Rebuild frontend ───────────────────────────────
echo [5/6] Rebuilding frontend...
cd src\dashboard\frontend
call npm run build >nul 2>&1
cd ..\..\..
echo      Done!

REM ── Step 6: Start server ───────────────────────────────────
echo [6/6] Starting server...
echo.
echo ============================================================
echo SERVER STARTING - Press Ctrl+C to stop
echo ============================================================
echo.
echo Dashboard will be available at:
echo   http://localhost:8001/dashboard/#/monitor
echo.
echo Waiting 5 seconds for server to start...
echo.

REM Start server
python src\main.py

pause
