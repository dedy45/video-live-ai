@echo off
REM Restart Dashboard Server with proper cleanup

echo ============================================================
echo AI Live Commerce - Dashboard Server Restart
echo ============================================================
echo.

REM Kill existing Python processes running the server
echo [1/4] Stopping existing server processes...
for /f "tokens=2" %%i in ('tasklist ^| findstr /i "python.exe"') do (
    taskkill /F /PID %%i >nul 2>&1
)
timeout /t 2 /nobreak >nul

REM Clean up PID file
echo [2/4] Cleaning up PID file...
if exist "data\.server.pid" del /f /q "data\.server.pid"

REM Verify .env file exists
echo [3/4] Checking .env file...
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please create .env file from .env.example
    pause
    exit /b 1
)
echo    OK: .env file found

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    echo [4/5] Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo [4/5] No virtual environment found, using system Python
)

REM Start server with debug logging
echo [5/5] Starting server...
echo.
echo ============================================================
echo Server starting on http://localhost:8000
echo Dashboard: http://localhost:8000/dashboard
echo API Docs: http://localhost:8000/docs
echo ============================================================
echo.
echo Press Ctrl+C to stop the server
echo.

.venv\Scripts\python.exe run_dashboard_debug.py

echo.
echo Server stopped.
pause
