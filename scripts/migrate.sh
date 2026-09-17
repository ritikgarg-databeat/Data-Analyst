#!/usr/bin/env bash
# Apply pending Alembic migrations. Run from repo root (or anywhere — this
# script cds there itself). Uses the apps/api uv-managed virtualenv.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run --project apps/api alembic -c alembic.ini upgrade head
