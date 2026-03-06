@echo off
REM Test setup - verify installation tanpa install ulang

echo ========================================
echo Testing VideoLiveAI Setup
echo ========================================
echo.

if not exist "pyproject.toml" (
    echo ERROR: Run from videoliveai folder
    pause
    exit /b 1
)

echo [1/7] Checking UV...
uv --version
if %errorlevel% neq 0 (
    echo X UV not installed
    pause
    exit /b 1
)
echo OK UV installed
echo.

echo [2/7] Checking .venv...
if not exist ".venv" (
    echo X .venv not found
    echo Run: uv venv
    pause
    exit /b 1
)
echo OK .venv exists
echo.

echo [3/7] Checking Python path...
uv run python -c "import sys; print('Python:', sys.executable)"
echo.

echo [4/7] Checking core packages...
uv run python -c "import fastapi; print('OK FastAPI:', fastapi.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo X FastAPI not installed
    echo Run: uv pip install -e .
    pause
    exit /b 1
)

uv run python -c "import pydantic; print('OK Pydantic:', pydantic.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo X Pydantic not installed
    pause
    exit /b 1
)

uv run python -c "import litellm; print('OK LiteLLM:', litellm.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo X LiteLLM not installed
    pause
    exit /b 1
)
echo.

echo [5/7] Checking LiveTalking packages (optional)...
uv run python -c "import torch; print('OK PyTorch:', torch.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ! PyTorch not installed (optional for LiveTalking)
) else (
    uv run python -c "import torch; print('  CUDA available:', torch.cuda.is_available())" 2>nul
)

uv run python -c "import cv2; print('OK OpenCV:', cv2.__version__)" 2>nul
if %errorlevel% neq 0 (
    echo ! OpenCV not installed (optional for LiveTalking)
)
echo.

echo [6/7] Checking project structure...
if exist "src\main.py" (
    echo OK src\main.py exists
) else (
    echo X src\main.py not found
)

if exist "config.yaml" (
    echo OK config.yaml exists
) else (
    echo ! config.yaml not found
)

if exist ".env" (
    echo OK .env exists
) else (
    echo ! .env not found (copy from .env.example)
)
echo.

echo [7/7] Testing imports...
set MOCK_MODE=true
uv run python -c "from src.config import get_config; print('OK Config loads')" 2>nul
if %errorlevel% neq 0 (
    echo X Config import failed
    pause
    exit /b 1
)

uv run python -c "from src.utils.logging import get_logger; print('OK Logging')" 2>nul
if %errorlevel% neq 0 (
    echo X Logging import failed
    pause
    exit /b 1
)
echo.

echo ========================================
echo OK Setup Test PASSED
echo ========================================
echo.
echo Your installation is ready!
echo.
echo To run the server:
echo   set MOCK_MODE=true
echo   uv run python -m src.main
echo.
echo To run tests:
echo   uv run pytest tests/ -v
echo.
pause
