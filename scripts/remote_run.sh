#!/bin/bash
# AI Live Commerce Platform — Remote Execution
# Deploys and runs the system on the remote GPU server
# Requirements: 29.1, 29.3

set -e

REMOTE_USER=${REMOTE_USER:-"root"}
REMOTE_HOST=${REMOTE_HOST:-"unknown.runpod.net"}
REMOTE_PORT=${REMOTE_PORT:-"22"}
REMOTE_DIR=${REMOTE_DIR:-"/workspace/videoliveai"}

echo "=========================================================="
echo "  AI Live Commerce — Remote Execution"
echo "  Target: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT"
echo "=========================================================="

if [ "$REMOTE_HOST" = "unknown.runpod.net" ]; then
    echo "ERROR: REMOTE_HOST is not set."
    exit 1
fi

# Multi-line SSH execution
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << EOF
    set -e
    echo "[1/4] Navigating to workspace..."
    cd $REMOTE_DIR

    echo "[2/4] Ensuring UV is installed..."
    if ! command -v uv &> /dev/null; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source \$HOME/.cargo/env
    fi

    echo "[3/4] Syncing dependencies (GPU profile)..."
    uv sync --extra gpu --no-dev

    echo "[4/4] Starting the platform in detached mode..."
    # Kill existing tmux session if running
    tmux kill-session -t videoliveai 2>/dev/null || true
    
    # Start new tmux session in detached mode
    tmux new-session -d -s videoliveai "MOCK_MODE=false uv run python -m src.main"
    
    echo "Platform successfully started in background (tmux session: videoliveai)."
    echo "To attach to logs: ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST -t 'tmux attach -t videoliveai'"
EOF

echo "Remote execution command finished."
