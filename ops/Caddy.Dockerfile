FROM node:24-bookworm-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.12-slim-bookworm AS assets
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /src
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv sync --frozen --no-dev \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY backend/ backend/
COPY --from=frontend /src/backend/static/atlas.js backend/static/atlas.js
RUN DJANGO_SECRET_KEY=build-only DJANGO_DEBUG=true LOCAL_SQLITE=1 .venv/bin/python backend/manage.py collectstatic --noinput
FROM caddy:2-alpine
COPY --from=assets /src/staticfiles /srv/static
