#!/bin/bash

#
# Backup PostgreSQL database
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"

cd "$PROJECT_ROOT"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Get current date for filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/hella_reptilian_${TIMESTAMP}.sql"

echo "Creating database backup..."

# Determine which compose file to use
if [ -f .env.prod ] && docker-compose ps | grep -q "hr_db"; then
    COMPOSE_FILE="docker-compose.yml"
    DB_CONTAINER="hr_db"
    DB_NAME="${POSTGRES_DB:-hella_reptilian}"
    DB_USER="${POSTGRES_USER:-hruser}"
elif docker-compose -f docker-compose.dev.yml ps | grep -q "hr_db_dev"; then
    COMPOSE_FILE="docker-compose.dev.yml"
    DB_CONTAINER="hr_db_dev"
    DB_NAME="${POSTGRES_DB:-hella_reptilian_dev}"
    DB_USER="${POSTGRES_USER:-hruser}"
else
    echo "Error: No running database container found"
    exit 1
fi

# Create backup
if [ "$COMPOSE_FILE" = "docker-compose.yml" ]; then
    docker-compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
else
    docker-compose -f docker-compose.dev.yml exec -T db pg_dump -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
fi

# Compress backup
gzip "$BACKUP_FILE"
BACKUP_FILE="${BACKUP_FILE}.gz"

echo "✓ Backup created: $BACKUP_FILE"
echo "  Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Keep only last 10 backups
echo "Cleaning old backups (keeping last 10)..."
cd "$BACKUP_DIR"
ls -t hella_reptilian_*.sql.gz | tail -n +11 | xargs -r rm
echo "✓ Cleanup complete"

