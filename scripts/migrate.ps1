# Apply pending Alembic migrations. Run from anywhere.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
uv run --project apps/api alembic -c alembic.ini upgrade head
