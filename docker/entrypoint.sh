#!/bin/bash
set -e

echo "========================================="
echo "Hella Webtilian - Production Startup"
echo "========================================="

# Function to wait for database
wait_for_db() {
  echo "Waiting for PostgreSQL..."

  # Extract DB connection details from DATABASE_URL
  if [[ -z "${DB_HOST:-}" || -z "${DB_PORT:-}" ]]; then
    if [[ -n "${DATABASE_URL:-}" ]]; then
      DB_HOST="$(
        python - <<'PY'
import os
from urllib.parse import urlparse
u = urlparse(os.environ["DATABASE_URL"])
print(u.hostname or "")
PY
      )"
      DB_PORT="$(
        python - <<'PY'
import os
from urllib.parse import urlparse
u = urlparse(os.environ["DATABASE_URL"])
print(u.port or "5432")
PY
      )"
    fi
  fi

  # On Fly, never default to "db". Fail fast if DB_HOST is still empty.
  if [[ -z "${DB_HOST:-}" ]]; then
    echo "ERROR: DB host not resolved. DATABASE_URL is missing or invalid."
    echo "       DATABASE_URL present? ${DATABASE_URL:+yes}"
    exit 1
  fi

  DB_PORT="${DB_PORT:-5432}"
  echo "Resolved Postgres: $DB_HOST:$DB_PORT"
}
## Function to wait for Redis
#wait_for_redis() {
#  echo "Waiting for Redis..."
#
#   if [[ -z "${REDIS_HOST:-}" || -z "${REDIS_PORT:-}" ]]; then
#      if [[ -n "${REDIS_URL:-}" ]]; then
#          REDIS_HOST="$(python - <<'PY'
#import os
#from urllib.parse import urlparse
#
#url = os.environ.get("REDIS_URL", "")
#parsed = urlparse(url)
#print(parsed.hostname or "")
#PY
#)"
#            REDIS_PORT="$(python - <<'PY'
#import os
#from urllib.parse import urlparse
#
#url = os.environ.get("REDIS_URL", "")
#parsed = urlparse(url)
#print(parsed.port or "")
#PY
#)"
#        fi
#    fi
#
#  REDIS_HOST="${REDIS_HOST:-redis}"
#  REDIS_PORT="${REDIS_PORT:-6379}"
#
#  while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
#    sleep 0.1
#  done
#
#  echo "Redis is available!"
#}

# Wait for required services
wait_for_db
#if [[ -n "${REDIS_HOST:-}" || -n "${REDIS_URL:-}" ]]; then
#    wait_for_redis
#else
#    echo "Skipping Redis wait (no REDIS_HOST/REDIS_URL set)."
#fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create cache table if it doesn't exist (if using database cache)
#echo "Setting up cache..."
#python manage.py createcachetable 2>/dev/null || true

echo "========================================="
echo "Startup complete! Starting application..."
echo "========================================="

# Execute the main command
exec "$@"
