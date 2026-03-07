@echo off
REM ============================================================
REM Setup Wav2Lip Model for LiveTalking
REM ============================================================
REM This script will guide you to download and setup wav2lip model
REM ============================================================

setlocal disabledelayedexpansion

echo.
echo ============================================================
echo   Wav2Lip Model Setup
echo ============================================================
echo.

REM Get project root
pushd "%~dp0"
set "PROJECT_ROOT=%CD%\"
popd

echo Project root: %PROJECT_ROOT%
echo.

REM Check if models directory exists
if not exist "%PROJECT_ROOT%models" (
    echo Creating models directory...
    mkdir "%PROJECT_ROOT%models"
)

REM Check if external/livetalking/models exists
if exist "%PROJECT_ROOT%external\livetalking\models\wav2lip.pth" (
    echo.
    echo ============================================================
    echo   Model Found in LiveTalking Directory!
    echo ============================================================
    echo.
    echo Found: external\livetalking\models\wav2lip.pth
    echo.
    set /p "COPY_MODEL=Copy to project models directory? (y/n): "
    
    setlocal enabledelayedexpansion
    if /i "!COPY_MODEL!"=="y" (
        endlocal
        echo.
        echo Copying model...
        copy "%PROJECT_ROOT%external\livetalking\models\wav2lip.pth" "%PROJECT_ROOT%models\wav2lip.pth"
        if %errorlevel% equ 0 (
            echo [OK] Model copied successfully!
            echo.
            echo Model location: %PROJECT_ROOT%models\wav2lip.pth
            echo.
            goto SETUP_AVATAR
        ) else (
            echo [ERROR] Failed to copy model
            pause
            exit /b 1
        )
    ) else (
        endlocal
        echo Skipped copying.
    )
)

REM Check if model already exists in project
if exist "%PROJECT_ROOT%models\wav2lip.pth" (
    echo.
    echo ============================================================
    echo   Model Already Exists!
    echo ============================================================
    echo.
    echo Location: %PROJECT_ROOT%models\wav2lip.pth
    echo.
    goto SETUP_AVATAR
)

REM Model not found - show download instructions
echo.
echo ============================================================
echo   Model Not Found - Download Required
echo ============================================================
echo.
echo You need to download wav2lip model manually.
echo.
echo Download Options:
echo.
echo [Option 1] LiveTalking Official Sources (Recommended)
echo   - Quark Cloud: https://pan.quark.cn/s/83a750323ef0
echo   - Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
echo.
echo   Download: wav2lip256.pth
echo   Rename to: wav2lip.pth
echo   Place in: %PROJECT_ROOT%models\
echo.
echo [Option 2] Original Wav2Lip Repository
echo   - GitHub: https://github.com/Rudrabha/Wav2Lip
echo   - Model: https://iiitaphyd-my.sharepoint.com/:u:/g/personal/radrabha_m_research_iiit_ac_in/Eb3LEzbfuKlJiR600lQWRxgBIY27JZg80f7V9jtMfbNDaQ?e=TBFBVW
echo.
echo After download:
echo   1. Rename to: wav2lip.pth
echo   2. Place in: %PROJECT_ROOT%models\
echo   3. Run this script again
echo.

set /p "DOWNLOADED=Have you downloaded the model? (y/n): "

setlocal enabledelayedexpansion
if /i "!DOWNLOADED!"=="y" (
    endlocal
    echo.
    echo Please place wav2lip.pth in: %PROJECT_ROOT%models\
    echo Then run this script again.
    echo.
) else (
    endlocal
    echo.
    echo Please download the model first, then run this script again.
    echo.
)

pause
exit /b 0

:SETUP_AVATAR
REM Check if avatar data exists
echo.
echo ============================================================
echo   Checking Avatar Data
echo ============================================================
echo.

if not exist "%PROJECT_ROOT%data" (
    echo Creating data directory...
    mkdir "%PROJECT_ROOT%data"
)

if not exist "%PROJECT_ROOT%data\avatars" (
    echo Creating avatars directory...
    mkdir "%PROJECT_ROOT%data\avatars"
)

REM Check if avatar exists in external/livetalking
if exist "%PROJECT_ROOT%external\livetalking\data\avatars\wav2lip256_avatar1" (
    echo Found avatar in LiveTalking directory!
    echo.
    set /p "COPY_AVATAR=Copy avatar to project data directory? (y/n): "
    
    setlocal enabledelayedexpansion
    if /i "!COPY_AVATAR!"=="y" (
        endlocal
        echo.
        echo Copying avatar...
        xcopy "%PROJECT_ROOT%external\livetalking\data\avatars\wav2lip256_avatar1" "%PROJECT_ROOT%data\avatars\wav2lip256_avatar1\" /E /I /Y
        if %errorlevel% equ 0 (
            echo [OK] Avatar copied successfully!
        ) else (
            echo [WARN] Failed to copy avatar
        )
    ) else (
        endlocal
    )
)

if exist "%PROJECT_ROOT%data\avatars\wav2lip256_avatar1" (
    echo [OK] Avatar data exists
) else (
    echo.
    echo [INFO] Avatar data not found
    echo.
    echo Download avatar data from:
    echo   - Quark: https://pan.quark.cn/s/83a750323ef0
    echo   - Google Drive: https://drive.google.com/drive/folders/1FOC_MD6wdogyyX_7V1d4NDIO7P9NlSAJ
    echo.
    echo Extract wav2lip256_avatar1.tar.gz to:
    echo   %PROJECT_ROOT%data\avatars\
    echo.
)

echo.
echo ============================================================
echo   Setup Complete!
echo ============================================================
echo.

if exist "%PROJECT_ROOT%models\wav2lip.pth" (
    echo [OK] Model: wav2lip.pth
) else (
    echo [MISSING] Model: wav2lip.pth
)

if exist "%PROJECT_ROOT%data\avatars\wav2lip256_avatar1" (
    echo [OK] Avatar: wav2lip256_avatar1
) else (
    echo [MISSING] Avatar: wav2lip256_avatar1
)

echo.
echo Next steps:
echo   1. If model is missing, download it (see instructions above)
echo   2. If avatar is missing, download it (optional for testing)
echo   3. Run: run_livetalking_web.bat
echo.

pause
