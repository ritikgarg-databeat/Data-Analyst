# Troubleshooting

Start here: **`make health`** (or `GET /api/v1/platform/health` if the API is already running) —
prints a dependency-aware status for the database, DuckDB, the SQL Lab's optional Postgres engine, the
Python Lab sandbox, dbt, the AI provider, and Kaggle. `not_configured` for AI/Kaggle/the Postgres SQL
engine is expected (they're optional, local-first-friendly) — `unavailable` means something real is
wrong; read that row's `detail` field, it's always a concrete, actionable message, never a stack trace.

## "A DB-touching request just hangs forever"

Almost always the same root cause across this project's history: a command was run in a way that
resolved `.env` incorrectly. `app/core/config.py`'s `env_file` is anchored to `config.py`'s own file
location (not the process's current working directory), so this should no longer happen for any
documented command — but if you've written a new script that imports `app.core.config` from an
unusual entrypoint, confirm `get_settings().database_url` prints the real local `sqlite:///.../data/
dev.db` path, not the hardcoded PostgreSQL default. A silent fallback to that Postgres default is the
signature of this bug: it doesn't fail fast, it hangs, because nothing is listening on that address.

## "I edited a file but the running server still serves the old behavior"

On Windows, `uv run --project apps/api uvicorn --reload` spawns a reloader process *and* a separate
child worker process. Killing the reloader's PID does not reliably kill its child — the orphaned child
can keep running, still bound to the port, still serving stale code, while a freshly started
reloader+worker pair sits behind it unable to receive traffic. If restarting the server doesn't seem to
pick up a change: compare `Get-Process` against `Get-NetTCPConnection -LocalPort 8000`'s
`OwningProcess` — if they disagree, kill the process actually holding the port (found by comparing
process start times), not just the reloader you most recently started.

## "Python Lab says unavailable"

`make health` will show `Python Sandbox: unavailable` with a `DockerException` detail if Docker
Desktop isn't running, or isn't reachable from this process. Start Docker Desktop and re-check; the
Python Lab's other prerequisite — the sandbox image itself — is built once with
`make build-python-sandbox` and does not need rebuilding on every start.

## "dbt says unavailable"

`make health`'s dbt check is a plain `shutil.which("dbt")` — it needs the `dbt` CLI on `PATH` inside
the Python environment `uv sync --project apps/api` installed. If you're running outside the
`apps/api` venv (e.g. a bare system Python), `dbt` won't be found even though it's installed correctly
inside the project's own virtualenv.

## "AI features say local-mode / not configured"

This is the default, not a bug — `AI_PROVIDER=local` needs no key and is what every phase's own test
suite runs against. To use a real provider: set `AI_PROVIDER=openai` or `=anthropic` and a matching key
in `.env` (see `.env.example`), then restart the API so it picks up the new environment.

## "Kaggle search/import isn't available"

Same shape as AI: `KAGGLE_USERNAME`/`KAGGLE_KEY` are optional. `GET /kaggle/status` (or `make health`)
tells you whether they're configured; the rest of the Dataset Hub (local file import, profiling, EDA,
visualization) works fully without them.

## "A migration or seed command behaves differently than I expect"

Migrations are additive and ordered (`alembic upgrade head` only ever adds/changes forward); nothing in
`make migrate`/`make seed` drops existing data. `make seed` re-running is always safe — every seed
function upserts by natural key (slug/email), never truncates first. If you genuinely want to discard
your own progress, see [`docs/backup-restore.md`](backup-restore.md) — take a backup first.

## "I want to inspect exactly what went wrong on a failed request"

Every error response includes a `request_id` (`{"error": {"code", "message", "details", "request_id"}}`)
that matches the same id in that request's server-side log line (`method`, `path`, `status`,
`duration_ms`, `request_id`) — grep the API's log output for that id to see the full context.

## Still stuck?

Check [`docs/architecture.md`](architecture.md) for how the pieces fit together, or
[`docs/roadmap.md`](roadmap.md)'s per-phase "found while building" sections — several of the issues
above were real, once-in-development bugs that are now documented there in full, with how they were
diagnosed.
