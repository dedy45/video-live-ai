#!/usr/bin/env pwsh
# ============================================================
# Deep Clean - Clear ALL caches and temporary files
# ============================================================

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DEEP CLEAN - CLEARING ALL CACHES" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "SilentlyContinue"

# ── Step 1: Kill all Python processes ──────────────────────
Write-Host "[1/10] Stopping all Python processes..." -ForegroundColor Yellow
Get-Process python* | Stop-Process -Force
Start-Sleep -Seconds 2
Write-Host "       Done!" -ForegroundColor Green

# ── Step 2: Clear Python cache ─────────────────────────────
Write-Host "[2/10] Clearing Python __pycache__..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force
Write-Host "       Done!" -ForegroundColor Green

# ── Step 3: Clear Python .pytest_cache ─────────────────────
Write-Host "[3/10] Clearing pytest cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter ".pytest_cache" | Remove-Item -Recurse -Force
Write-Host "       Done!" -ForegroundColor Green

# ── Step 4: Clear .hypothesis cache ────────────────────────
Write-Host "[4/10] Clearing hypothesis cache..." -ForegroundColor Yellow
Get-ChildItem -Path . -Recurse -Directory -Filter ".hypothesis" | Remove-Item -Recurse -Force
Write-Host "       Done!" -ForegroundColor Green

# ── Step 5: Clear frontend node_modules cache ──────────────
Write-Host "[5/10] Clearing frontend Vite cache..." -ForegroundColor Yellow
if (Test-Path "src\dashboard\frontend\node_modules\.vite") {
    Remove-Item -Path "src\dashboard\frontend\node_modules\.vite" -Recurse -Force
}
Write-Host "       Done!" -ForegroundColor Green

# ── Step 6: Clear frontend build ───────────────────────────
Write-Host "[6/10] Clearing frontend dist..." -ForegroundColor Yellow
if (Test-Path "src\dashboard\frontend\dist") {
    Remove-Item -Path "src\dashboard\frontend\dist" -Recurse -Force
}
Write-Host "       Done!" -ForegroundColor Green

# ── Step 7: Clear browser cache (Chrome) ───────────────────
Write-Host "[7/10] Clearing Chrome cache..." -ForegroundColor Yellow
$chromeCachePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $chromeCachePath) {
    Remove-Item -Path $chromeCachePath -Recurse -Force
}
$chromeCodeCachePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Code Cache"
if (Test-Path $chromeCodeCachePath) {
    Remove-Item -Path $chromeCodeCachePath -Recurse -Force
}
Write-Host "       Done!" -ForegroundColor Green

# ── Step 8: Clear browser cache (Edge) ─────────────────────
Write-Host "[8/10] Clearing Edge cache..." -ForegroundColor Yellow
$edgeCachePath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Cache"
if (Test-Path $edgeCachePath) {
    Remove-Item -Path $edgeCachePath -Recurse -Force
}
$edgeCodeCachePath = "$env:LOCALAPPDATA\Microsoft\Edge\User Data\Default\Code Cache"
if (Test-Path $edgeCodeCachePath) {
    Remove-Item -Path $edgeCodeCachePath -Recurse -Force
}
Write-Host "       Done!" -ForegroundColor Green

# ── Step 9: Clear temp logs ────────────────────────────────
Write-Host "[9/10] Clearing temp logs..." -ForegroundColor Yellow
Get-ChildItem -Path . -File -Filter "*.log" | Where-Object { $_.Name -like "tmp-*" } | Remove-Item -Force
Write-Host "       Done!" -ForegroundColor Green

# ── Step 10: Rebuild frontend ──────────────────────────────
Write-Host "[10/10] Rebuilding frontend..." -ForegroundColor Yellow
Push-Location "src\dashboard\frontend"
npm run build | Out-Null
Pop-Location
Write-Host "        Done!" -ForegroundColor Green

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "DEEP CLEAN COMPLETE!" -ForegroundColor Green
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run: .\quick_restart.bat" -ForegroundColor White
Write-Host "  2. Wait 10 seconds for server to start" -ForegroundColor White
Write-Host "  3. Open: http://localhost:8001/dashboard/#/monitor" -ForegroundColor White
Write-Host "  4. Test: .\test_performance.bat`n" -ForegroundColor White

$ErrorActionPreference = "Continue"
