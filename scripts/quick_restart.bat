@echo off
REM ============================================================
REM Quick Restart (No Cache Clear)
REM ============================================================

echo.
echo ============================================================
echo QUICK RESTART SERVER
echo ============================================================
echo.

REM Kill old processes
echo [1/2] Stopping old server...
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 2 /nobreak >nul
echo      Done!

REM Start new server
echo [2/2] Starting new server...
echo.
echo ============================================================
echo SERVER STARTING - Press Ctrl+C to stop
echo ============================================================
echo.
echo Dashboard: http://localhost:8001/dashboard/#/monitor
echo.

python C:\\Users\\dedy\\Documents\\!fast-track-income\\videoliveai\\src\\main.py

pause
