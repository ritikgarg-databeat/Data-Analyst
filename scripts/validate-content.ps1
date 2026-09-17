# Validate every content/ file against its schema and cross-references.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
uv run --project apps/api python -m app.content.validate
