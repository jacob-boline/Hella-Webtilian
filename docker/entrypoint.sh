#!/bin/bash
set -e

echo "========================================="
echo "Hella Webtilian - Production Startup"
echo "========================================="

# Function to wait for database
wait_for_db() {
    echo "Waiting for PostgreSQL..."

    # Extract DB connection details from DATABASE_URL or use defaults
    DB_HOST="${DB_HOST:-db}"
    DB_PORT="${DB_PORT:-5432}"

    while ! nc -z "$DB_HOST" "$DB_PORT"; do
        sleep 0.1
    done

    echo "PostgreSQL is available!"
}

# Function to wait for Redis
wait_for_redis() {
    echo "Waiting for Redis..."

    REDIS_HOST="${REDIS_HOST:-redis}"
    REDIS_PORT="${REDIS_PORT:-6379}"

    while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
        sleep 0.1
    done

    echo "Redis is available!"
}

# Wait for required services
wait_for_db
wait_for_redis

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table if it doesn't exist (if using database cache)
echo "Setting up cache..."
python manage.py createcachetable 2>/dev/null || true

echo "========================================="
echo "Startup complete! Starting application..."
echo "========================================="

# Execute the main command
exec "$@"

