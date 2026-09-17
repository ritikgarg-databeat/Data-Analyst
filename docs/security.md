# Security

This app is local-first and normally runs on a single developer's own machine, but "local" is not
treated as an automatic safety guarantee — every layer below is real, verified isolation/redaction
code, not a policy statement. Facts here were confirmed against the current codebase during Phase 12's
security audit (not carried forward from earlier phases' own descriptions).

## Python sandbox (`apps/api/app/python_lab/docker_backend.py`)

Every Python Lab execution runs inside a fresh Docker container with:

- `network_mode="none"` — no network stack at all, not even loopback.
- `user="1000:1000"` — non-root, a dedicated `sandbox` user baked into the sandbox image.
- `read_only=True` root filesystem; only `/tmp` (a size-capped `tmpfs`) is writable.
- `cap_drop=["ALL"]` and `security_opt=["no-new-privileges"]`.
- Configurable resource ceilings: `mem_limit` (default 512m), `nano_cpus` (default 1 CPU),
  `pids_limit` (default 128).
- A dual timeout: an in-container `SIGALRM` wall-clock interrupt, backed by an outer host-side
  `ThreadPoolExecutor` timeout that force-kills the container if the inner one doesn't fire.
- The dataset directory is mounted `ro` (read-only); nothing else from the host is exposed.

**What this does *not* do**: there is no code-level restriction on what the executed Python can call —
`import subprocess`, `import os`, `open(...)` are all reachable at the language level. Isolation is
enforced entirely by the container boundary above (no network to exfiltrate over, a read-only root
filesystem so nothing persists, dropped capabilities so most privileged syscalls fail). This is a
deliberate, documented tradeoff, not an oversight — see `docker_backend.py`'s own module docstring.

## SQL Lab (`apps/api/app/sql/safety.py`, `app/sql/engines/*.py`)

- A denylist (`assert_safe_query`) rejects `INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE/ATTACH/
  DETACH/COPY/GRANT/REVOKE/VACUUM/SET/CALL/EXPORT/IMPORT/INSTALL/LOAD/MERGE/PRAGMA/RESET/CHECKPOINT/USE`
  and multi-statement input (`;`-separated) before either engine ever sees the query.
- The PostgreSQL engine additionally opens every session `read_only=True` and always ends with
  `rollback()`, even on success — defense in depth beyond the denylist.
- A query timeout (`SQL_LAB_QUERY_TIMEOUT_SECONDS`, default 10s) and row limit (`SQL_LAB_ROW_LIMIT`,
  default 1000) apply to every query.
- The SQL Lab's optional PostgreSQL connection (`SQL_LAB_POSTGRES_URL`) is a **completely separate**
  connection/credential from the application's own metadata database (`DATABASE_URL`) — no code path
  shares the two, by design (see `Settings.sql_lab_postgres_url`'s own comment).

## AI Layer (`apps/api/app/ai/security.py`, `gateway.py`)

- `redact_secrets` strips OpenAI/Anthropic-shaped keys, AWS access-key IDs, DB connection strings,
  JWT-shaped tokens, and `KEY=value` env-style lines from anything before it's used in a prompt.
- `strip_forbidden_keys` recursively removes any dict key containing `api_key`, `password`, `secret`,
  `token`, `database_url`, `connection_string`, `private_key`, `access_key`, or `credential` (case-
  insensitive substring match) from every AI context payload, at any nesting depth.
- `wrap_untrusted_data` wraps any dataset/user-authored text passed to a model in an explicit
  `<untrusted_data>` block instructing the model to treat it as data, never as instructions — the
  platform's prompt-injection defense.
- Provider calls carry a real timeout (`AI_REQUEST_TIMEOUT_SECONDS`, default 30s) and bounded retries
  (`AI_MAX_RETRIES`, default 2, only on 5xx/timeout, with exponential backoff).
- A daily request limit (`AI_DAILY_REQUEST_LIMIT`, default 200, per-user) is enforced before every
  dispatch, and every call is written to an append-only `AIAuditLog` (feature/provider/model/tokens/
  latency/success — never the full prompt, only a redacted preview).
- Provider API keys never reach the frontend — confirmed by inspection: the only occurrences of
  `AI_API_KEY`/`OPENAI`/`ANTHROPIC` anywhere under `apps/web` are UI label text, never a key value.

## Error handling & logging

- Every domain error in the backend raises through one `AppError` family (`NotFoundError`,
  `ConflictError`, or the base `AppError`) — **zero** call sites raise a raw `HTTPException` anywhere in
  the codebase. Every error response has the same shape: `{"error": {"code", "message", "details",
  "request_id"}}`.
- A request-id + duration logging middleware (`app/core/middleware.py`, added in Phase 12) assigns
  (or reuses an inbound `X-Request-ID` header for) every request, logs one line per request
  (`method`, `path`, `status`, `duration_ms`, `request_id`), and echoes the id back as a response
  header — so a slow or failing request can always be correlated to its own log line and to the
  `request_id` inside its own error response.
- Secrets are never logged: a repo-wide audit found no logger call anywhere that references an API
  key, database URL, or password field. `.env`/environment variables are the only place a real secret
  ever lives.

## CORS

`CORS_ORIGINS` defaults to `["http://localhost:3000"]` only — both locally and in `docker-compose.yml`.
Methods/headers are wide open (`*`) for that one allowed origin, which is the frontend's own origin.

## File uploads

- Dataset Hub imports sanitize filenames (`app/dataset_hub/security.py`): any path component is
  stripped (preventing `../../` traversal), null bytes/dotfiles/Windows-reserved device names are
  rejected, and the remainder is validated against an allowlist regex before ever touching disk.
- The Resume/JD "Uploaded" source label does not yet have a real file-upload code path behind it (see
  [Known Limitations](../README.md) in the final report) — choosing it in the UI reads the file's text
  content client-side and submits it through the same paste endpoint, never sending raw file bytes to
  the backend.

## What's explicitly out of scope for a local-first single-user app

- No general HTTP rate-limiting middleware exists (only the AI daily-request-limit and a Python Lab
  per-user concurrent-container cap). For a single local user with no exposed public endpoint, this is
  an accepted tradeoff, not an oversight — revisit before ever exposing this API beyond localhost.
- No authentication/authorization layer — the whole platform models exactly one local user
  (`UserService.get_current_user()`), consistent with every phase's design.
