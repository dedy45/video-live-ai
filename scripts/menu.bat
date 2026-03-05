@echo off
chcp 65001 >nul 2>&1

REM ============================================================
REM  AI Live Commerce -- Node Controller Menu v0.5.1
REM  PID-based start/stop, LLM test, full validation
REM  FIX: delayed expansion disabled at top level to prevent
REM       ! character in path (e.g. !fast-track-income) breaking cd
REM ============================================================

REM -- Resolve project root (parent of scripts\)
pushd "%~dp0.."
set "PROJECT_DIR=%CD%"
popd

set "PID_FILE=%PROJECT_DIR%\data\.server.pid"
set "PYTHONUTF8=1"
set "PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"
set "LOG_DIR=%PROJECT_DIR%\data\logs"

REM --- Verify venv exists
if not exist "%PYTHON%" (
    echo.
    echo   [ERROR] Virtual environment not found!
    echo   Expected: %PYTHON%
    echo   Run: uv sync --extra dev
    echo.
    pause & exit /b 1
)

:menu
cls
echo.
echo  +======================================================+
echo  ^|     AI LIVE COMMERCE -- NODE CONTROLLER v0.5.1      ^|
echo  +======================================================+
echo  ^|                                                      ^|
echo  ^|   SERVER                                             ^|
echo  ^|   [1] Start Server (Mock Mode - no GPU needed)      ^|
echo  ^|   [2] Start Server (Production Mode)                ^|
echo  ^|   [3] Stop Server  (safe PID-based)                 ^|
echo  ^|   [4] Server Status + Last Logs                     ^|
echo  ^|                                                      ^|
echo  ^|   LLM TEST                                           ^|
echo  ^|   [5] Test LLM - Auto Route                         ^|
echo  ^|   [6] Test LLM - Local Gemini Flash (8091)          ^|
echo  ^|   [7] Test LLM - Groq                               ^|
echo  ^|   [8] Test LLM - Chutes                             ^|
echo  ^|   [9] Test ALL Providers                            ^|
echo  ^|                                                      ^|
echo  ^|   VALIDATION                                         ^|
echo  ^|   [10] Run Unit Tests (66 tests)                    ^|
echo  ^|   [11] Run Pipeline Verification                    ^|
echo  ^|   [12] Run Linting (Ruff)                           ^|
echo  ^|                                                      ^|
echo  ^|   DATABASE                                           ^|
echo  ^|   [13] Database Health Check                        ^|
echo  ^|   [14] Reset Database                               ^|
echo  ^|                                                      ^|
echo  ^|   DASHBOARD                                          ^|
echo  ^|   [15] Open Dashboard (Browser)                     ^|
echo  ^|   [16] Open API Docs (Browser)                      ^|
echo  ^|   [17] Health Check via API                         ^|
echo  ^|                                                      ^|
echo  ^|   TOOLS                                              ^|
echo  ^|   [18] Sync Dependencies                            ^|
echo  ^|   [19] Check Config + Env Keys                      ^|
echo  ^|   [20] Check Module Imports                         ^|
echo  ^|   [21] View Logs (tail)                             ^|
echo  ^|   [22] Clean Cache / Temp Files                     ^|
echo  ^|                                                      ^|
echo  ^|   [0] Exit                                          ^|
echo  +======================================================+
echo.
set /p CHOICE="  Select option: "

if "%CHOICE%"=="1"  goto start_mock
if "%CHOICE%"=="2"  goto start_prod
if "%CHOICE%"=="3"  goto stop_server
if "%CHOICE%"=="4"  goto server_status
if "%CHOICE%"=="5"  goto llm_auto
if "%CHOICE%"=="6"  goto llm_local
if "%CHOICE%"=="7"  goto llm_groq
if "%CHOICE%"=="8"  goto llm_chutes
if "%CHOICE%"=="9"  goto llm_all
if "%CHOICE%"=="10" goto tests
if "%CHOICE%"=="11" goto verify
if "%CHOICE%"=="12" goto lint
if "%CHOICE%"=="13" goto db_health
if "%CHOICE%"=="14" goto db_reset
if "%CHOICE%"=="15" goto open_dashboard
if "%CHOICE%"=="16" goto open_docs
if "%CHOICE%"=="17" goto health_check
if "%CHOICE%"=="18" goto sync_dev
if "%CHOICE%"=="19" goto check_config
if "%CHOICE%"=="20" goto check_imports
if "%CHOICE%"=="21" goto view_logs
if "%CHOICE%"=="22" goto clean
if "%CHOICE%"=="0"  goto exit_menu

echo   Invalid option, try again.
timeout /t 2 >nul
goto menu

REM ======================================================
REM  SERVER
REM ======================================================

