#!/bin/bash
set -euo pipefail

#
# Hella Webtilian - Development Environment Startup
#
# This script:
#   1) Ensures .env.dev exists
#   2) Builds and starts all Docker containers
#   3) Waits for PostgreSQL and Redis to be ready
#   4) Waits for the web service to actually accept connections (and optionally HTTP)
#   5) Runs migrations, creates superuser, seeds data, collects static
#
# Key improvements:
#   - Fails fast with timeouts
#   - Prints container status + last logs on failure
#   - Uses docker compose v2 if available (falls back to docker-compose)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

COMPOSE_FILE="docker-compose.dev.yml"

# Prefer Compose v2 ("docker compose"), fallback to v1 ("docker-compose")
if command -v docker &>/dev/null && docker compose version &>/dev/null; then
  DC="docker compose"
elif command -v docker-compose &>/dev/null; then
  DC="docker-compose"
else
  echo "✗ Error: Neither 'docker compose' nor 'docker-compose' found in PATH."
  exit 1
fi

# ------------------------------
# Helpers
# ------------------------------

die() {
  echo ""
  echo "✗ $*"
  echo ""
  echo "=== compose ps ==="
  $DC -f "$COMPOSE_FILE" ps || true
  echo ""
  echo "=== last 80 lines: web ==="
  $DC -f "$COMPOSE_FILE" logs --tail=80 web || true
  echo ""
  echo "=== last 80 lines: vite ==="
  $DC -f "$COMPOSE_FILE" logs --tail=80 vite || true
  echo ""
  echo "=== last 80 lines: db ==="
  $DC -f "$COMPOSE_FILE" logs --tail=80 db || true
  echo ""
  echo "=== last 80 lines: redis ==="
  $DC -f "$COMPOSE_FILE" logs --tail=80 redis || true
  exit 1
}

# Read a single KEY=value from .env.dev, without sourcing it.
# (Safer than `source .env.dev` because values can contain characters that bash will interpret.)
env_get() {
  local key="$1"
  local default="${2:-}"
  local val
  val="$(grep -E "^${key}=" .env.dev 2>/dev/null | head -n1 | sed -E "s/^${key}=//")" || true
  if [ -z "${val:-}" ]; then
    echo "$default"
  else
    # strip surrounding quotes if present
    val="${val%\"}"
    val="${val#\"}"
    echo "$val"
  fi
}

wait_for_exec() {
  local service="$1"
  local timeout_s="${2:-60}"
  local start
  start="$(date +%s)"

  echo -n "Waiting for '$service' container to accept exec"
  while true; do
    if $DC -f "$COMPOSE_FILE" exec -T "$service" sh -lc 'echo ok' >/dev/null 2>&1; then
      echo " ✓"
      return 0
    fi
    echo -n "."
    sleep 1
    if (( $(date +%s) - start > timeout_s )); then
      echo ""
      die "Timed out waiting for exec on service '$service' (${timeout_s}s)."
    fi
  done
}

wait_for_db() {
  local timeout_s="${1:-90}"
  local start
  start="$(date +%s)"

  local db_user db_name
  db_user="$(env_get POSTGRES_USER hruser)"
  db_name="$(env_get POSTGRES_DB hella_reptilian_dev)"

  echo -n "Waiting for PostgreSQL (${db_user}@${db_name})"
  while true; do
    if $DC -f "$COMPOSE_FILE" exec -T db pg_isready -U "$db_user" -d "$db_name" >/dev/null 2>&1; then
      echo " ✓"
      return 0
    fi
    echo -n "."
    sleep 1
    if (( $(date +%s) - start > timeout_s )); then
      echo ""
      die "Timed out waiting for PostgreSQL (${timeout_s}s)."
    fi
  done
}

wait_for_redis() {
  local timeout_s="${1:-60}"
  local start
  start="$(date +%s)"

  echo -n "Waiting for Redis"
  while true; do
    if $DC -f "$COMPOSE_FILE" exec -T redis redis-cli ping >/dev/null 2>&1; then
      echo " ✓"
      return 0
    fi
    echo -n "."
    sleep 1
    if (( $(date +%s) - start > timeout_s )); then
      echo ""
      die "Timed out waiting for Redis (${timeout_s}s)."
    fi
  done
}

wait_for_web_port() {
  # Checks whether port 8000 is listening inside the web container.
  local timeout_s="${1:-90}"
  local start
  start="$(date +%s)"

  echo -n "Waiting for Django port (8000) to listen"
  while true; do
    if $DC -f "$COMPOSE_FILE" exec -T web sh -lc 'nc -z 127.0.0.1 8000' >/dev/null 2>&1; then
      echo " ✓"
      return 0
    fi

    echo -n "."
    sleep 1
    if (( $(date +%s) - start > timeout_s )); then
      echo ""
      die "Timed out waiting for Django to listen on port 8000 (${timeout_s}s)."
    fi
  done
}

