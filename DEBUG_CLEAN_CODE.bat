@echo off
REM ========================================
REM Debug Clean Code - 4 Providers Only
REM ========================================
REM
REM Providers yang DISIMPAN:
REM   - groq (Groq Llama 3.3)
REM   - gemini (Google Gemini 2.0)
REM   - claude (Anthropic Claude)
REM   - gpt4o (OpenAI GPT-4o)
REM
REM Providers yang DIHAPUS:
REM   - chutes (latency besar)
REM   - gemini_local_* (latency besar)
REM   - claude_local (latency besar)
REM   - gpt4o_local (latency besar)
REM   - local (latency besar)
REM ========================================

echo.
echo ========================================
echo STEP 1: SYNTAX CHECK
echo ========================================
echo.

python -m py_compile src/brain/router.py
if errorlevel 1 (
    echo [ERROR] Syntax error in router.py!
    pause
    exit /b 1
)
echo [OK] Syntax check passed

echo.
echo ========================================
echo STEP 2: STOP OLD SERVER
echo ========================================
echo.

taskkill /F /IM python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
echo [OK] Server stopped

echo.
echo ========================================
echo STEP 3: CLEAR LOGS
echo ========================================
echo.

if exist "tmp-dashboard-8011.log" del /F /Q "tmp-dashboard-8011.log"
if exist "tmp-dashboard-8011-error.log" del /F /Q "tmp-dashboard-8011-error.log"
echo [OK] Logs cleared

echo.
echo ========================================
echo STEP 4: START SERVER
echo ========================================
echo.

start /B python src/main.py > tmp-dashboard-8011.log 2>&1
echo [OK] Server starting...
timeout /t 10 /nobreak >nul

echo.
echo ========================================
echo STEP 5: CHECK LOADED ADAPTERS
echo ========================================
echo.

powershell -Command "Select-String -Path 'tmp-dashboard-8011.log' -Pattern 'adapter_loaded|adapter_skipped' | ForEach-Object { $_.Line }"

echo.
echo ========================================
echo STEP 6: CHECK ADAPTERS BUILD COMPLETE
echo ========================================
echo.

powershell -Command "Select-String -Path 'tmp-dashboard-8011.log' -Pattern 'adapters_build_complete' | ForEach-Object { $_.Line }"

echo.
echo ========================================
echo STEP 7: TEST BRAIN HEALTH API
echo ========================================
echo.

timeout /t 3 /nobreak >nul
powershell -Command "$response = Invoke-WebRequest -Uri 'http://localhost:8001/api/brain/health' -Method GET -TimeoutSec 15; $json = $response.Content | ConvertFrom-Json; Write-Host ''; Write-Host 'Providers loaded:'; $json.providers.PSObject.Properties | ForEach-Object { Write-Host \"  - $($_.Name): $($_.Value)\" }; Write-Host ''; Write-Host \"Total: $($json.healthy_count)/$($json.total_count)\"; Write-Host \"Current: $($json.current_provider)\"; Write-Host ''"

echo.
echo ========================================
echo STEP 8: CHECK FOR ERRORS
echo ========================================
echo.

if exist "tmp-dashboard-8011-error.log" (
    echo Checking error log...
    powershell -Command "Get-Content 'tmp-dashboard-8011-error.log' | Select-Object -Last 20"
) else (
    echo [OK] No error log found
)

echo.
echo ========================================
echo STEP 9: VERIFY CLEAN CODE
echo ========================================
echo.

echo Checking for removed adapters in logs...
powershell -Command "$log = Get-Content 'tmp-dashboard-8011.log' -Raw; $removed = @('chutes', 'gemini_local', 'claude_local', 'gpt4o_local', 'local'); $found = $false; foreach ($name in $removed) { if ($log -match $name) { Write-Host \"[WARNING] Found '$name' in logs!\"; $found = $true } }; if (-not $found) { Write-Host '[OK] No removed adapters found in logs' }"

echo.
echo ========================================
echo DEBUGGING COMPLETE!
echo ========================================
echo.
echo Expected result:
echo   - Only 4 adapters loaded: groq, gemini, claude, gpt4o
echo   - No chutes, gemini_local_*, claude_local, gpt4o_local, local
echo   - Current provider: groq
echo.
echo Open dashboard: http://localhost:8001/dashboard/#/monitor
echo.
pause
