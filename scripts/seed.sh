#!/usr/bin/env bash
# Idempotent database seed — safe to run repeatedly. Requires migrations to
# already be applied (run scripts/migrate.sh first).
#
# Runs from the repo root (not --directory apps/api) so that a relative
# DATABASE_URL (e.g. a local sqlite:///./foo.db used outside Docker) resolves
# to the same working directory migrate.sh used — `app` still resolves via
# apps/api's editable install (see `uv sync --project apps/api`).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run --project apps/api python -m app.db.seed