wait_for_web_http() {
  # Optional HTTP check. Works if curl exists in the web container.
  local path="${1:-/}"
  local timeout_s="${2:-60}"
  local start
  start="$(date +%s)"

  if ! $DC -f "$COMPOSE_FILE" exec -T web sh -lc 'command -v curl >/dev/null 2>&1'; then
    echo "Skipping HTTP readiness check (curl not present in web container)."
    return 0
  fi

  echo -n "Waiting for Django HTTP ${path}"
  while true; do
    if $DC -f "$COMPOSE_FILE" exec -T web sh -lc "curl -fsS http://localhost:8000${path} >/dev/null"; then
      echo " ✓"
      return 0
    fi
    echo -n "."
    sleep 1
    if (( $(date +%s) - start > timeout_s )); then
      echo ""
      die "Timed out waiting for Django HTTP ${path} (${timeout_s}s)."
    fi
  done
}

# ------------------------------
# Main
# ------------------------------

echo "========================================="
echo "Hella Webtilian - Development Setup"
echo "========================================="
echo ""

# Check if .env.dev exists, create from example if not
if [ ! -f .env.dev ]; then
  echo "Creating .env.dev from example..."
  if [ -f .env.dev.example ]; then
    cp .env.dev.example .env.dev
    echo "✓ Created .env.dev - please review and update as needed"
  else
    die "Error: .env.dev.example not found"
  fi
else
  echo "✓ Found .env.dev"
fi

echo ""
echo "Step 1: Building Docker containers..."
echo "--------------------------------------"
$DC -f "$COMPOSE_FILE" build

echo ""
echo "Step 2: Starting services..."
echo "--------------------------------------"
$DC -f "$COMPOSE_FILE" up -d

echo ""
echo "Step 3: Waiting for services to be ready..."
echo "--------------------------------------"

# Ensure base containers accept exec (helps avoid races)
wait_for_exec db 60
wait_for_exec redis 60
wait_for_exec web 60

wait_for_db 90
wait_for_redis 60

# Web readiness: require port to be listening (and optionally HTTP)
wait_for_web_port 120
wait_for_web_http "/" 60

echo ""
echo "Step 4: Running database migrations..."
echo "--------------------------------------"
$DC -f "$COMPOSE_FILE" exec -T web python manage.py migrate || die "Migration failed."

echo ""
echo "Step 5: Creating/ensuring superuser..."
echo "--------------------------------------"
$DC -f "$COMPOSE_FILE" exec -T web python manage.py shell -c "
import os
from django.contrib.auth import get_user_model

# This is a dev script; only run when DEBUG is truthy.
debug_val = (os.getenv('DEBUG', '0') or '').strip().lower()
if debug_val not in ('1','true','yes','on'):
    print('Skipping superuser creation (not in dev)')
    raise SystemExit(0)

User = get_user_model()

username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@hellareptilian.local')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin')

if '@' not in email:
    raise ValueError(f'Invalid DJANGO_SUPERUSER_EMAIL: {email!r}')

user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': email},
)

changed = False

if getattr(user, 'email', None) != email:
    user.email = email
    changed = True

if not user.is_staff:
    user.is_staff = True
    changed = True

if not user.is_superuser:
    user.is_superuser = True
    changed = True

if not user.check_password(password):
    user.set_password(password)
    changed = True

if changed:
    user.full_clean()
    user.save()

print('✓ Superuser created' if created else '✓ Superuser ensured')
" || die "Superuser ensure failed."

echo ""
echo "Step 6: Seeding initial data..."
echo "--------------------------------------"
$DC -f "$COMPOSE_FILE" exec -T web python manage.py seed_data || echo "Seed command completed or not needed"

echo ""
echo "Step 7: Collecting static files..."
echo "--------------------------------------"
if [ "${RUN_COLLECTSTATIC:-0}" = "1" ]; then
  $DC -f "$COMPOSE_FILE" exec -T web python manage.py collectstatic --noinput || die "collectstatic failed."
  echo "✓ collectstatic completed"
else
  echo "↷ Skipping collectstatic (set RUN_COLLECTSTATIC=1 to enable)"
fi

echo ""
echo "========================================="
echo "✓ Development environment is ready!"
echo "========================================="
echo ""
echo "Services running:"
echo "  • Django:      http://localhost:8000"
echo "  • Vite:        http://localhost:5174"
echo "  • PostgreSQL:  localhost:5432"
echo "  • Redis:       localhost:6379"
echo ""
echo "Useful commands:"
echo "  • View logs:        $DC -f $COMPOSE_FILE logs -f"
echo "  • Stop services:    $DC -f $COMPOSE_FILE down"
echo "  • Restart services: $DC -f $COMPOSE_FILE restart"
echo "  • Shell access:     $DC -f $COMPOSE_FILE exec web sh"
echo "  • Django shell:     $DC -f $COMPOSE_FILE exec web python manage.py shell"
echo ""
