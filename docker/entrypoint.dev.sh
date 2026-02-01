#!/bin/bash
set -e

export UV_PROJECT_ENVIRONMENT=/opt/venv
export VIRTUAL_ENV=/opt/venv
export PATH="$VIRTUAL_ENV/bin:$PATH"

echo "========================================="
echo "Hella Webtilian - Development Startup"
echo "========================================="

# NOTE:
# This entrypoint is intentionally "dumb + safe".
# It only waits for dependent services so the main process doesn't crash-loop,
# then hands off to the CMD. All migrations/seed/superuser/collectstatic are
# driven by start-dev.sh to avoid double-running.

wait_for_db() {
  echo "Waiting for PostgreSQL..."

  DB_HOST="${DB_HOST:-db}"
  DB_PORT="${DB_PORT:-5432}"

  while ! nc -z "$DB_HOST" "$DB_PORT"; do
    sleep 0.1
  done

  echo "PostgreSQL is available!"
}

wait_for_redis() {
  echo "Waiting for Redis..."

  REDIS_HOST="${REDIS_HOST:-redis}"
  REDIS_PORT="${REDIS_PORT:-6379}"

  while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
    sleep 0.1
  done

  echo "Redis is available!"
}

wait_for_db
wait_for_redis

echo "========================================="
echo "Container dependencies ready; starting main process..."
echo "========================================="

exec "$@"
