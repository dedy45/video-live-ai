#!/bin/bash
# AI Live Commerce Platform — Remote Sync
# Syncs local code to remote GPU server (e.g., RunPod)
# Requirements: 29.1, 29.2

set -e

REMOTE_USER=${REMOTE_USER:-"root"}
REMOTE_HOST=${REMOTE_HOST:-"unknown.runpod.net"}
REMOTE_PORT=${REMOTE_PORT:-"22"}
REMOTE_DIR=${REMOTE_DIR:-"/workspace/videoliveai"}

echo "=========================================================="
echo "  AI Live Commerce — Remote Sync"
echo "  Target: $REMOTE_USER@$REMOTE_HOST:$REMOTE_PORT"
echo "=========================================================="

if [ "$REMOTE_HOST" = "unknown.runpod.net" ]; then
    echo "ERROR: REMOTE_HOST is not set."
    echo "Usage: REMOTE_HOST=x.x.x.x REMOTE_PORT=22 ./scripts/remote_sync.sh"
    exit 1
fi

echo "[1/3] Creating remote directory..."
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

echo "[2/3] Syncing files via rsync..."
rsync -avz --progress \
    --exclude '.git' \
    --exclude '.venv' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.ruff_cache' \
    --exclude '.mypy_cache' \
    --exclude 'data/logs' \
    --exclude 'data/cache' \
    -e "ssh -p $REMOTE_PORT" \
    ./ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

echo "[3/3] Sync complete."
echo "To access remote terminal:"
echo "ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST"
