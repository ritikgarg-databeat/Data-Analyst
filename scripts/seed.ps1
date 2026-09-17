# Idempotent database seed — safe to run repeatedly. Run migrate.ps1 first.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
uv run --project apps/api python -m app.db.seed
