@echo off
chcp 65001 >nul 2>&1

REM ============================================================
REM  AI Live Commerce — Full Validation Pipeline
REM  Runs all checks: env, deps, config, imports, lint, tests, verify, db
REM ============================================================

set "PROJECT_DIR=C:\Users\dedy\Documents\!fast-track-income\videoliveai"
cd /d %~dp0\..\
set "PROJECT_DIR=%CD%"
set "MOCK_MODE=true"
set "PYTHONUTF8=1"
set "PYTHON=%PROJECT_DIR%\.venv\Scripts\python.exe"

set PASS=0
set FAIL=0
set WARN=0
set TOTAL=0

echo.
echo ============================================================
echo   AI Live Commerce — Full Validation Pipeline
echo   %date% %time%
echo ============================================================
echo.

REM ── Step 0: Check venv ──────────────────────────────────────
call :header "0/8 Virtual Environment Check"
if exist "%PYTHON%" (
    call :pass "venv found at .venv\"
    for /f %%V in ('"%PYTHON%" --version 2^>^&1') do set "PYVER=%%V"
    call :pass "Python: !PYVER!"
) else (
    call :fail "venv not found — run 'uv sync --extra dev' first"
    echo.
    echo   Cannot continue without venv. Exiting.
    exit /b 1
)
echo.

REM ── Step 1: Environment ─────────────────────────────────────
call :header "1/8 Environment Check"
call :check_cmd "UV" "uv --version"
call :check_file ".env" "%PROJECT_DIR%\.env"
call :check_file "config.yaml" "%PROJECT_DIR%\config\config.yaml"
call :check_file "pyproject.toml" "%PROJECT_DIR%\pyproject.toml"
echo.

REM ── Step 2: Dependencies ────────────────────────────────────
call :header "2/8 Dependency Sync"
uv sync --extra dev >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "Dependencies synced (dev)"
) else (
    call :warn "uv sync partial — check betterproto/platform deps (non-blocking)"
)
echo.

REM ── Step 3: Config Validation ───────────────────────────────
call :header "3/8 Config Validation"
"%PYTHON%" -c "import sys; sys.path.insert(0,'.'); from src.config.loader import load_config, load_env; c=load_config(); e=load_env(); print('  App:', c.app.name, 'v' + c.app.version); print('  Composition:', str(c.composition.resolution) + ' @ ' + str(c.composition.fps) + 'fps'); print('  LLM budget: $' + str(c.llm_providers.daily_budget_usd) + '/day'); print('  Mock Mode:', e.mock_mode)" 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "Config + EnvSettings loaded successfully"
) else (
    call :fail "Config loading failed"
)
echo.

REM ── Step 4: Import Check ────────────────────────────────────
call :header "4/8 Module Import Check"
set MODULES=src.config src.data.database src.brain.router src.brain.persona src.brain.safety src.voice.engine src.face.pipeline src.composition.compositor src.stream.rtmp src.chat.monitor src.commerce.manager src.commerce.analytics src.orchestrator.state_machine src.dashboard.api src.dashboard.diagnostic src.utils.health src.utils.logging src.utils.mock_mode
for %%M in (%MODULES%) do (
    "%PYTHON%" -c "import %%M" >nul 2>&1 && call :pass "%%M" || call :fail "%%M ^-^- import failed"
)
echo.

REM ── Step 5: Linting ─────────────────────────────────────────
call :header "5/8 Linting (Ruff)"
"%PYTHON%" -m ruff check src/ --select E,F --quiet 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "Ruff: no critical errors (E/F)"
) else (
    call :warn "Ruff found issues (non-blocking — fix with: %PYTHON% -m ruff check src/ --fix)"
)
echo.

REM ── Step 6: Unit Tests ──────────────────────────────────────
call :header "6/8 Unit Tests (pytest)"
set MOCK_MODE=true
"%PYTHON%" -m pytest tests/ --tb=short --no-header -q 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "All tests passed"
) else (
    call :fail "Some tests failed — check output above"
)
echo.

REM ── Step 7: Pipeline Verification ───────────────────────────
call :header "7/8 Pipeline Verification (11 layers)"
set MOCK_MODE=true
"%PYTHON%" scripts/verify_pipeline.py 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "Pipeline verification passed"
) else (
    call :fail "Pipeline verification found failures — check output above"
)
echo.

REM ── Step 8: Database Health ─────────────────────────────────
call :header "8/8 Database Health"
"%PYTHON%" -c "import sys; sys.path.insert(0,'.'); from src.data.database import init_database, check_database_health; init_database(); h=check_database_health(); print('  Healthy:', h['healthy']); print('  Tables: ', h['tables']); print('  Message:', h['message'])" 2>&1
if %ERRORLEVEL% EQU 0 (
    call :pass "Database healthy"
) else (
    call :fail "Database check failed"
)
echo.

REM ── Summary ─────────────────────────────────────────────────
echo ============================================================
echo   VALIDATION SUMMARY
echo ============================================================
echo.
echo   Total checks:  %TOTAL%
echo   Passed:        %PASS%
echo   Failed:        %FAIL%
echo   Warnings:      %WARN%
echo.
if "%FAIL%"=="0" (
    echo   *** ALL CHECKS PASSED ***
    echo.
    echo ============================================================
    exit /b 0
) else (
    echo   *** %FAIL% CHECK^(S^) FAILED — See details above ***
    echo.
    echo ============================================================
    exit /b 1
)

REM ── Helper functions ────────────────────────────────────────
:header
echo ──────────────────────────────────────────────────
echo   %~1
echo ──────────────────────────────────────────────────
goto :eof

:pass
set /a TOTAL+=1
set /a PASS+=1
echo   [PASS] %~1
goto :eof

:fail
set /a TOTAL+=1
set /a FAIL+=1
echo   [FAIL] %~1
goto :eof

:warn
set /a TOTAL+=1
set /a WARN+=1
echo   [WARN] %~1
goto :eof

:check_cmd
%~2 >nul 2>&1
if errorlevel 1 goto check_cmd_fail
for /f "delims=" %%V in ('%~2 2^>^&1') do set "VER=%%V"
call :pass "%~1 — %VER%"
goto :eof
:check_cmd_fail
call :fail "%~1 — not found"
goto :eof

:check_file
if exist "%~2" (
    call :pass "%~1 exists"
) else (
    call :fail "%~1 missing at %~2"
)
goto :eof

