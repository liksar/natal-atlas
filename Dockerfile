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
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv sync --frozen --no-dev \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY backend/ backend/
COPY --from=frontend /src/backend/static/atlas.js backend/static/atlas.js
COPY data-manifests/ data-manifests/
COPY ops/ ops/
COPY LICENSE LICENSES.md ./
RUN DJANGO_SECRET_KEY=build-only-placeholder DJANGO_DEBUG=true LOCAL_SQLITE=1 python backend/manage.py collectstatic --noinput && useradd --uid 10001 --create-home atlas
WORKDIR /app/backend
USER atlas
EXPOSE 8000
CMD ["sh", "-c", "python manage.py preflight && exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --worker-class sync --workers ${WEB_WORKERS:-2} --threads 1 --timeout 60 --error-logfile /dev/null"]
