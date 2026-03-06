@echo off
REM Simple and robust UV setup - fixes websockets corruption

echo ========================================
echo Simple UV Setup (Fix Websockets Issue)
echo ========================================
echo.

REM Check directory
if not exist "pyproject.toml" (
    echo ERROR: Run from videoliveai folder
    pause
    exit /b 1
)

echo Step 1: Delete corrupt .venv
if exist ".venv" (
    echo Deleting .venv...
    rmdir /s /q .venv 2>nul
    timeout /t 2 /nobreak >nul
    if exist ".venv" (
        echo ERROR: Cannot delete .venv
        echo Close all programs and try again
        pause
        exit /b 1
    )
)
echo ✓ Clean slate
echo.

echo Step 2: Clean UV cache
uv cache clean
echo ✓ Cache cleaned
echo.

echo Step 3: Create fresh .venv
uv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create .venv
    pause
    exit /b 1
)
echo ✓ .venv created
echo.

echo Step 4: Install dependencies WITHOUT cache
echo This avoids corrupt packages
echo.
uv pip install --no-cache -e .
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Installation failed
    echo.
    echo Trying minimal install...
    uv pip install --no-cache fastapi uvicorn pydantic python-dotenv
    if %errorlevel% neq 0 (
        echo ERROR: Even minimal install failed
        pause
        exit /b 1
    )
    echo.
    echo ✓ Minimal install successful
    echo You can install more packages later with:
    echo   uv pip install package-name
) else (
    echo ✓ All dependencies installed
)
echo.

echo Step 5: Verify
uv run python -c "import sys; print('Python:', sys.executable)"
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Test with:
echo   set MOCK_MODE=true
echo   uv run python -m src.main
echo.
pause
