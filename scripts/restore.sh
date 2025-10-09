#!/bin/bash
# License Compliance Checker - Restore Script
#
# This script restores from a backup created by backup.sh
#
# Usage: ./scripts/restore.sh <backup_file_or_directory>

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

log_prompt() {
    echo -e "${BLUE}[PROMPT]${NC} $1"
}

# Error handler
error_handler() {
    log_error "Restore failed at line $1"
    exit 1
}

trap 'error_handler $LINENO' ERR

# Check arguments
if [ $# -eq 0 ]; then
    log_error "Usage: $0 <backup_file_or_directory>"
    log_error "Example: $0 backups/lcc_backup_20241031_120000.tar.gz"
    exit 1
fi

BACKUP_SOURCE="$1"

# Check if backup exists
if [ ! -e "${BACKUP_SOURCE}" ]; then
    log_error "Backup not found: ${BACKUP_SOURCE}"
    exit 1
fi

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
REDIS_CONTAINER="${REDIS_CONTAINER:-lcc-redis-1}"

log_info "Starting restore from: ${BACKUP_SOURCE}"

# Create temporary directory for extraction
TEMP_DIR=$(mktemp -d)
trap "rm -rf ${TEMP_DIR}" EXIT

# Extract backup if it's a tar.gz file
if [[ "${BACKUP_SOURCE}" == *.tar.gz ]]; then
    log_info "Extracting backup archive..."
    tar -xzf "${BACKUP_SOURCE}" -C "${TEMP_DIR}"
    # Find the extracted directory
    BACKUP_DIR=$(find "${TEMP_DIR}" -maxdepth 1 -type d -name "lcc_backup_*" | head -n1)
    if [ -z "${BACKUP_DIR}" ]; then
        log_error "Failed to find backup directory in archive"
        exit 1
    fi
    log_info "Archive extracted to: ${BACKUP_DIR}"
else
    BACKUP_DIR="${BACKUP_SOURCE}"
fi

# Display backup metadata
if [ -f "${BACKUP_DIR}/metadata.txt" ]; then
    log_info "========================================="
    log_info "Backup Information:"
    log_info "========================================="
    cat "${BACKUP_DIR}/metadata.txt"
    echo ""
fi

# Confirm restore
log_warn "========================================="
log_warn "WARNING: This will overwrite current data!"
log_warn "========================================="
log_prompt "Are you sure you want to restore? (yes/no)"
read -r confirmation

if [ "${confirmation}" != "yes" ]; then
    log_info "Restore cancelled"
    exit 0
fi

# 1. Restore PostgreSQL database
if [ -f "${BACKUP_DIR}/database.sql" ]; then
    log_info "Restoring PostgreSQL database..."

    # Check if PostgreSQL container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${POSTGRES_CONTAINER}$"; then
        log_error "PostgreSQL container is not running: ${POSTGRES_CONTAINER}"
        log_error "Start services with: docker-compose -f docker-compose.prod.yml up -d"
        exit 1
    fi

    # Drop and recreate database
    log_warn "Dropping and recreating database: ${POSTGRES_DB}"
    docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -c "DROP DATABASE IF EXISTS ${POSTGRES_DB};"
    docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -c "CREATE DATABASE ${POSTGRES_DB};"

    # Restore database
    docker exec -i "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" "${POSTGRES_DB}" < "${BACKUP_DIR}/database.sql"
    log_info "Database restored successfully"
else
    log_warn "No database backup found, skipping"
fi

# 2. Restore policy files
if [ -d "${BACKUP_DIR}/policies" ]; then
    log_info "Restoring policy files..."
    mkdir -p "${PROJECT_DIR}/data/policies"
    cp -r "${BACKUP_DIR}/policies"/* "${PROJECT_DIR}/data/policies/"
    log_info "Policy files restored"
else
    log_warn "No policy files found, skipping"
fi

# 3. Restore configuration files
if [ -d "${BACKUP_DIR}/config" ]; then
    log_info "Restoring configuration files..."

    # Backup current config files
    CURRENT_BACKUP="${PROJECT_DIR}/config_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "${CURRENT_BACKUP}"

    CONFIG_FILES=(
        ".env"
        "docker-compose.prod.yml"
        "nginx/nginx.conf"
        "nginx/conf.d/default.conf"
        "nginx/conf.d/ssl.conf"
    )

    for file in "${CONFIG_FILES[@]}"; do
        if [ -f "${PROJECT_DIR}/${file}" ]; then
            file_dir=$(dirname "${file}")
            mkdir -p "${CURRENT_BACKUP}/${file_dir}"
            cp "${PROJECT_DIR}/${file}" "${CURRENT_BACKUP}/${file}"
        fi
    done

    log_info "Current config backed up to: ${CURRENT_BACKUP}"

    # Restore config files
    log_prompt "Restore configuration files? This will overwrite current configs. (yes/no)"
    read -r restore_config

    if [ "${restore_config}" = "yes" ]; then
        cp -r "${BACKUP_DIR}/config"/* "${PROJECT_DIR}/"
        log_info "Configuration files restored"
        log_warn "NOTE: You may need to restart services for config changes to take effect"
    else
        log_info "Skipped configuration restore"
    fi
else
    log_warn "No configuration files found, skipping"
fi

# 4. Restore SSL certificates
if [ -d "${BACKUP_DIR}/ssl" ]; then
    log_info "Restoring SSL certificates..."
    mkdir -p "${PROJECT_DIR}/nginx/ssl"
    cp -r "${BACKUP_DIR}/ssl"/* "${PROJECT_DIR}/nginx/ssl/"
    chmod 600 "${PROJECT_DIR}/nginx/ssl"/*.key 2>/dev/null || true
    log_info "SSL certificates restored"
else
    log_warn "No SSL certificates found, skipping"
fi

# 5. Restore Redis data
if [ -f "${BACKUP_DIR}/redis.rdb" ]; then
    log_info "Restoring Redis data..."

    if docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
        # Stop Redis
        docker exec "${REDIS_CONTAINER}" redis-cli SHUTDOWN NOSAVE 2>/dev/null || true
        sleep 2

        # Copy RDB file
        docker cp "${BACKUP_DIR}/redis.rdb" "${REDIS_CONTAINER}:/data/dump.rdb"

        # Restart Redis container
        docker restart "${REDIS_CONTAINER}"
        log_info "Redis data restored"
    else
        log_warn "Redis container not running, skipping Redis restore"
    fi
else
    log_warn "No Redis data found, skipping"
fi

# 6. Verify restore
log_info "Verifying restore..."

# Check database connection
if docker exec "${POSTGRES_CONTAINER}" psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" > /dev/null 2>&1; then
    log_info "✓ Database connection verified"
else
    log_error "✗ Database connection failed"
fi

# Check policy files
if [ -d "${PROJECT_DIR}/data/policies" ]; then
    POLICY_COUNT=$(find "${PROJECT_DIR}/data/policies" -type f | wc -l)
    log_info "✓ Policy files found: ${POLICY_COUNT}"
else
    log_warn "✗ No policy files found"
fi

# Display summary
log_info "========================================="
log_info "Restore completed successfully!"
log_info "========================================="
log_info ""
log_info "Next steps:"
log_info "1. Verify application configuration (.env)"
log_info "2. Restart services if needed:"
log_info "   docker-compose -f docker-compose.prod.yml restart"
log_info "3. Check logs for any issues:"
log_info "   docker-compose -f docker-compose.prod.yml logs -f"
log_info "4. Verify application health:"
log_info "   curl http://localhost:8000/health"
log_info ""

exit 0
