#!/bin/bash

#
# Initial Docker Setup Script
# Run this once after cloning the repository
#

set -e

echo "========================================="
echo "Hella Webtilian - Initial Docker Setup"
echo "========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "Step 1: Making scripts executable..."
chmod +x scripts/*.sh
chmod +x docker/entrypoint.sh
chmod +x docker/entrypoint.dev.sh
echo "✓ Scripts are now executable"

echo ""
echo "Step 2: Creating environment files..."

if [ ! -f .env.dev ]; then
    cp .env.dev.example .env.dev
    echo "✓ Created .env.dev"
else
    echo "⊙ .env.dev already exists (skipping)"
fi

if [ ! -f .env.prod ]; then
    cp .env.prod.example .env.prod
    echo "✓ Created .env.prod"
    echo "  ⚠ IMPORTANT: Edit .env.prod before deploying to production!"
else
    echo "⊙ .env.prod already exists (skipping)"
fi

echo ""
echo "Step 3: Creating backup directory..."
mkdir -p backups
echo "✓ Backup directory created"

echo ""
echo "Step 4: Checking Docker..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is installed"
    docker --version
else
    echo "✗ Docker is not installed"
    echo "  Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker-compose &> /dev/null; then
    echo "✓ Docker Compose is installed"
    docker-compose --version
else
    echo "✗ Docker Compose is not installed"
    echo "  Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo ""
echo "========================================="
echo "✓ Initial setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo ""
echo "For DEVELOPMENT:"
echo "  1. Review .env.dev (optional - defaults are fine)"
echo "  2. Run: ./scripts/start-dev.sh"
echo "  3. Access: http://localhost:8000"
echo ""
echo "For PRODUCTION:"
echo "  1. Edit .env.prod with your settings"
echo "  2. Run: ./scripts/start-prod.sh"
echo "  3. Configure your domain/reverse proxy"
echo ""
echo "Documentation:"
echo "  • Full guide: DOCKER_README.md"
echo "  • Quick ref:  DOCKER_QUICKREF.md"
echo ""

