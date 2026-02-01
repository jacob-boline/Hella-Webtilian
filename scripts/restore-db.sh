#!/bin/bash

#
# Restore PostgreSQL database from backup
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"

cd "$PROJECT_ROOT"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    ls -lh "$BACKUP_DIR"/hella_reptilian_*.sql.gz 2>/dev/null || echo "  No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# If only filename provided, look in backup directory
if [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/$1"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring database from: $BACKUP_FILE"
read -p "This will REPLACE the current database. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

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

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_FILE="/tmp/restore_$(date +%s).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

echo "Dropping and recreating database..."
if [ "$COMPOSE_FILE" = "docker-compose.yml" ]; then
    docker-compose exec -T db psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker-compose exec -T db psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

    echo "Restoring data..."
    cat "$RESTORE_FILE" | docker-compose exec -T db psql -U "$DB_USER" "$DB_NAME"
else
    docker-compose -f docker-compose.dev.yml exec -T db psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
    docker-compose -f docker-compose.dev.yml exec -T db psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;"

    echo "Restoring data..."
    cat "$RESTORE_FILE" | docker-compose -f docker-compose.dev.yml exec -T db psql -U "$DB_USER" "$DB_NAME"
fi

# Clean up temp file
if [ -n "$TEMP_FILE" ]; then
    rm "$TEMP_FILE"
fi

echo "✓ Database restored successfully"
echo ""
echo "You may need to restart the application:"
if [ "$COMPOSE_FILE" = "docker-compose.yml" ]; then
    echo "  docker-compose restart web"
else
    echo "  docker-compose -f docker-compose.dev.yml restart web"
fi

