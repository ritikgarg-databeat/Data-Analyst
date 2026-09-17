#!/usr/bin/env bash
# One-shot local setup: install deps, apply migrations, seed the database.
# Assumes Postgres is already running (e.g. `docker compose up -d postgres`)
# and DATABASE_URL (see .env.example) points at it.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> Installing frontend dependencies (npm workspaces)"
npm install

echo "==> Installing backend dependencies (uv)"
uv sync --project apps/api --extra dev

echo "==> Applying migrations"
./scripts/migrate.sh

echo "==> Seeding database"
./scripts/seed.sh

echo "==> Done. Start the app with 'docker compose up --build' or see README.md for running frontend/backend locally."
