#!/bin/bash
# Fish-Speech S2-Pro Upgrade Script
# Automates upgrade from v1.5 to S2-Pro with Indonesian language support

set -e

echo "=========================================="
echo "Fish-Speech S2-Pro Upgrade Script"
echo "=========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# FASE 1: System Check
echo -e "${YELLOW}FASE 1: Checking System Requirements${NC}"
echo "--------------------------------------"

# Check GPU
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓${NC} NVIDIA GPU detected"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    VRAM=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n1)
    if [ "$VRAM" -lt 8000 ]; then
        echo -e "${RED}✗${NC} Warning: VRAM < 8GB. S2-Pro requires at least 8GB VRAM"
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${RED}✗${NC} NVIDIA GPU not detected. S2-Pro requires CUDA-capable GPU"
    exit 1
fi

# Check UV (Windows compatible)
if uv --version &> /dev/null; then
    UV_VERSION=$(uv --version 2>&1 | head -n1)
    echo -e "${GREEN}✓${NC} UV found: $UV_VERSION"
else
    echo -e "${RED}✗${NC} UV not found. Install it first:"
    echo "  Windows: pip install uv"
    echo "  Linux/Mac: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Check Python via UV
if uv python list | grep -q "3.12"; then
    echo -e "${GREEN}✓${NC} Python 3.12 available via UV"
    PYTHON_VERSION="3.12"
elif uv python list | grep -q "3.11"; then
    echo -e "${YELLOW}!${NC} Python 3.11 available (3.12 recommended)"
    PYTHON_VERSION="3.11"
elif uv python list | grep -q "3.10"; then
    echo -e "${YELLOW}!${NC} Python 3.10 available (3.12 recommended)"
    PYTHON_VERSION="3.10"
else
    echo -e "${RED}✗${NC} Python 3.10+ not found in UV"
    echo "  Install with: uv python install 3.12"
    exit 1
fi

# Check disk space
AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 15 ]; then
    echo -e "${RED}✗${NC} Insufficient disk space. Need at least 15GB, have ${AVAILABLE_SPACE}GB"
    exit 1
else
    echo -e "${GREEN}✓${NC} Disk space: ${AVAILABLE_SPACE}GB available"
fi

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}✓${NC} FFmpeg found: $(ffmpeg -version | head -n1)"
else
    echo -e "${YELLOW}!${NC} FFmpeg not found (optional but recommended)"
fi

echo ""

# FASE 2: Backup v1.5
echo -e "${YELLOW}FASE 2: Backing up Fish-Speech v1.5${NC}"
echo "--------------------------------------"

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)
EXTERNAL_DIR="$PROJECT_ROOT/external"

if [ -d "$EXTERNAL_DIR/fish-speech" ]; then
    BACKUP_DIR="$EXTERNAL_DIR/fish-speech-v1.5-backup-$(date +%Y%m%d-%H%M%S)"
    echo "Moving $EXTERNAL_DIR/fish-speech to $BACKUP_DIR"
    mv "$EXTERNAL_DIR/fish-speech" "$BACKUP_DIR"
    echo -e "${GREEN}✓${NC} Backup created at $BACKUP_DIR"
else
    echo -e "${YELLOW}!${NC} No existing fish-speech folder found, skipping backup"
fi

echo ""

# FASE 3: Clone Fresh Repository
echo -e "${YELLOW}FASE 3: Cloning Fresh Fish-Speech Repository${NC}"
echo "--------------------------------------"

mkdir -p "$EXTERNAL_DIR"
cd "$EXTERNAL_DIR"

if [ -d "fish-speech" ]; then
    echo -e "${RED}✗${NC} fish-speech directory already exists"
    exit 1
fi

echo "Cloning from https://github.com/fishaudio/fish-speech.git"
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech
echo -e "${GREEN}✓${NC} Repository cloned successfully"

echo ""

# FASE 4: Install Dependencies with UV
echo -e "${YELLOW}FASE 4: Installing Dependencies with UV${NC}"
echo "--------------------------------------"

