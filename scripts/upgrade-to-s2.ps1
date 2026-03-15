# Fish-Speech S2-Pro Upgrade Script for Windows
# Automates upgrade from v1.5 to S2-Pro with Indonesian language support

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Fish-Speech S2-Pro Upgrade Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# FASE 1: System Check
Write-Host "FASE 1: Checking System Requirements" -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Check GPU
try {
    $gpuInfo = nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>$null
    if ($gpuInfo) {
        Write-Host "[OK] NVIDIA GPU detected" -ForegroundColor Green
        Write-Host $gpuInfo
        
        $vram = (nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null | Select-Object -First 1)
        if ([int]$vram -lt 8000) {
            Write-Host "[!] Warning: VRAM < 8GB. S2-Pro requires at least 8GB VRAM" -ForegroundColor Yellow
            Write-Host "    Your VRAM: $vram MB (OK for testing, production needs 8GB+)" -ForegroundColor Yellow
            $continue = Read-Host "Continue anyway? (y/n)"
            if ($continue -ne "y") { exit 1 }
        }
    }
} catch {
    Write-Host "[X] NVIDIA GPU not detected. S2-Pro requires CUDA-capable GPU" -ForegroundColor Red
    exit 1
}

# Check UV
try {
    $uvVersion = uv --version 2>&1
    Write-Host "[OK] UV found: $uvVersion" -ForegroundColor Green
} catch {
    Write-Host "[X] UV not found. Install it first:" -ForegroundColor Red
    Write-Host "    pip install uv"
    exit 1
}

# Check Python via UV
$pythonList = uv python list 2>&1 | Out-String

if ($pythonList -match "3\.12") {
    Write-Host "[OK] Python 3.12 available via UV" -ForegroundColor Green
    $pythonVersion = "3.12"
} elseif ($pythonList -match "3\.11") {
    Write-Host "[!] Python 3.11 available (3.12 recommended)" -ForegroundColor Yellow
    $pythonVersion = "3.11"
} elseif ($pythonList -match "3\.10") {
    Write-Host "[!] Python 3.10 available (3.12 recommended)" -ForegroundColor Yellow
    $pythonVersion = "3.10"
} else {
    Write-Host "[X] Python 3.10+ not found in UV" -ForegroundColor Red
    Write-Host "    Install with: uv python install 3.12"
    exit 1
}

# Check disk space
$drive = (Get-Location).Drive
$freeSpace = [math]::Round((Get-PSDrive $drive.Name).Free / 1GB, 2)
if ($freeSpace -lt 15) {
    Write-Host "[X] Insufficient disk space. Need at least 15GB, have ${freeSpace}GB" -ForegroundColor Red
    exit 1
} else {
    Write-Host "[OK] Disk space: ${freeSpace}GB available" -ForegroundColor Green
}

# Check ffmpeg
try {
    $ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
    Write-Host "[OK] FFmpeg found" -ForegroundColor Green
} catch {
    Write-Host "[!] FFmpeg not found (optional but recommended)" -ForegroundColor Yellow
}

Write-Host ""

# FASE 2: Backup v1.5
Write-Host "FASE 2: Backing up Fish-Speech v1.5" -ForegroundColor Yellow
Write-Host "--------------------------------------"

$projectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$externalDir = Join-Path $projectRoot "external"
$fishSpeechDir = Join-Path $externalDir "fish-speech"

if (Test-Path $fishSpeechDir) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = Join-Path $externalDir "fish-speech-v1.5-backup-$timestamp"
    Write-Host "Moving $fishSpeechDir to $backupDir"
    
    try {
        # Force move with robocopy for better handling of locked files
        robocopy $fishSpeechDir $backupDir /E /MOVE /R:1 /W:1 /NFL /NDL /NJH /NJS | Out-Null
        if (Test-Path $fishSpeechDir) {
            Remove-Item $fishSpeechDir -Recurse -Force -ErrorAction SilentlyContinue
        }
        Write-Host "[OK] Backup created at $backupDir" -ForegroundColor Green
    } catch {
        Write-Host "[!] Could not move folder (may be in use). Please:" -ForegroundColor Yellow
        Write-Host "    1. Close any Fish-Speech processes"
        Write-Host "    2. Close File Explorer if viewing the folder"
        Write-Host "    3. Manually rename: $fishSpeechDir to $backupDir"
        Write-Host "    4. Run this script again"
        exit 1
    }
} else {
    Write-Host "[!] No existing fish-speech folder found, skipping backup" -ForegroundColor Yellow
}

