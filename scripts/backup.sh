#!/bin/bash
# AI Live Commerce Platform — Data Backup
# Backs up database, configs, and assets
# Requirements: 13.7

set -e

PROJECT_DIR=$(dirname "$0")/..
BACKUP_DIR="${PROJECT_DIR}/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
ARCHIVE_NAME="videoliveai_backup_${TIMESTAMP}.tar.gz"

echo "=========================================================="
echo "  AI Live Commerce — Data Backup"
echo "  Timestamp: $TIMESTAMP"
echo "=========================================================="

mkdir -p "$BACKUP_DIR"
cd "$PROJECT_DIR"

echo "[1/3] Preparing files for backup..."
# Create a temporary list of files to back up
cat << EOF > /tmp/backup_include.txt
data/commerce.db
config/config.yaml
.env
data/sample_products.json
EOF

echo "[2/3] Creating archive $ARCHIVE_NAME..."
tar -czvf "$BACKUP_DIR/$ARCHIVE_NAME" -T /tmp/backup_include.txt

# Clean old backups (keep last 7)
echo "[3/3] Rotating old backups..."
ls -1tr "$BACKUP_DIR"/videoliveai_backup_*.tar.gz | head -n -7 | xargs -d '\n' rm -f -- || true

rm /tmp/backup_include.txt

echo ""
echo "Backup successful: $BACKUP_DIR/$ARCHIVE_NAME"
