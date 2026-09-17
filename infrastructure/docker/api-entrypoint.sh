#!/usr/bin/env bash
# Entrypoint for the `api` container: applies pending Alembic migrations
# (idempotent — no-op if already at head) before starting the API, so a
# fresh `docker compose up` always boots against an up-to-date schema.
# Seeding is deliberately NOT run automatically here — run
# `scripts/seed.sh` (or `docker compose exec api uv run python -m app.db.seed`)
# explicitly, per README.md, so a developer always knows when seed data changed.
set -euo pipefail

cd /app
echo "[api-entrypoint] Applying database migrations..."
alembic -c alembic.ini upgrade head

echo "[api-entrypoint] Starting API..."
exec "$@"
