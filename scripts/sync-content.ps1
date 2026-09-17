# Validate content/, then upsert Lesson/Exercise rows into the database.
# Requires migrate.ps1 + seed.ps1 to have already run at least once.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
uv run --project apps/api python -m app.content.sync
