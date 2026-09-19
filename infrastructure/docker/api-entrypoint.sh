#!/usr/bin/env bash
# Entrypoint for the `api` container: applies pending Alembic migrations
# (idempotent — no-op if already at head) before starting the API, so a
# fresh `docker compose up` always boots against an up-to-date schema. The
# shared curriculum seed and administrator bootstrap are both idempotent, so
# running them here also makes a fresh Render database immediately usable.
set -euo pipefail

cd /app
echo "[api-entrypoint] Applying database migrations..."
alembic -c alembic.ini upgrade head

echo "[api-entrypoint] Syncing shared curriculum content..."
python -m app.db.seed

if [[ -n "${INITIAL_ADMIN_PASSWORD:-}" ]]; then
  echo "[api-entrypoint] Ensuring the initial administrator exists..."
  python -m app.db.bootstrap_admin
else
  echo "[api-entrypoint] INITIAL_ADMIN_PASSWORD is not set; skipping administrator bootstrap."
fi

echo "[api-entrypoint] Starting API..."
exec "$@"