:start_mock
call :section "Starting Server (Mock Mode)"
call :check_port_free
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo @echo off                                      > "%LOG_DIR%\_launcher.bat"
echo set "MOCK_MODE=true"                          >> "%LOG_DIR%\_launcher.bat"
echo set "PYTHONUTF8=1"                            >> "%LOG_DIR%\_launcher.bat"
echo cd /d "%PROJECT_DIR%"                         >> "%LOG_DIR%\_launcher.bat"
echo "%PYTHON%" -m src.main                        >> "%LOG_DIR%\_launcher.bat"
start "AI-Live-Commerce" cmd /c ""%LOG_DIR%\_launcher.bat" >> "%LOG_DIR%\server.log" 2>&1"
echo   Server starting... waiting 6 seconds...
timeout /t 6 >nul
call :check_server_running
pause
goto menu

:start_prod
call :section "Starting Server (Production Mode)"
call :check_port_free
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
echo @echo off                                      > "%LOG_DIR%\_launcher.bat"
echo set "MOCK_MODE=false"                         >> "%LOG_DIR%\_launcher.bat"
echo set "PYTHONUTF8=1"                            >> "%LOG_DIR%\_launcher.bat"
echo cd /d "%PROJECT_DIR%"                         >> "%LOG_DIR%\_launcher.bat"
echo "%PYTHON%" -m src.main                        >> "%LOG_DIR%\_launcher.bat"
start "AI-Live-Commerce" cmd /c ""%LOG_DIR%\_launcher.bat" >> "%LOG_DIR%\server.log" 2>&1"
echo   Server starting... waiting 6 seconds...
timeout /t 6 >nul
call :check_server_running
pause
goto menu

:stop_server
call :section "Stopping Server"
REM Method 1: kill via PID file (pakai powershell untuk baca PID — aman dari ! expansion)
if exist "%PID_FILE%" (
    echo   Killing process from PID file...
    powershell -command "Stop-Process -Id (Get-Content '%PID_FILE%') -Force -ErrorAction SilentlyContinue"
    del "%PID_FILE%" >nul 2>&1
    echo   [OK] Process killed via PID file.
) else (
    echo   No PID file found, scanning port 8000...
)
REM Method 2: kill by port (backup)
for /f "tokens=5" %%P in ('netstat -aon 2^>nul ^| findstr ":8000 " ^| findstr "LISTENING"') do (
    echo   Killing PID %%P on port 8000...
    taskkill /f /pid %%P >nul 2>&1
)
timeout /t 2 >nul
netstat -aon 2>nul | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo   [OK] Server stopped.
) else (
    echo   [!!] Port still in use. May be TIME_WAIT state (normal, will clear in ~60s).
)
pause
goto menu

:server_status
call :section "Server Status"
netstat -aon 2>nul | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [RUNNING] Port 8000 is active
    echo.
    curl -s --max-time 3 http://localhost:8000/ 2>nul
    echo.
) else (
    echo   [STOPPED] No server on port 8000
)
echo.
echo   Last 15 lines of server.log:
if exist "%LOG_DIR%\server.log" (
    powershell -command "Get-Content '%LOG_DIR%\server.log' -Tail 15"
) else (
    echo   No server.log found.
)
pause
goto menu

REM ======================================================
REM  LLM TESTS
REM ======================================================

:llm_auto
call :section "Test LLM - Auto Route"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys,asyncio; sys.path.insert(0,'.'); exec(open('scripts/_llm_test.py').read())" auto
pause
goto menu

:llm_local
call :section "Test LLM - Local Gemini Flash (localhost:8091)"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys,asyncio; sys.path.insert(0,'.'); exec(open('scripts/_llm_test.py').read())" gemini_local_flash
pause
goto menu

:llm_groq
call :section "Test LLM - Groq"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys,asyncio; sys.path.insert(0,'.'); exec(open('scripts/_llm_test.py').read())" groq
pause
goto menu

:llm_chutes
call :section "Test LLM - Chutes (MiniMax M2.5-TEE)"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys,asyncio; sys.path.insert(0,'.'); exec(open('scripts/_llm_test.py').read())" chutes
pause
goto menu

:llm_all
call :section "Test ALL LLM Providers"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys,asyncio; sys.path.insert(0,'.'); exec(open('scripts/_llm_test.py').read())" all
pause
goto menu

REM ======================================================
REM  VALIDATION
REM ======================================================

:tests
call :section "Running Unit Tests (66 tests expected)"
cd /d "%PROJECT_DIR%"
set "MOCK_MODE=true"
"%PYTHON%" -m pytest tests/ --ignore=tests/test_property.py -v --tb=short
pause
goto menu

:verify
call :section "Pipeline Verification (11 layers)"
cd /d "%PROJECT_DIR%"
set "MOCK_MODE=true"
"%PYTHON%" scripts/verify_pipeline.py --verbose
pause
goto menu

:lint
call :section "Running Linting (Ruff)"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -m ruff check src/ --select E,F,I,N,W,UP
echo.
"%PYTHON%" -m ruff format --check src/ 2>nul
if %ERRORLEVEL% EQU 0 (echo   Formatting: OK) else (echo   Formatting: needs fix)
pause
goto menu

REM ======================================================
REM  DATABASE
REM ======================================================

:db_health
call :section "Database Health Check"
cd /d "%PROJECT_DIR%"
"%PYTHON%" -c "import sys; sys.path.insert(0,'.'); from src.data.database import init_database, check_database_health; init_database(); h=check_database_health(); print('  Healthy:', h['healthy']); print('  Tables: ', h['tables']); print('  Message:', h['message'])"
pause
goto menu

