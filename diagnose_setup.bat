@echo off
REM Diagnose setup issues - comprehensive check
REM Run this if setup fails or hangs

echo ========================================
echo VideoLiveAI Setup Diagnostics
echo ========================================
echo.

if not exist "pyproject.toml" (
    echo ERROR: Run from videoliveai folder
    pause
    exit /b 1
)

echo [System Info]
echo OS: %OS%
echo Processor: %PROCESSOR_ARCHITECTURE%
echo User: %USERNAME%
echo Current Dir: %CD%
echo.

echo [UV Info]
where uv
uv --version
echo.

echo [Python Info]
where python
python --version
echo.

echo [Virtual Environment]
if exist ".venv" (
    echo ✓ .venv exists
    dir .venv\Scripts\python.exe
    echo.
    echo Python in venv:
    .venv\Scripts\python.exe --version
    echo.
    echo Packages in venv:
    .venv\Scripts\python.exe -m pip list | findstr /i "fastapi pydantic torch opencv"
) else (
    echo ❌ .venv not found
)
echo.

echo [UV Lock File]
if exist "uv.lock" (
    echo ✓ uv.lock exists
    uv lock --check
) else (
    echo ❌ uv.lock not found
)
echo.

echo [Disk Space]
echo Checking available disk space...
wmic logicaldisk get caption,freespace,size
echo.

echo [Network Test]
echo Testing PyPI connection...
ping pypi.org -n 2
echo.

echo [UV Cache]
echo UV cache location:
uv cache dir
echo.
echo Cache size:
dir /s "%LOCALAPPDATA%\uv\cache" 2>nul | findstr /i "bytes"
echo.

echo [Project Files]
if exist "pyproject.toml" echo ✓ pyproject.toml
if exist "config.yaml" echo ✓ config.yaml
if exist ".env" (
    echo ✓ .env
) else (
    echo ⚠ .env not found
)
if exist "src\main.py" echo ✓ src\main.py
if exist "tests" echo ✓ tests folder
echo.

echo [Git Submodules]
if exist ".gitmodules" (
    echo ✓ .gitmodules exists
    type .gitmodules
    echo.
    if exist "external\livetalking" (
        echo ✓ LiveTalking submodule cloned
    ) else (
        echo ⚠ LiveTalking submodule NOT cloned
        echo   Run: git submodule update --init
    )
) else (
    echo ⚠ No git submodules configured
)
echo.

echo [Common Issues Check]
echo.
echo 1. Checking for conda interference...
where conda 2>nul
if %errorlevel% equ 0 (
    echo ⚠ Conda found in PATH
    echo   Make sure NOT to activate conda env when using UV
) else (
    echo ✓ No conda in PATH
)
echo.

echo 2. Checking for multiple Python installations...
where python /R C:\
echo.

echo 3. Checking antivirus/firewall...
echo   If setup hangs, temporarily disable antivirus
echo   and check firewall settings for Python/UV
echo.

echo ========================================
echo Diagnostic Complete
echo ========================================
echo.
echo If you see issues above:
echo 1. Network issues → Check firewall/proxy
echo 2. Disk space low → Free up space
echo 3. Conda interference → Don't activate conda
echo 4. .venv corrupt → Run: simple_setup_uv.bat
echo.
pause
