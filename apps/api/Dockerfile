FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir uv

WORKDIR /app

# Install dependencies first so the layer is cached across code-only changes.
COPY apps/api/pyproject.toml apps/api/pyproject.toml
WORKDIR /app/apps/api
RUN uv pip install --system --no-cache -e ".[dev]" || uv pip install --system --no-cache -e "."

WORKDIR /app
COPY apps/api apps/api
COPY database database
COPY content content
COPY data/sample data/sample
COPY alembic.ini alembic.ini
COPY infrastructure/docker/api-entrypoint.sh api-entrypoint.sh
RUN chmod +x api-entrypoint.sh

WORKDIR /app/apps/api

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

ENTRYPOINT ["/app/api-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
