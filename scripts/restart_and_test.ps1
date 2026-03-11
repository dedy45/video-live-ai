#!/usr/bin/env pwsh
# Restart server and test monitor performance

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RESTARTING SERVER WITH FIX" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Kill old Python processes running main.py
Write-Host "Stopping old server processes..." -ForegroundColor Yellow
Get-Process | Where-Object {
    $_.ProcessName -eq "python" -and 
    $_.CommandLine -like "*main.py*"
} | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

# Start new server in background
Write-Host "Starting new server..." -ForegroundColor Yellow
$serverJob = Start-Job -ScriptBlock {
    Set-Location "C:\Users\dedy\Documents\!fast-track-income\videoliveai"
    python src/main.py
}

Write-Host "Waiting for server to start (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test if server is up
Write-Host "`nTesting server health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/api/status" -Method GET -TimeoutSec 5
    Write-Host "✓ Server is UP (Status: $($response.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "✗ Server not responding yet" -ForegroundColor Red
    Write-Host "Waiting 10 more seconds..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

# Run performance test
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "RUNNING PERFORMANCE TEST" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

python test_monitor_api.py

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "TEST COMPLETE" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Server is running in background (Job ID: $($serverJob.Id))" -ForegroundColor Yellow
Write-Host "To stop server: Stop-Job -Id $($serverJob.Id); Remove-Job -Id $($serverJob.Id)" -ForegroundColor Yellow
Write-Host "To view logs: Receive-Job -Id $($serverJob.Id) -Keep" -ForegroundColor Yellow
