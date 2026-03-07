@echo off
REM ============================================================
REM Setup MuseTalk 1.5 Model for LiveTalking
REM ============================================================
REM MuseTalk provides better lip-sync quality than Wav2Lip
REM ============================================================

setlocal disabledelayedexpansion

echo.
echo ============================================================
echo   MuseTalk 1.5 Model Setup
echo ============================================================
echo.
echo MuseTalk 1.5 provides:
echo   - Better lip-sync quality
echo   - More natural facial movements
echo   - Higher realism
echo.
echo Requirements:
echo   - GPU: RTX 3080 Ti or better (8GB+ VRAM)
echo   - Model size: ~1.5 GB
echo.

REM Get project root
pushd "%~dp0"
set "PROJECT_ROOT=%CD%\"
popd

echo Project root: %PROJECT_ROOT%
echo.

REM Create models directory
if not exist "%PROJECT_ROOT%models\musetalk" (
    echo Creating musetalk directory...
    mkdir "%PROJECT_ROOT%models\musetalk"
)

REM Check if models exist in external/livetalking
if exist "%PROJECT_ROOT%external\livetalking\models\musetalk" (
    echo.
    echo ============================================================
    echo   Models Found in LiveTalking Directory!
    echo ============================================================
    echo.
    echo Found: external\livetalking\models\musetalk\
    echo.
    
    setlocal enabledelayedexpansion
    set /p "COPY_MODEL=Copy to project models directory? (y/n): "
    
    if /i "!COPY_MODEL!"=="y" (
        endlocal
        echo.
        echo Copying MuseTalk models...
        xcopy "%PROJECT_ROOT%external\livetalking\models\musetalk" "%PROJECT_ROOT%models\musetalk\" /E /I /Y
        if %errorlevel% equ 0 (
            echo [OK] Models copied successfully!
            echo.
            goto CHECK_AVATAR
        ) else (
            echo [ERROR] Failed to copy models
            pause
            exit /b 1
        )
    ) else (
        endlocal
        echo Skipped copying.
    )
)

REM Check if models already exist
if exist "%PROJECT_ROOT%models\musetalk\*.pth" (
    echo.
    echo ============================================================
    echo   MuseTalk Models Already Exist!
    echo ============================================================
    echo.
    echo Location: %PROJECT_ROOT%models\musetalk\
    echo.
    dir "%PROJECT_ROOT%models\musetalk\*.pth" /B
    echo.
    goto CHECK_AVATAR
)

REM Models not found - show download instructions
echo.
echo ============================================================
echo   Models Not Found - Download Required
echo ============================================================
echo.
echo Download MuseTalk 1.5 models:
echo.
echo [Option 1] LiveTalking Official Sources (Recommended)
echo   - Quark Cloud: https://pan.quark.cn/s/83a750323ef0
echo   - Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
echo.
echo   Look for: musetalk models
echo   Place in: %PROJECT_ROOT%models\musetalk\
echo.
echo [Option 2] MuseTalk Official Repository
echo   - GitHub: https://github.com/TMElyralab/MuseTalk
echo   - HuggingFace: https://huggingface.co/TMElyralab/MuseTalk
echo.
echo   Download all model files to: %PROJECT_ROOT%models\musetalk\
echo.
echo [Option 3] HuggingFace CLI (Automated)
echo.
echo   Install HuggingFace CLI:
echo     uv pip install huggingface-hub
echo.
echo   Download models:
echo     huggingface-cli download TMElyralab/MuseTalk --local-dir models\musetalk
echo.

setlocal enabledelayedexpansion
set /p "DOWNLOAD_NOW=Download using HuggingFace CLI now? (y/n): "

if /i "!DOWNLOAD_NOW!"=="y" (
    endlocal
    echo.
    echo Installing HuggingFace CLI...
    call "%PROJECT_ROOT%.venv\Scripts\activate.bat"
    uv pip install huggingface-hub
    
    echo.
    echo Downloading MuseTalk models (~1.5 GB)...
    echo This may take 10-20 minutes...
    echo.
    
    huggingface-cli download TMElyralab/MuseTalk --local-dir "%PROJECT_ROOT%models\musetalk"
    
    if %errorlevel% equ 0 (
        echo.
        echo [OK] Models downloaded successfully!
        goto CHECK_AVATAR
    ) else (
        echo.
        echo [ERROR] Download failed
        echo Please download manually from the links above
        pause
        exit /b 1
    )
) else (
    endlocal
    echo.
    echo Please download models manually, then run this script again.
    echo.
    pause
    exit /b 0
)

:CHECK_AVATAR
echo.
echo ============================================================
echo   Checking Avatar Data
echo ============================================================
echo.

if not exist "%PROJECT_ROOT%data\avatars" (
    echo Creating avatars directory...
    mkdir "%PROJECT_ROOT%data\avatars"
)

REM Check for MuseTalk avatar
if exist "%PROJECT_ROOT%external\livetalking\data\avatars\musetalk_avatar1" (
    echo Found MuseTalk avatar in LiveTalking directory!
    echo.
    
    setlocal enabledelayedexpansion
    set /p "COPY_AVATAR=Copy avatar to project data directory? (y/n): "
    
    if /i "!COPY_AVATAR!"=="y" (
        endlocal
        echo.
        echo Copying avatar...
        xcopy "%PROJECT_ROOT%external\livetalking\data\avatars\musetalk_avatar1" "%PROJECT_ROOT%data\avatars\musetalk_avatar1\" /E /I /Y
        if %errorlevel% equ 0 (
            echo [OK] Avatar copied successfully!
        )
    ) else (
        endlocal
    )
)

if exist "%PROJECT_ROOT%data\avatars\musetalk_avatar1" (
    echo [OK] MuseTalk avatar data exists
) else (
    echo.
    echo [INFO] MuseTalk avatar data not found
    echo.
    echo You can:
    echo   1. Download from LiveTalking sources
    echo   2. Use custom video/image
    echo   3. Record your own reference video
    echo.
)

echo.
echo ============================================================
echo   Setup Summary
echo ============================================================
echo.

if exist "%PROJECT_ROOT%models\musetalk\*.pth" (
    echo [OK] MuseTalk models installed
    dir "%PROJECT_ROOT%models\musetalk\*.pth" /B
) else (
    echo [MISSING] MuseTalk models
)

echo.

if exist "%PROJECT_ROOT%data\avatars\musetalk_avatar1" (
    echo [OK] Avatar: musetalk_avatar1
) else (
    echo [OPTIONAL] Avatar: musetalk_avatar1
)

echo.
echo ============================================================
echo   Next Steps
echo ============================================================
echo.

if exist "%PROJECT_ROOT%models\musetalk\*.pth" (
    echo Models are ready! You can now run:
    echo.
    echo   run_livetalking_musetalk.bat
    echo.
    echo Or manually:
    echo   run_livetalking_web.bat
    echo   Then edit to use --model musetalk
    echo.
) else (
    echo Please download MuseTalk models first:
    echo   1. From LiveTalking sources, or
    echo   2. Run this script again and choose HuggingFace CLI option
    echo.
)

pause