Write-Host ""

# FASE 3: Clone Fresh Repository
Write-Host "FASE 3: Cloning Fresh Fish-Speech Repository" -ForegroundColor Yellow
Write-Host "--------------------------------------"

if (-not (Test-Path $externalDir)) {
    New-Item -ItemType Directory -Path $externalDir | Out-Null
}

Set-Location $externalDir

if (Test-Path "fish-speech") {
    Write-Host "[X] fish-speech directory already exists" -ForegroundColor Red
    exit 1
}

Write-Host "Cloning from https://github.com/fishaudio/fish-speech.git"
git clone https://github.com/fishaudio/fish-speech.git
Set-Location fish-speech
Write-Host "[OK] Repository cloned successfully" -ForegroundColor Green

Write-Host ""

# FASE 4: Install Dependencies with UV
Write-Host "FASE 4: Installing Dependencies with UV" -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Detect CUDA version
try {
    $nvccOutput = nvcc --version 2>&1 | Out-String
    if ($nvccOutput -match "release (\d+\.\d+)") {
        $cudaVersion = $matches[1]
        Write-Host "Detected CUDA version: $cudaVersion"

        
        if ($cudaVersion -like "12.9*") {
            $cudaSuffix = "cu129"
        } elseif ($cudaVersion -like "12.8*") {
            $cudaSuffix = "cu128"
        } elseif ($cudaVersion -like "12.6*") {
            $cudaSuffix = "cu126"
        } else {
            Write-Host "[!] CUDA version $cudaVersion detected, defaulting to cu126" -ForegroundColor Yellow
            $cudaSuffix = "cu126"
        }
    }
} catch {
    Write-Host "[!] nvcc not found, defaulting to cu126" -ForegroundColor Yellow
    $cudaSuffix = "cu126"
}

Write-Host "Creating UV virtual environment with Python $pythonVersion..."
uv venv --python $pythonVersion

Write-Host "Installing Fish-Speech with CUDA support ($cudaSuffix)..."
uv pip install -e ".[$cudaSuffix]"

Write-Host "[OK] Dependencies installed with UV" -ForegroundColor Green

Write-Host ""

# FASE 5: Download S2-Pro Model
Write-Host "FASE 5: Downloading S2-Pro Model (~10GB)" -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Check if huggingface-cli is available
try {
    huggingface-cli --version 2>&1 | Out-Null
} catch {
    Write-Host "Installing huggingface-hub with UV..."
    uv pip install huggingface-hub
}

Write-Host "Downloading fishaudio/s2-pro model..."
Write-Host "This will take several minutes depending on your connection..."


if (-not (Test-Path "checkpoints")) {
    New-Item -ItemType Directory -Path "checkpoints" | Out-Null
}

uv run huggingface-cli download fishaudio/s2-pro --local-dir checkpoints/s2-pro

Write-Host "[OK] S2-Pro model downloaded" -ForegroundColor Green

Write-Host ""

# FASE 6: Test CLI Inference
Write-Host "FASE 6: Testing CLI Inference (Indonesian)" -ForegroundColor Yellow
Write-Host "--------------------------------------"

$testText = "Halo, selamat datang di toko kami. Hari ini ada promo spesial."
Write-Host "Test text: $testText"

Write-Host "[!] CLI test skipped (requires reference audio)" -ForegroundColor Yellow
Write-Host "    Use WebUI for interactive testing"

Write-Host ""

# FASE 7: Launch WebUI
Write-Host "FASE 7: Ready to Launch WebUI" -ForegroundColor Yellow
Write-Host "--------------------------------------"

Write-Host ""
Write-Host "==========================================" -ForegroundColor Green
Write-Host "Upgrade Complete!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Run WebUI: cd $externalDir\fish-speech; uv run python tools/run_webui.py"
Write-Host "2. Open browser: http://localhost:7860"
Write-Host "3. Test Indonesian text with emotion tags like [excited], [whisper]"
Write-Host ""
Write-Host "For automated testing, run:"
Write-Host "  uv run python $projectRoot\scripts\test-s2-indonesia.py"
Write-Host ""
if ($backupDir) {
    Write-Host "Backup location: $backupDir"
}
Write-Host ""

# Ask if user wants to start WebUI now
$startNow = Read-Host "Start WebUI now? (y/n)"
if ($startNow -eq "y") {
    Write-Host "Starting WebUI at http://localhost:7860" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop"
    uv run python tools/run_webui.py
}
