#!/usr/bin/env bash
# Validate every content/ file against its schema and cross-references
# (duplicate slugs, broken prerequisites, missing skills/datasets/tags).
# Does NOT require a database connection.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

uv run --project apps/api python -m app.content.validate
