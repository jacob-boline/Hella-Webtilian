#!/bin/bash

#
# Hella Webtilian - Production Environment Startup
#
# This script:
#   1) Loads environment variables from .env.prod
#   2) Builds and starts all Docker containers
#   3) Waits for services to be healthy
#   4) Starts the application
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Hella Webtilian - Production Deployment"
echo "========================================="
echo ""

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "✗ Error: .env.prod not found"
    echo ""
    echo "Please create .env.prod from .env.prod.example and configure it:"
    echo "  cp .env.prod.example .env.prod"
    echo "  nano .env.prod  # or use your preferred editor"
    echo ""
    exit 1
fi

echo "✓ Found .env.prod"
echo ""

# Confirm production deployment
read -p "Deploy to PRODUCTION? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 0
fi

echo ""
echo "Step 1: Building Docker containers..."
echo "--------------------------------------"
docker-compose build --no-cache

echo ""
echo "Step 2: Starting services..."
echo "--------------------------------------"
docker-compose up -d

echo ""
echo "Step 3: Waiting for services to be healthy..."
echo "--------------------------------------"

# Wait for database health check
echo -n "Waiting for PostgreSQL..."
max_attempts=30
attempt=0
until docker-compose exec -T db pg_isready -U ${POSTGRES_USER:-hruser} > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 2
    ((attempt++))
done

if [ $attempt -eq $max_attempts ]; then
    echo " ✗ Failed!"
    echo "PostgreSQL did not become ready in time"
    exit 1
fi
echo " ✓ Ready!"

# Wait for Redis health check
echo -n "Waiting for Redis..."
attempt=0
until docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 2
    ((attempt++))
done

if [ $attempt -eq $max_attempts ]; then
    echo " ✗ Failed!"
    echo "Redis did not become ready in time"
    exit 1
fi
echo " ✓ Ready!"

# Wait for web application health check
echo -n "Waiting for web application..."
attempt=0
until curl -f http://localhost/health/ > /dev/null 2>&1 || [ $attempt -eq $max_attempts ]; do
    echo -n "."
    sleep 3
    ((attempt++))
done

if [ $attempt -eq $max_attempts ]; then
    echo " ✗ Failed!"
    echo "Web application did not become healthy in time"
    echo "Check logs with: docker-compose logs web"
    exit 1
fi
echo " ✓ Ready!"

echo ""
echo "========================================="
echo "✓ Production deployment complete!"
echo "========================================="
echo ""
echo "Services running:"
echo "  • Application: http://localhost:${NGINX_PORT:-80}"
echo "  • Health check: http://localhost:${NGINX_PORT:-80}/health/"
echo ""
echo "Useful commands:"
echo "  • View logs:        docker-compose logs -f"
echo "  • View web logs:    docker-compose logs -f web"
echo "  • View nginx logs:  docker-compose logs -f nginx"
echo "  • View worker logs: docker-compose logs -f rq_worker"
echo "  • Stop services:    docker-compose down"
echo "  • Restart services: docker-compose restart"
echo ""
echo "To update the application:"
echo "  1. Pull latest code"
echo "  2. Run: docker-compose build"
echo "  3. Run: docker-compose up -d"
echo ""

