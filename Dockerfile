##########################
# PY BUILDER (prod deps) #
##########################
FROM python:3.11-slim-bookworm AS py-builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

RUN uv sync --frozen --no-dev
RUN /opt/venv/bin/python -c "import django; print('Django OK', django.get_version())"


##########################
# NODE BUILDER (prod)    #
##########################
FROM node:20-slim AS node-builder

WORKDIR /build

COPY package.json package-lock.json ./
RUN npm ci

COPY hr_core/static_src ./hr_core/static_src
COPY vite.config.js ./

RUN npm run build


##########################
# PROD RUNTIME           #
##########################
FROM python:3.11-slim-bookworm AS prod

RUN groupadd -r app && useradd -r -g app app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    DJANGO_SETTINGS_MODULE=hr_config.settings.prod_docker

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    imagemagick \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/app/web

RUN mkdir -p /home/app/web/staticfiles \
             /home/app/web/media \
             /home/app/web/logs

COPY --from=py-builder /opt/venv /opt/venv
COPY --from=node-builder /build/hr_core/static/hr_core/dist ./hr_core/static/hr_core/dist

# Copy app code (exclude heavy stuff via .dockerignore)
COPY --chown=app:app . .

COPY --chown=app:app docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /home/app

USER app

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn hr_django.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 4 --timeout 120 --access-logfile - --error-logfile -"]


##########################
# DEV IMAGE              #
##########################
FROM python:3.11-slim-bookworm AS dev

RUN groupadd -r app && useradd -r -g app app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=hr_config.settings.dev

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    imagemagick \
    netcat-openbsd \
    curl \
    git \
    tzdata \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Node for Vite (dev)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && apt-get install -y --no-install-recommends nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /home/app/web

RUN mkdir -p /home/app/web/staticfiles \
             /home/app/web/media \
             /home/app/web/logs

# deps for caching
COPY pyproject.toml uv.lock ./

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv && \
    /opt/venv/bin/python -m pip install --upgrade pip && \
    uv sync --frozen && \
    rm -rf /home/app/web/.venv

RUN chown -R app:app /opt/venv

# node deps (dev)
COPY package.json package-lock.json ./
RUN npm install

# App code (in compose you'll typically mount over this)
COPY --chown=app:app . .

COPY docker/entrypoint.dev.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh && chown -R app:app /home/app

USER app

EXPOSE 8000 5173

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
