##########################
# BUILDER STAGE          #
##########################
FROM python:3.11-slim-bookworm AS builder

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv sync --frozen --no-dev


##########################
# NODE BUILD STAGE       #
##########################
FROM node:20-slim AS node-builder

WORKDIR /build

# Copy package files
COPY package.json package-lock.json ./

# Install Node dependencies
RUN npm ci

# Copy source files for Vite build
COPY hr_core/static_src ./hr_core/static_src
COPY vite.config.js ./

# Build static assets with Vite
RUN npm run build


##########################
# FINAL STAGE            #
##########################
FROM python:3.11-slim-bookworm

# Create app user and group
RUN groupadd -r app && useradd -r -g app app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=hr_config.settings.prod_docker

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    imagemagick \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /home/app/web && \
    mkdir -p /home/app/web/staticfiles && \
    mkdir -p /home/app/web/media && \
    mkdir -p /home/app/web/logs

WORKDIR /home/app/web

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy built static assets from node-builder
COPY --from=node-builder /build/hr_core/static/hr_core/dist ./hr_core/static/hr_core/dist

# Copy application code
COPY --chown=app:app . .

# Copy entrypoint script
COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set ownership
RUN chown -R app:app /home/app

# Switch to non-root user
USER app

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn hr_django.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 4 --timeout 120 --access-logfile - --error-logfile -"]