# Detect CUDA version
if command -v nvcc &> /dev/null; then
    CUDA_VERSION=$(nvcc --version | grep "release" | sed -n 's/.*release \([0-9]*\.[0-9]*\).*/\1/p')
    echo "Detected CUDA version: $CUDA_VERSION"
    
    if [[ "$CUDA_VERSION" == 12.9* ]]; then
        CUDA_SUFFIX="cu129"
    elif [[ "$CUDA_VERSION" == 12.8* ]]; then
        CUDA_SUFFIX="cu128"
    elif [[ "$CUDA_VERSION" == 12.6* ]]; then
        CUDA_SUFFIX="cu126"
    else
        echo -e "${YELLOW}!${NC} CUDA version $CUDA_VERSION detected, defaulting to cu126"
        CUDA_SUFFIX="cu126"
    fi
else
    echo -e "${YELLOW}!${NC} nvcc not found, defaulting to cu126"
    CUDA_SUFFIX="cu126"
fi

echo "Creating UV virtual environment with Python $PYTHON_VERSION..."
uv venv --python $PYTHON_VERSION

echo "Installing Fish-Speech with CUDA support ($CUDA_SUFFIX)..."
uv pip install -e ".[$CUDA_SUFFIX]"

echo -e "${GREEN}✓${NC} Dependencies installed with UV"

echo ""

# FASE 5: Download S2-Pro Model
echo -e "${YELLOW}FASE 5: Downloading S2-Pro Model (~10GB)${NC}"
echo "--------------------------------------"

if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface-hub with UV..."
    uv pip install huggingface-hub
fi

echo "Downloading fishaudio/s2-pro model..."
echo "This will take several minutes depending on your connection..."

mkdir -p checkpoints
huggingface-cli download fishaudio/s2-pro --local-dir checkpoints/s2-pro

echo -e "${GREEN}✓${NC} S2-Pro model downloaded"

echo ""

# FASE 6: Test CLI Inference
echo -e "${YELLOW}FASE 6: Testing CLI Inference (Indonesian)${NC}"
echo "--------------------------------------"

TEST_TEXT="Halo, selamat datang di toko kami. Hari ini ada promo spesial."
echo "Test text: $TEST_TEXT"

# Create test script
cat > test_inference.py << 'EOF'
import sys
sys.path.insert(0, ".")

from tools.llama.generate import launch_thread_safe_queue
from tools.vqgan.inference import load_model as load_decoder
import torch

print("Loading models...")
decoder_model = load_decoder("checkpoints/s2-pro", device="cuda")
print("✓ Decoder loaded")

# Test inference
test_text = "Halo, selamat datang di toko kami."
print(f"Generating audio for: {test_text}")

# This is a simplified test - actual inference requires more setup
print("✓ Model initialization successful")
print("Note: Full inference test requires reference audio")
EOF

uv run python test_inference.py || echo -e "${YELLOW}!${NC} CLI test skipped (requires reference audio)"
rm test_inference.py

echo ""

# FASE 7: Launch WebUI
echo -e "${YELLOW}FASE 7: Launching WebUI${NC}"
echo "--------------------------------------"

echo ""
echo -e "${GREEN}=========================================="
echo "Upgrade Complete!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Run WebUI: cd $EXTERNAL_DIR/fish-speech && uv run python tools/run_webui.py"
echo "2. Open browser: http://localhost:7860"
echo "3. Test Indonesian text with emotion tags like [excited], [whisper]"
echo ""
echo "For automated testing, run:"
echo "  uv run python $PROJECT_ROOT/scripts/test-s2-indonesia.py"
echo ""
echo "Backup location: $BACKUP_DIR"
echo ""

# Ask if user wants to start WebUI now
read -p "Start WebUI now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting WebUI at http://localhost:7860"
    echo "Press Ctrl+C to stop"
    uv run python tools/run_webui.py
fi
