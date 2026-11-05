FROM node:24-bookworm-slim AS frontend
WORKDIR /src/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.13.7 AS uv
FROM python:3.12-slim-bookworm
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.render
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv sync --frozen --no-dev \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY backend/ backend/
COPY --from=frontend /src/backend/static/atlas.js backend/static/atlas.js
COPY ops/ ops/
COPY data-manifests/ data-manifests/
COPY bundled-data/ bundled-data/
COPY LICENSE LICENSES.md ./
RUN python ops/safe_extract.py bundled-data/natal-data.tar.gz /app \
    && rm -rf bundled-data \
    && DJANGO_SETTINGS_MODULE=config.settings DJANGO_SECRET_KEY=build-only DJANGO_DEBUG=true LOCAL_SQLITE=1 python backend/manage.py collectstatic --noinput \
    && useradd --uid 10001 --create-home atlas
USER atlas
CMD ["python", "ops/render_start.py"]