:db_reset
call :section "Reset Database"
echo   WARNING: This will DELETE the existing database!
set /p CONFIRM="  Type 'yes' to confirm: "
if /i "%CONFIRM%"=="yes" (
    if exist "%PROJECT_DIR%\data\commerce.db" del "%PROJECT_DIR%\data\commerce.db"
    cd /d "%PROJECT_DIR%"
    "%PYTHON%" -c "import sys; sys.path.insert(0,'.'); from src.data.database import init_database; init_database(); print('  Database re-initialized OK.')"
) else (
    echo   Cancelled.
)
pause
goto menu

REM ======================================================
REM  DASHBOARD
REM ======================================================

:open_dashboard
call :section "Opening Dashboard"
start "" "http://localhost:8000/dashboard/"
echo   http://localhost:8000/dashboard/
pause
goto menu

:open_docs
call :section "Opening API Docs"
start "" "http://localhost:8000/docs"
echo   http://localhost:8000/docs
pause
goto menu

:health_check
call :section "Health Check via API"
echo   /diagnostic/ :
curl -s --max-time 5 http://localhost:8000/diagnostic/ 2>nul
echo.
echo.
echo   /api/status :
curl -s --max-time 5 http://localhost:8000/api/status 2>nul
echo.
pause
goto menu

REM ======================================================
REM  TOOLS
REM ======================================================

:sync_dev
call :section "Syncing Dependencies"
cd /d "%PROJECT_DIR%"
uv sync --extra dev
echo.
"%PYTHON%" -m pip install litellm --quiet
echo   litellm: OK
pause
goto menu

:check_config
call :section "Config + Env Keys Check"
cd /d "%PROJECT_DIR%"
"%PYTHON%" scripts\_check_config.py
pause
goto menu

:check_imports
call :section "Module Import Check"
cd /d "%PROJECT_DIR%"
echo   Testing core modules...
for %%M in (src.config src.data.database src.brain.router src.brain.adapters.litellm_adapter src.brain.persona src.brain.safety src.voice.engine src.face.pipeline src.composition.compositor src.stream.rtmp src.commerce.manager src.commerce.analytics src.orchestrator.state_machine src.dashboard.api src.dashboard.diagnostic src.utils.health src.utils.logging src.utils.mock_mode) do (
    "%PYTHON%" -c "import sys; sys.path.insert(0,'.'); import %%M" >nul 2>&1 && echo   [OK] %%M || echo   [!!] %%M -- FAILED
)
echo.
"%PYTHON%" -c "import litellm; print('  [OK] litellm', litellm.__version__)"
pause
goto menu

:view_logs
call :section "Recent Logs"
if exist "%LOG_DIR%\server.log" (
    echo   Last 30 lines of server.log:
    powershell -command "Get-Content '%LOG_DIR%\server.log' -Tail 30"
) else (
    echo   No server.log found.
)
echo.
if exist "%PROJECT_DIR%\data\logs\app.log" (
    echo   Last 15 lines of app.log:
    powershell -command "Get-Content '%PROJECT_DIR%\data\logs\app.log' -Tail 15"
)
pause
goto menu

:clean
call :section "Cleaning Cache and Temp Files"
for /d /r "%PROJECT_DIR%\src" %%D in (__pycache__) do if exist "%%D" rd /s /q "%%D" >nul 2>&1
for /d /r "%PROJECT_DIR%\tests" %%D in (__pycache__) do if exist "%%D" rd /s /q "%%D" >nul 2>&1
if exist "%PROJECT_DIR%\.pytest_cache" rd /s /q "%PROJECT_DIR%\.pytest_cache" >nul 2>&1
if exist "%PROJECT_DIR%\.ruff_cache" rd /s /q "%PROJECT_DIR%\.ruff_cache" >nul 2>&1
if exist "%LOG_DIR%\_launcher.bat" del "%LOG_DIR%\_launcher.bat" >nul 2>&1
echo   Done.
pause
goto menu

REM ======================================================
REM  EXIT
REM ======================================================

:exit_menu
echo.
echo   Goodbye!
exit /b 0

REM ======================================================
REM  HELPER SUBROUTINES
REM ======================================================

:section
echo.
echo ======================================================
echo   %~1
echo ======================================================
echo.
goto :eof

:check_port_free
netstat -aon 2>nul | findstr ":8000 " | findstr "LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [WARN] Port 8000 already in use! Stop existing server first with [3].
    pause
)
goto :eof

:check_server_running
curl -s --max-time 5 http://localhost:8000/ >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo   [OK] Server is running!
    echo   Dashboard : http://localhost:8000/dashboard/
    echo   API Docs  : http://localhost:8000/docs
) else (
    echo   [..] Server still starting. Check [4] for status.
    if exist "%LOG_DIR%\server.log" (
        echo   Last 5 lines of server.log:
        powershell -command "Get-Content '%LOG_DIR%\server.log' -Tail 5"
    )
)
goto :eof
