#!/usr/bin/env bash
# Validate content/, then upsert Lesson/Exercise rows (+ tags/skills/datasets/
# prerequisites/related-lessons) into the database from content/**/*.yaml.
# Requires migrations AND the taxonomy seed to already exist (domains/modules/
# skills/datasets/tags) — run ./scripts/migrate.sh then ./scripts/seed.sh
# first. ./scripts/seed.sh already calls this internally; run it standalone
# only when you've edited content/ and want to re-sync without reseeding.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run --project apps/api python -m app.content.sync
