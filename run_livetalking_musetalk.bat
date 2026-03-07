@echo off
REM ============================================================
REM Run LiveTalking with MuseTalk 1.5
REM ============================================================
REM MuseTalk provides better quality than Wav2Lip
REM Requires: RTX 3080 Ti or better (8GB+ VRAM)
REM ============================================================

setlocal disabledelayedexpansion

echo.
echo ============================================================
echo   LiveTalking with MuseTalk 1.5
echo ============================================================
echo.

REM Get project root
pushd "%~dp0"
set "PROJECT_ROOT=%CD%\"
popd

echo Project root: %PROJECT_ROOT%
echo.

REM Check if LiveTalking exists
if not exist "%PROJECT_ROOT%external\livetalking\app.py" (
    echo [ERROR] LiveTalking not found!
    echo.
    echo Please run setup first:
    echo   git submodule update --init --recursive
    echo.
    pause
    exit /b 1
)

REM Check if MuseTalk models exist
if not exist "%PROJECT_ROOT%models\musetalk\*.pth" (
    echo [ERROR] MuseTalk models not found!
    echo.
    echo Please run setup first:
    echo   setup_musetalk_model.bat
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
if exist "%PROJECT_ROOT%.venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call "%PROJECT_ROOT%.venv\Scripts\activate.bat"
)

REM Check dependencies
echo Checking dependencies...
"%PROJECT_ROOT%.venv\Scripts\python.exe" -c "import flask_sockets" 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Dependencies not installed!
    echo Please run: install_livetalking_deps.bat
    pause
    exit /b 1
)

REM Change to LiveTalking directory
cd /d "%PROJECT_ROOT%external\livetalking"

echo.
echo ============================================================
echo   Starting LiveTalking with MuseTalk 1.5
echo ============================================================
echo.
echo Server will run on: http://localhost:8010
echo.
echo Available web interfaces:
echo   - WebRTC API:  http://localhost:8010/webrtcapi.html
echo   - RTC Push:    http://localhost:8010/rtcpushapi.html
echo   - Chat:        http://localhost:8010/chat.html
echo   - Dashboard:   http://localhost:8010/dashboard.html
echo.
echo Model: MuseTalk 1.5 (Better quality, requires RTX 3080 Ti+)
echo.
echo Press Ctrl+C to stop the server
echo.
echo ============================================================
echo.

REM Build Python path
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"

REM Check GPU
echo Checking GPU...
"%PYTHON_EXE%" -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"No GPU\"}')"
echo.

REM Run server with MuseTalk
echo Running LiveTalking with MuseTalk...
echo.

"%PYTHON_EXE%" app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar1

REM Alternative configurations:
REM For RTMP streaming:
REM "%PYTHON_EXE%" app.py --transport rtmp --model musetalk --avatar_id musetalk_avatar1

REM For custom avatar:
REM "%PYTHON_EXE%" app.py --transport webrtc --model musetalk --avatar_id your_custom_avatar

echo.
echo Server stopped.
cd /d "%PROJECT_ROOT%"
pause
