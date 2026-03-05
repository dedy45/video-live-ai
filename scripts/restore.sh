#!/bin/bash
# AI Live Commerce Platform — Data Restore
# Restores database and configs from a backup archive
# Requirements: 13.7

set -e

PROJECT_DIR=$(dirname "$0")/..
BACKUP_DIR="${PROJECT_DIR}/backups"

echo "=========================================================="
echo "  AI Live Commerce — Data Restore"
echo "=========================================================="

if [ -z "$1" ]; then
    echo "ERROR: Backup archive not specified."
    echo "Available backups:"
    ls -1 "$BACKUP_DIR"
    echo ""
    echo "Usage: ./scripts/restore.sh <filename.tar.gz>"
    exit 1
fi

ARCHIVE_PATH="$BACKUP_DIR/$1"

if [ ! -f "$ARCHIVE_PATH" ]; then
    echo "ERROR: Archive $ARCHIVE_PATH not found."
    exit 1
fi

echo "WARNING: This will overwrite current data/commerce.db, config/config.yaml, and .env!"
read -p "Are you sure you want to restore? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 1
fi

cd "$PROJECT_DIR"

echo "[1/2] Creating pre-restore backup..."
./scripts/backup.sh || true

echo "[2/2] Extracting archive..."
tar -xzvf "$ARCHIVE_PATH"

echo "Restore complete! Please restart the application."
