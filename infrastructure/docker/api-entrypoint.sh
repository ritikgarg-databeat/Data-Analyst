#!/usr/bin/env bash
# Entrypoint for the `api` container: applies pending Alembic migrations
# (idempotent — no-op if already at head) before starting the API, so a
# fresh `docker compose up` always boots against an up-to-date schema. The
# administrator bootstrap is idempotent, so it is safe on every deploy. The
# larger curriculum seed is intentionally not run here because it can exceed
# hosted platforms' port-binding startup window; seed/sync it as a separate
# release operation when provisioning an empty database.
set -euo pipefail

cd /app
echo "[api-entrypoint] Applying database migrations..."
alembic -c alembic.ini upgrade head

if [[ "${BOOTSTRAP_ADMIN_ON_START:-true}" == "true" && -n "${INITIAL_ADMIN_PASSWORD:-}" ]]; then
  echo "[api-entrypoint] Ensuring the initial administrator exists..."
  python -m app.db.bootstrap_admin
elif [[ "${BOOTSTRAP_ADMIN_ON_START:-true}" != "true" ]]; then
  echo "[api-entrypoint] Administrator bootstrap disabled for this established environment."
else
  echo "[api-entrypoint] INITIAL_ADMIN_PASSWORD is not set; skipping administrator bootstrap."
fi

echo "[api-entrypoint] Starting API..."
exec "$@"
