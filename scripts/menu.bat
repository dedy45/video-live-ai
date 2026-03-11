@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1

pushd "%~dp0.."
set "PROJECT_DIR=%CD%"
popd

set "PYTHONUTF8=1"

where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] uv not found in PATH.
    echo         Install UV first, then run this menu again.
    echo.
    pause
    exit /b 1
)

:menu
cls
echo.
echo  +==============================================================+
echo  ^|        AI LIVE COMMERCE -- UNIFIED OPERATOR MENU            ^|
echo  +==============================================================+
echo  ^|                                                              ^|
echo  ^|   SETUP                                                      ^|
echo  ^|   [1] Setup All ^(App + LiveTalking + MuseTalk + Fish-Speech^) ^|
echo  ^|   [2] Setup App                                               ^|
echo  ^|   [3] Setup LiveTalking                                       ^|
echo  ^|   [4] Setup MuseTalk Model                                    ^|
echo  ^|   [5] Setup Fish-Speech                                       ^|
echo  ^|                                                              ^|
echo  ^|   START / STOP                                               ^|
echo  ^|   [6] Start App ^(Real Mode^)                                 ^|
echo  ^|   [7] Start LiveTalking ^(MuseTalk^)                          ^|
echo  ^|   [8] Start Fish-Speech                                       ^|
echo  ^|   [9] Stop All                                                ^|
echo  ^|                                                              ^|
echo  ^|   STATUS / HEALTH                                            ^|
echo  ^|   [10] Status All                                             ^|
echo  ^|   [11] Status Fish-Speech                                     ^|
echo  ^|   [12] Health Summary                                         ^|
echo  ^|   [13] Tail Logs                                              ^|
echo  ^|                                                              ^|
echo  ^|   VALIDATE                                                   ^|
echo  ^|   [14] Validate All                                           ^|
echo  ^|   [15] Validate Readiness                                     ^|
echo  ^|   [16] Validate LiveTalking                                   ^|
echo  ^|   [17] Validate Fish-Speech                                   ^|
echo  ^|                                                              ^|
echo  ^|   OPEN                                                       ^|
echo  ^|   [18] Open Dashboard                                         ^|
echo  ^|   [19] Open Performer                                         ^|
echo  ^|   [20] Open Monitor                                           ^|
echo  ^|   [21] Open Vendor                                            ^|
echo  ^|                                                              ^|
echo  ^|   [0] Exit                                                   ^|
echo  +==============================================================+
echo.
set /p CHOICE="  Select option: "

if "%CHOICE%"=="1"  goto setup_all
if "%CHOICE%"=="2"  goto setup_app
if "%CHOICE%"=="3"  goto setup_livetalking
if "%CHOICE%"=="4"  goto setup_musetalk
if "%CHOICE%"=="5"  goto setup_fish_speech
if "%CHOICE%"=="6"  goto start_app_real
if "%CHOICE%"=="7"  goto start_livetalking_musetalk
if "%CHOICE%"=="8"  goto start_fish_speech
if "%CHOICE%"=="9"  goto stop_all
if "%CHOICE%"=="10" goto status_all
if "%CHOICE%"=="11" goto status_fish_speech
if "%CHOICE%"=="12" goto health_summary
if "%CHOICE%"=="13" goto tail_logs
if "%CHOICE%"=="14" goto validate_all
if "%CHOICE%"=="15" goto validate_readiness
if "%CHOICE%"=="16" goto validate_livetalking
if "%CHOICE%"=="17" goto validate_fish_speech
if "%CHOICE%"=="18" goto open_dashboard
if "%CHOICE%"=="19" goto open_performer
if "%CHOICE%"=="20" goto open_monitor
if "%CHOICE%"=="21" goto open_vendor
if "%CHOICE%"=="0"  goto exit_menu

echo Invalid option, try again.
timeout /t 2 >nul
goto menu

:setup_all
call :section "Setup All"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup all
pause
goto menu

:setup_app
call :section "Setup App"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup app
pause
goto menu

:setup_livetalking
call :section "Setup LiveTalking"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup livetalking
pause
goto menu

:setup_musetalk
call :section "Setup MuseTalk Model"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup musetalk-model
pause
goto menu

:setup_fish_speech
call :section "Setup Fish-Speech"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup fish-speech
pause
goto menu

:start_app_real
call :section "Start App Real Mode"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py serve --real
pause
goto menu

:start_livetalking_musetalk
call :section "Start LiveTalking MuseTalk"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py start livetalking --mode musetalk
pause
goto menu

:start_fish_speech
call :section "Start Fish-Speech"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py start fish-speech
pause
goto menu

:stop_all
call :section "Stop All"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py stop all
pause
goto menu

:status_all
call :section "Status All"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py status all
pause
goto menu

:status_fish_speech
call :section "Status Fish-Speech"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py status fish-speech
pause
goto menu

:health_summary
call :section "Health Summary"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py health
pause
goto menu

:tail_logs
call :section "Tail Logs"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py logs --lines 30
pause
goto menu

:validate_all
call :section "Validate All"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate all
pause
goto menu

:validate_readiness
call :section "Validate Readiness"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate readiness
pause
goto menu

:validate_livetalking
call :section "Validate LiveTalking"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate livetalking
pause
goto menu

:validate_fish_speech
call :section "Validate Fish-Speech"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate fish-speech
pause
goto menu

:open_dashboard
call :section "Open Dashboard"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open dashboard
pause
goto menu

:open_performer
call :section "Open Performer"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open performer
pause
goto menu

:open_monitor
call :section "Open Monitor"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open monitor
pause
goto menu

:open_vendor
call :section "Open Vendor"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open vendor
pause
goto menu

:exit_menu
echo.
echo Goodbye!
exit /b 0

:section
echo.
echo ======================================================
echo   %~1
echo ======================================================
echo.
goto :eof
