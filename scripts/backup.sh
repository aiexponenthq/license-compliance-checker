#!/bin/bash
# License Compliance Checker - Backup Script
#
# This script backs up:
# - PostgreSQL database
# - Policy files
# - Configuration files
# - SSL certificates
#
# Usage: ./scripts/backup.sh [backup_dir]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BACKUP_DIR="${1:-${PROJECT_DIR}/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="lcc_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handler
error_handler() {
    log_error "Backup failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Load environment variables
if [ -f "${PROJECT_DIR}/.env" ]; then
    source "${PROJECT_DIR}/.env"
else
    log_warn ".env file not found, using defaults"
fi

# Set defaults
POSTGRES_USER="${POSTGRES_USER:-lcc}"
POSTGRES_DB="${POSTGRES_DB:-lcc}"
POSTGRES_CONTAINER="${POSTGRES_CONTAINER:-lcc-postgres-1}"

log_info "Starting backup: ${BACKUP_NAME}"

# Create backup directory
mkdir -p "${BACKUP_PATH}"
log_info "Created backup directory: ${BACKUP_PATH}"

# 1. Backup PostgreSQL database
log_info "Backing up PostgreSQL database..."
if docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
    docker exec "${POSTGRES_CONTAINER}" pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" \
        > "${BACKUP_PATH}/database.sql"
    log_info "Database backup completed: database.sql"
else
    log_warn "PostgreSQL container not running, skipping database backup"
fi

# 2. Backup policy files
log_info "Backing up policy files..."
if [ -d "${PROJECT_DIR}/data/policies" ]; then
    cp -r "${PROJECT_DIR}/data/policies" "${BACKUP_PATH}/policies"
    log_info "Policy files backed up"
else
    log_warn "Policy directory not found, skipping"
fi

# 3. Backup configuration files
log_info "Backing up configuration files..."
CONFIG_FILES=(
    ".env"
    "docker-compose.prod.yml"
    "nginx/nginx.conf"
    "nginx/conf.d/default.conf"
    "nginx/conf.d/ssl.conf"
)

mkdir -p "${BACKUP_PATH}/config"
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "${PROJECT_DIR}/${file}" ]; then
        # Preserve directory structure
        file_dir=$(dirname "${file}")
        mkdir -p "${BACKUP_PATH}/config/${file_dir}"
        cp "${PROJECT_DIR}/${file}" "${BACKUP_PATH}/config/${file}"
        log_info "Backed up: ${file}"
    else
        log_warn "File not found: ${file}"
    fi
done

# 4. Backup SSL certificates (if they exist)
log_info "Backing up SSL certificates..."
if [ -d "${PROJECT_DIR}/nginx/ssl" ]; then
    mkdir -p "${BACKUP_PATH}/ssl"
    cp -r "${PROJECT_DIR}/nginx/ssl"/* "${BACKUP_PATH}/ssl/" 2>/dev/null || true
    log_info "SSL certificates backed up"
else
    log_warn "SSL directory not found, skipping"
fi

# 5. Backup Redis data (optional)
log_info "Backing up Redis data..."
REDIS_CONTAINER="${REDIS_CONTAINER:-lcc-redis-1}"
if docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
    # Trigger Redis save
    docker exec "${REDIS_CONTAINER}" redis-cli SAVE 2>/dev/null || true
    # Copy RDB file
    docker cp "${REDIS_CONTAINER}:/data/dump.rdb" "${BACKUP_PATH}/redis.rdb" 2>/dev/null || true
    log_info "Redis data backed up"
else
    log_warn "Redis container not running, skipping Redis backup"
fi

# 6. Create metadata file
log_info "Creating backup metadata..."
cat > "${BACKUP_PATH}/metadata.txt" << EOF
Backup Information
==================
Date: $(date)
Hostname: $(hostname)
User: $(whoami)
Backup Name: ${BACKUP_NAME}
LCC Version: ${VERSION:-unknown}
Environment: ${ENVIRONMENT:-unknown}

Contents:
- database.sql (PostgreSQL dump)
- policies/ (Policy files)
- config/ (Configuration files)
- ssl/ (SSL certificates)
- redis.rdb (Redis data)

Restore Command:
  ./scripts/restore.sh ${BACKUP_PATH}
EOF

log_info "Metadata created"

# 7. Create compressed archive
log_info "Creating compressed archive..."
cd "${BACKUP_DIR}"
tar -czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"
ARCHIVE_SIZE=$(du -h "${BACKUP_NAME}.tar.gz" | cut -f1)
log_info "Archive created: ${BACKUP_NAME}.tar.gz (${ARCHIVE_SIZE})"

# 8. Remove uncompressed backup directory
rm -rf "${BACKUP_NAME}"
log_info "Cleaned up temporary files"

# 9. Apply retention policy
if [ -n "${BACKUP_RETENTION_DAYS:-}" ]; then
    log_info "Applying retention policy: ${BACKUP_RETENTION_DAYS} days"
    find "${BACKUP_DIR}" -name "lcc_backup_*.tar.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete
    log_info "Old backups removed"
fi

# 10. Display backup summary
log_info "========================================="
log_info "Backup completed successfully!"
log_info "========================================="
log_info "Archive: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
log_info "Size: ${ARCHIVE_SIZE}"
log_info ""
log_info "To restore this backup:"
log_info "  ./scripts/restore.sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
log_info ""

# Optional: Upload to remote storage (S3, etc.)
if [ -n "${BACKUP_S3_BUCKET:-}" ]; then
    log_info "Uploading to S3: ${BACKUP_S3_BUCKET}"
    aws s3 cp "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
        "s3://${BACKUP_S3_BUCKET}/lcc-backups/${BACKUP_NAME}.tar.gz" || \
        log_warn "S3 upload failed"
fi

exit 0
