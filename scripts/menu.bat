@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul 2>&1

REM ============================================================
REM  AI Live Commerce -- UV Operator Menu
REM  Windows convenience wrapper over:
REM      uv run python scripts/manage.py <command>
REM ============================================================

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
echo  +======================================================+
echo  ^|       AI LIVE COMMERCE -- UV OPERATOR MENU          ^|
echo  +======================================================+
echo  ^|                                                      ^|
echo  ^|   APP                                                ^|
echo  ^|   [1] Start App ^(Mock Mode^)                         ^|
echo  ^|   [2] Start App ^(Real Mode^)                         ^|
echo  ^|   [3] Stop App                                      ^|
echo  ^|   [4] App Status                                    ^|
echo  ^|   [5] Health Summary                                ^|
echo  ^|                                                      ^|
echo  ^|   VALIDATION                                         ^|
echo  ^|   [6] Run Test Suite                                ^|
echo  ^|   [7] Run Pipeline Verification                     ^|
echo  ^|   [8] Run Real-Mode Readiness Gate                  ^|
echo  ^|   [9] Run LiveTalking Smoke Test                    ^|
echo  ^|                                                      ^|
echo  ^|   LOGS                                               ^|
echo  ^|   [10] Tail Logs                                    ^|
echo  ^|                                                      ^|
echo  ^|   SETUP                                              ^|
echo  ^|   [11] UV Sync ^(Dev^)                               ^|
echo  ^|   [12] Setup LiveTalking ^(UV^)                      ^|
echo  ^|   [13] Load Sample Products                         ^|
echo  ^|                                                      ^|
echo  ^|   OPEN                                               ^|
echo  ^|   [14] Open Dashboard                               ^|
echo  ^|   [15] Open API Docs                                ^|
echo  ^|   [16] Open Vendor Debug                            ^|
echo  ^|                                                      ^|
echo  ^|   [0] Exit                                          ^|
echo  +======================================================+
echo.
set /p CHOICE="  Select option: "

if "%CHOICE%"=="1"  goto start_mock
if "%CHOICE%"=="2"  goto start_real
if "%CHOICE%"=="3"  goto stop_app
if "%CHOICE%"=="4"  goto app_status
if "%CHOICE%"=="5"  goto health_summary
if "%CHOICE%"=="6"  goto validate_tests
if "%CHOICE%"=="7"  goto validate_pipeline
if "%CHOICE%"=="8"  goto validate_readiness
if "%CHOICE%"=="9"  goto validate_livetalking
if "%CHOICE%"=="10" goto tail_logs
if "%CHOICE%"=="11" goto sync_dev
if "%CHOICE%"=="12" goto sync_livetalking
if "%CHOICE%"=="13" goto load_products
if "%CHOICE%"=="14" goto open_dashboard
if "%CHOICE%"=="15" goto open_docs
if "%CHOICE%"=="16" goto open_vendor
if "%CHOICE%"=="0"  goto exit_menu

echo Invalid option, try again.
timeout /t 2 >nul
goto menu

:start_mock
call :section "Start App (Mock Mode)"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py serve --mock
pause
goto menu

:start_real
call :section "Start App (Real Mode)"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py serve --real
pause
goto menu

:stop_app
call :section "Stop App"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py stop
pause
goto menu

:app_status
call :section "App Status"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py status
pause
goto menu

:health_summary
call :section "Health Summary"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py health
pause
goto menu

:validate_tests
call :section "Validation - Test Suite"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate tests
pause
goto menu

:validate_pipeline
call :section "Validation - Pipeline Verification"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate pipeline
pause
goto menu

:validate_readiness
call :section "Validation - Real-Mode Readiness"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate readiness
pause
goto menu

:validate_livetalking
call :section "Validation - LiveTalking Smoke"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py validate livetalking
pause
goto menu

:tail_logs
call :section "Tail Logs"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py logs --lines 30
pause
goto menu

:sync_dev
call :section "Setup - UV Sync (Dev)"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py sync
pause
goto menu

:sync_livetalking
call :section "Setup - LiveTalking (UV)"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py setup-livetalking --skip-models
pause
goto menu

:load_products
call :section "Setup - Load Sample Products"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py load-products
pause
goto menu

:open_dashboard
call :section "Open Dashboard"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open dashboard
pause
goto menu

:open_docs
call :section "Open API Docs"
cd /d "%PROJECT_DIR%"
uv run python scripts/manage.py open docs
pause
goto menu

:open_vendor
call :section "Open Vendor Debug"
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
