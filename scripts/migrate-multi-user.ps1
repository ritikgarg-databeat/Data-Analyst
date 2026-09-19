# Back up SQLite/PostgreSQL and data/, then apply the multi-user migration and bootstrap.
$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$BackupRoot = Join-Path $RepoRoot "backups\multi-user-$Timestamp"
New-Item -ItemType Directory -Path $BackupRoot | Out-Null

$DatabaseUrl = $env:DATABASE_URL
if (-not $DatabaseUrl) {
    $EnvCandidates = @((Join-Path $RepoRoot "apps\api\.env"), (Join-Path $RepoRoot ".env"))
    foreach ($EnvPath in $EnvCandidates) {
        if (-not $DatabaseUrl -and (Test-Path $EnvPath)) {
            $Line = Get-Content $EnvPath | Where-Object { $_ -match '^DATABASE_URL=' } | Select-Object -First 1
            if ($Line) { $DatabaseUrl = $Line.Substring("DATABASE_URL=".Length) }
        }
    }
}
if (-not $DatabaseUrl) { throw "DATABASE_URL is required before migration." }

if ($DatabaseUrl -match '^sqlite(?:\+[^:]+)?:///') {
    $DatabasePathValue = $DatabaseUrl -replace '^sqlite(?:\+[^:]+)?:///', ''
    if ([IO.Path]::IsPathRooted($DatabasePathValue)) {
        $DatabasePath = [IO.Path]::GetFullPath($DatabasePathValue)
    } else {
        $DatabasePath = [IO.Path]::GetFullPath((Join-Path $RepoRoot $DatabasePathValue))
    }
    if (-not (Test-Path -LiteralPath $DatabasePath -PathType Leaf)) {
        throw "SQLite database not found at the configured path; migration was not started."
    }
    Copy-Item -LiteralPath $DatabasePath -Destination (Join-Path $BackupRoot "database.sqlite3")
} elseif ($DatabaseUrl -match '^postgresql(?:\+[^:]+)?://') {
    if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
        throw "pg_dump must be installed and on PATH for PostgreSQL migration."
    }
    $PgUrl = $DatabaseUrl -replace '^postgresql\+psycopg', 'postgresql'
    & pg_dump --format=custom --file (Join-Path $BackupRoot "postgres.dump") $PgUrl
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL backup failed; migration was not started." }
} else {
    throw "Only SQLite and PostgreSQL DATABASE_URL values are supported by this migration script."
}

$TarCommand = Get-Command tar -ErrorAction SilentlyContinue
if (-not $TarCommand) {
    throw "tar must be installed and on PATH to back up data/ without Windows long-path failures."
}
$DataBackup = Join-Path $BackupRoot "data.tar.gz"
& $TarCommand.Source -czf $DataBackup -C $RepoRoot "data"
if ($LASTEXITCODE -ne 0) { throw "data/ backup failed; migration was not started." }

uv run --project apps/api alembic -c alembic.ini upgrade head
uv run --project apps/api python -m app.db.bootstrap_admin
Write-Host "Migration complete. Backup: $BackupRoot"
