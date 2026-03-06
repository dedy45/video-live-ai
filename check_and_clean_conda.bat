@echo off
REM Check dan clean conda base environment dari packages LiveTalking

echo ========================================
echo Check Conda Base Environment
echo ========================================
echo.

echo [1/3] Checking conda base packages...
echo.
echo Packages yang mungkin ter-install dari LiveTalking:
echo - torch, torchvision, torchaudio
echo - opencv-python
echo - aiortc, av
echo - librosa, soundfile, resampy
echo - scikit-image
echo.

REM Check packages
echo Checking for torch...
conda list | findstr /i "torch"
if %errorlevel% equ 0 (
    echo ✓ Found torch packages
) else (
    echo ✗ No torch packages
)
echo.

echo Checking for opencv...
conda list | findstr /i "opencv"
if %errorlevel% equ 0 (
    echo ✓ Found opencv packages
) else (
    echo ✗ No opencv packages
)
echo.

echo Checking for aiortc...
conda list | findstr /i "aiortc"
if %errorlevel% equ 0 (
    echo ✓ Found aiortc packages
) else (
    echo ✗ No aiortc packages
)
echo.

echo Checking for librosa...
conda list | findstr /i "librosa"
if %errorlevel% equ 0 (
    echo ✓ Found librosa packages
) else (
    echo ✗ No librosa packages
)
echo.

echo [2/3] Summary...
echo.
echo Conda base environment location:
conda info --base
echo.

echo Total packages in conda base:
conda list | find /c /v ""
echo.

echo [3/3] Cleanup options...
echo.
echo Jika ada packages LiveTalking di conda base, Anda bisa:
echo.
echo Option 1: Uninstall specific packages
echo   conda uninstall torch torchvision torchaudio opencv-python aiortc
echo.
echo Option 2: Create fresh conda environment (recommended)
echo   conda create -n clean python=3.13
echo   conda activate clean
echo.
echo Option 3: Ignore conda, use UV only (BEST for this project)
echo   cd videoliveai
echo   uv venv
echo   uv pip install -e ".[livetalking]"
echo.

echo ========================================
echo Recommendation
echo ========================================
echo.
echo Untuk project ini (videoliveai), JANGAN gunakan conda!
echo Gunakan UV virtual environment:
echo.
echo   cd videoliveai
echo   uv venv
echo   uv pip install -e ".[livetalking]"
echo   uv run python -m src.main
echo.
echo Conda base environment Anda terlihat bersih.
echo Tidak perlu uninstall apapun.
echo.
pause
