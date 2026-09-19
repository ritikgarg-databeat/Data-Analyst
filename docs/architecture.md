# Architecture

## Overview

Data Lab is a monorepo with a clean separation between frontend, backend, database,
content, and infrastructure:

```
apps/web        Next.js (App Router) frontend
apps/api        FastAPI backend
packages/shared TypeScript types/constants shared across the frontend (API contract, nav, content types)
content/        Authored learning material (Markdown/YAML), referenced by the database
data/           Raw/processed/sample datasets
database/       Alembic migrations + YAML seed data
infrastructure/ Dockerfiles' supporting scripts, docker-compose helpers
tests/          Cross-cutting e2e and integration tests
docs/           This documentation
scripts/        Convenience CLI wrappers (migrate, seed, setup)
```

## Backend (`apps/api`)

Layered, in order of dependency:

```
routers/       FastAPI path operations only — no business logic, just request → service → response
services/      Business logic; the only layer that assembles response schemas from ORM models
repositories/  Thin SQLAlchemy data access, one per aggregate root
models/        SQLAlchemy ORM models (source of truth for schema; Alembic autogenerates from these)
schemas/       Pydantic response/request models — the API contract, mirrored 1:1 in packages/shared
dependencies/  FastAPI DI wiring (DB session, per-service factories)
core/          Config, database engine/session, error handling, logging
```

Routers depend on services (via `dependencies/services.py`), services depend on repositories,
repositories depend on models. Nothing skips a layer. `core/errors.py` defines a small hierarchy of
`AppError` subclasses (e.g. `NotFoundError`) that map to structured `{"error": {code, message,
details}}` JSON responses via global FastAPI exception handlers — routers and services never build
error responses by hand.

Primary keys are 36-char string UUIDs (`app/models/base.py::UUIDPrimaryKeyMixin`) rather than the
Postgres-only `UUID` column type. This is deliberate: it lets the exact same models run against
PostgreSQL (Docker/production) and SQLite (fast local `pytest` runs, ~0.5s for the full suite) without
dialect branching anywhere in the codebase. The same reasoning applies to enum columns
(`native_enum=False` — stored as plain strings) and the `datasets.metadata` JSON column (generic
`sa.JSON`, not `JSONB`).

### Multi-user authentication and isolation

FastAPI resolves the current user from short-lived JWT access cookies backed by rotating database
refresh sessions. Passwords are Argon2id hashes and never enter tokens. Unsafe authenticated requests
also require a double-submit CSRF token. User-owned rows are queried with the authenticated user id;
private datasets and dbt state live under `data/users/{user_id}`. Administrators have a separate,
audited management API and read-only data views, without impersonation.

### Content-driven, not hard-coded

`Lesson.content_reference` and `Exercise.content_reference` are plain string paths into `content/`.
The database never stores lesson body text — see `content/README.md` for the content architecture and
`content/schema/*.schema.json` for the file shapes.

## Content & Learning Engine (Phase 2)

### Content pipeline (`apps/api/app/content/`)

- `schema.py` — Pydantic models for lesson/exercise content files, including the 12-variant `ContentBlock`
  discriminated union (text, heading, callout, code, output, table, formula, image, example, question,
  checklist, comparison). This is the **real, enforced** validation source of truth — `content/schema/*.json`
  and `packages/shared/src/content-types.ts` are hand-maintained mirrors for docs/frontend typing.
- `loader.py` — discovers and parses every file under `content/lessons/**/*.yaml` and
  `content/exercises/**/*.yaml`, tolerantly (a bad file becomes a `ContentLoadError`, not a crash, so
  every problem can be reported in one pass).
- `validate.py` (`python -m app.content.validate`, or `scripts/validate-content.sh`) — loads everything,
  then cross-checks references (module/skill/dataset/tag/prerequisite/lesson_slug) against
  `database/seeds/*.yaml` and the other content files. Runs with **no database connection** required.
- `sync.py` (`python -m app.content.sync`, or `scripts/sync-content.sh`) — refuses to run if validation
  fails; otherwise upserts `Lesson`/`Exercise` rows plus their `Tag`/`LessonSkill`/`LessonPrerequisite`/
  `LessonDataset`/`RelatedLesson` relations by slug. A lesson/exercise previously synced but no longer on
  disk is **deactivated**, never deleted, so progress history referencing it survives. `app/db/seed.py`
  calls this automatically after seeding the taxonomy (domains/skills/modules/datasets/tags) — those stay
  YAML-seeded since they're structural, not rich authored content.

### Content file format: YAML, not Markdown+frontmatter

Phase 1 used Markdown+frontmatter for the two proof-of-concept lessons. Phase 2 lessons need 12 distinct
structured block types (a comparison table is not expressible as clean Markdown without inventing custom
directive syntax), so lesson/exercise files are pure YAML — the whole file is the parsed document, with a
`blocks:` list for the body. See any file under `content/lessons/` for the pattern, or
`content/lessons/data-analyst-foundations/how-to-use-this-lab/the-learning-loop.yaml` for a compact
example.

### Completion rules (`app/services/completion_rules.py`)

`Lesson.completion_criteria` (JSON: `{"type": "reading_percent"|"exercise_score"|"assessment_score",
"threshold": float}`, defaulting to `reading_percent` @ 90) is evaluated server-side whenever a client
requests `status: COMPLETED` (`ProgressService.upsert_lesson_progress`) — a request that doesn't meet the
threshold is silently downgraded to `IN_PROGRESS` rather than honored. This is the direct implementation
of "don't mark a lesson complete merely because it was opened."

### Prerequisites (`app/services/prerequisites.py`)

`LessonPrerequisite` rows carry an `is_hard_blocker` flag. Hard blockers lock a lesson
(`LessonContentResponse.is_locked`) until the prerequisite is `COMPLETED`; soft ones are informational
only. `content/**/*.yaml`'s `prerequisites:`/`soft_prerequisites:` lists map directly onto this at sync
time.

### Mastery (`app/services/mastery.py`)

`UserSkill.mastery_score` is recalculated after every graded `ExerciseAttempt`/`AssessmentAnswer` from a
weighted average of that skill's scored events — weighted by exercise difficulty (harder counts more) and
recency (30-day half-life decay), with a hint/solution-reveal penalty applied to each event's score before
weighting. `app.models.enums.mastery_level_for_score` maps the 0-100 score to
BEGINNER(<40)/DEVELOPING(<60)/INTERMEDIATE(<75)/STRONG(<90)/MASTERED via a single configurable threshold
table — not "one completed lesson = mastery."

### Recommendations (`app/services/recommendations.py`)

Fully deterministic, no AI: incomplete hard prerequisite of the user's next lesson → next lesson in the
user's current in-progress module → a lesson teaching the user's weakest practiced skill → any other
unfinished lesson → a completed lesson whose skill mastery has since dipped (review). Phase 10 is where
this becomes a real personalized/spaced-repetition engine.

### Search (`app/services/search.py`)

Case-insensitive `ILIKE` substring match across domain/module/lesson/skill/exercise title+description —
deliberately **not** Postgres `tsvector`/GIN, so the same search code path runs under the SQLite test
suite as production Postgres. `SearchService.search()`'s signature doesn't leak this choice, so a
`tsvector` or later semantic/vector search upgrade is a drop-in replacement behind the same interface, not
a rewrite — see the module docstring for the full reasoning.

### Assessments (`app/models/assessment.py`)

`Assessment` (attached to a `Module`) + `AssessmentQuestion` (a thin join to the existing `Exercise`
question bank, so there's no duplicate question model) + `AssessmentAttempt`/`AssessmentAnswer`. Grading
reuses `app/services/grading.py` (the same auto-grader exercises use) per question, weighted by each
question's `points`. Assessments are DB-seeded (`database/seeds/assessments.yaml`, loaded by
`app/db/seed.py` **after** content sync since it references exercise slugs) rather than content-file-driven,
since they're configuration (passing score, time limit, retry policy) rather than authored material.

### Admin scope is deliberately split

`Domain`/`Module`/`Skill`/`Tag` are database-owned — the admin API supports full create/update for them.
`Lesson`/`Exercise` are content-file-owned — admin can only `PATCH` `is_active`/`display_order` (reorder,
activate/deactivate); editing title/body/objectives means editing the YAML file and re-running
`sync-content`, by design, so the file-based content system and the admin UI never fight over who owns the
content.

## SQL Lab (Phase 3)

### Engine abstraction (`apps/api/app/sql/`)

`app/sql/engines/base.py` defines the shared `SqlEngine` ABC (`execute`, `list_tables`, `get_table_schema`,
`preview_table`) and the normalized result dataclasses (`SqlExecutionResult`, `TableSchema`,
`TablePreview`) every engine returns, regardless of backend. Two implementations:

- `engines/duckdb_engine.py` — the default/always-available engine. A fresh in-memory DuckDB connection
  per execution (never pooled — single-user local app, and it guarantees no state leaks between runs),
  with one `VIEW` per registered table pointing directly at its source CSV/Parquet/JSON file (data is
  never copied into DuckDB's own storage). Has no native `statement_timeout`, so cancellation is done via
  `ThreadPoolExecutor` + `future.result(timeout=...)` + `connection.interrupt()`.
- `engines/postgres_engine.py` — secondary/"architecturally available," using raw `psycopg` (not
  SQLAlchemy) against a **separate** `SQL_LAB_POSTGRES_URL`, deliberately never the app's own
  `DATABASE_URL` — this is what keeps user SQL from ever reaching `users`/`lesson_progress`/etc. Uses
  Postgres's own `read_only` transaction mode + `SET LOCAL statement_timeout`, both native mechanisms
  Postgres has and DuckDB doesn't. Reported `is_available: false` (not silently disabled) when
  unconfigured — see `GET /sql/engines`. **Not live-tested** in this environment (no Postgres instance
  available); verified by import/type-checking only.

`app/sql/registry.py` resolves an `(engine_name, database_name)` pair from the request into a live engine
instance — a DuckDB "database" is just a `Dataset` row that has one or more `SqlTable` children (see
below), so it's still a normal Phase 1/2 `Dataset` (shows up in `/datasets` too) with SQL-Lab-specific
metadata layered on.

### Safety (`app/sql/safety.py`)

A **denylist**, not an allowlist — deliberately. An early allowlist-of-leading-keywords design was
rejected during this phase: it swallowed a genuine typo ("SELCT") behind a generic "not allowed" message
instead of DuckDB's real, educational parser error, and it incorrectly rejected valid DuckDB FROM-first
syntax. The shipped version blocks only known write/DDL/admin keywords (`INSERT`, `UPDATE`, `DELETE`,
`DROP`, `ALTER`, `CREATE`, `ATTACH`, `COPY`, `PRAGMA`, ...) and multi-statement stacking (splits on `;`,
rejects more than one non-empty statement), then passes everything else through untouched so the engine's
own parser error surfaces verbatim. `app/sql/service.py::SqlExecutionService.execute` additionally enforces
`sql_lab_query_timeout_seconds` and `sql_lab_row_limit` (both configurable via `Settings`, not hard-coded)
on every execution.

### Dataset architecture

`SqlTable` (new model, `app/models/sql_lab.py`) extends a `Dataset` with the metadata needed to make it
SQL-queryable: one row per table, `file_path`/`file_format`, a human `grain` description, and
`row_count`/`column_count` computed from the real file at sync time (never hand-maintained) by
`app/sql/sync.py`, wired into `app/db/seed.py::seed()` right after the taxonomy seed. The registered
practice dataset is `ecommerce` — 8 CSVs generated deterministically by
`app/sql/generate_dataset.py` (`SEED = 20260301`, stdlib `random.Random` only, no pandas/Faker) with
enforced business-consistency invariants: referential integrity, temporal ordering (no order before its
customer's signup), and exact dollar reconciliation (`payments.amount` == the sum of that order's
`order_items` line revenue) — verified via direct DuckDB queries after generation, not just assumed.

### Exercise evaluation (`app/sql/evaluation.py`, `app/services/sql_exercise_service.py`)

Result-based, never SQL-text comparison, per the explicit Phase 3 requirement. A submission executes the
student's query and the exercise's authored `sql_solution_query` against the same live dataset, then
`compare_full_result()` diffs the two `SqlExecutionResult`s with configurable row-order independence and
numeric tolerance. Optional `sql_hidden_tests` are a lightweight alternative to per-test physical dataset
variants: each is a small SQL query (also run live) returning `[*key_columns, expected_value]` rows,
checked against a keyed lookup in the **student's own** result set — so hidden tests never need hardcoded
expected numbers and can't leak by inspecting the exercise's content file (only `business_context`,
`tables`, and `starter_query` are ever sent to the client — see `SqlExerciseContent`). Scoring
(`score_attempt`) weights Correctness 70 / Edge Cases (hidden tests) 15 / Efficiency (student vs. reference
execution time) 10 / Explanation 5, pass threshold 70.

Grading always runs the student's query against the **DuckDB** engine regardless of which engine the user
happens to be exploring with in the open Playground (`GRADING_ENGINE = "duckdb"` in
`sql_exercise_service.py`) — exercises are authored/verified against the checked-in CSVs, not a live
Postgres instance that may not even be configured.

Per the explicit reuse instruction for this phase, grading reuses the existing `ExerciseAttempt` model
(Phase 2) rather than a duplicate one — `SqlExerciseTestResult` (new) only carries the *additional*
per-test breakdown (name/passed/is_hidden/message), FK'd to `exercise_attempts.id`.

### Difficulty tiers vs. the `DifficultyLevel` enum

The curriculum's five conceptual tiers (Beginner/Easy/Intermediate/Advanced/Interview) are deliberately
layered on top of the existing three-value `DifficultyLevel` enum (`BEGINNER`/`INTERMEDIATE`/`ADVANCED`,
shared by every exercise type across the whole platform) rather than expanding that enum — expanding a
platform-wide enum for one exercise type's finer distinction would ripple into every other exercise/lesson
difficulty badge. Beginner and Easy exercises both persist as `difficulty: BEGINNER`; Advanced and
Interview both persist as `difficulty: ADVANCED`; the finer label lives in each exercise's `tags` (e.g.
`easy`, `interview`) and its `lesson_slug`/`skill` association. `database/seeds/tags.yaml` is a closed
vocabulary enforced by the content validator — new technique tags (`window-functions`, `ranking`,
`subqueries`) were added there deliberately rather than left as free text.

### API surface

All under `/api/v1/sql/*` — `engines`, `databases`, `databases/{db}/tables[/{table}/schema|/preview]`,
`execute`, `history` (+ delete), `workspaces` (+ create), `saved` (full CRUD), `exercises/{slug}`
(content, never the solution) and `exercises/{slug}/submit`. See `app/routers/sql.py` and
`app/schemas/sql.py` for the exact contract; `app/sql/converters.py` is the single place internal
dataclasses become their Pydantic API mirrors, shared by the router and the exercise service so that
mapping is never duplicated.

## Python Lab (Phase 4)

### Sandbox architecture: kernel, server, client, Docker

`infrastructure/docker/python-sandbox/` is a **self-contained** unit — zero imports from `app.*` — built
into its own Docker image (`infrastructure/docker/python-sandbox/Dockerfile`), never into the `api` image.
This isolation is deliberate: the API process itself has no ability to run pandas/numpy/etc at all (they
aren't even in `apps/api/pyproject.toml`'s main dependencies — see below), which is a second, structural
line of defense on top of the container boundary itself.

- **`kernel.py`** — the actual "run this code and return a structured result" engine (`PythonKernel`).
  Holds one persistent `globals` dict across many `.execute()` calls (that's what gives cells their
  notebook-like variable persistence), captures stdout, matplotlib figures (`plt.get_fignums()` after
  each execution → base64 PNG, then `plt.close("all")`), Plotly figures (monkeypatches
  `BaseFigure.show()` to record `.to_json()` instead of trying to open a browser), auto-displays a
  trailing bare expression the way a notebook cell does (`ast`-splits the code into "everything but the
  last statement" + "the last statement, if it's a bare expression"), and formats errors with only the
  student's own frames in the traceback (filters out frames from the `<cell>` synthetic filename that
  aren't the user's). A per-execution wall-clock timeout is enforced with `SIGALRM`/`signal.setitimer`
  (POSIX-only — the sandbox container always runs Linux regardless of host OS).
- **`server.py`** — the container's entrypoint (PID 1). Wraps one `PythonKernel` behind a **Unix domain
  socket**, not a TCP port — deliberately, so it keeps working with the container started
  `network_mode="none"` (see below), which removes the container's network stack entirely, including any
  published port.
- **`client.py`** — invoked via `docker exec <container> python /sandbox/client.py execute <base64-code>`
  from the host side. Connects to the socket *from inside the container's own namespace* and relays one
  request/response pair over that filesystem-based IPC channel, then exits — `docker exec`'s own stdout
  capture is the entire transport back to the host.

### `DockerRuntimeBackend` (`app/python_lab/docker_backend.py`) — the one production `PythonRuntimeBackend`

Every execution goes through a real Docker container of the sandbox image, created via `docker-py`
(`docker.from_env()`), configured with (all Settings-configurable, see `app/core/config.py`):
`network_mode="none"`, `mem_limit`, `nano_cpus`, `pids_limit`, `read_only=True` root filesystem (only
`/tmp`, a size-capped tmpfs, is writable), a non-root user baked into the image, `cap_drop=["ALL"]`,
`security_opt=["no-new-privileges"]`, and exactly one read-only bind mount (the practice datasets
directory → `/data`). The container's `environment` dict is built from scratch in this function — never
inherited from the API process's own environment — so `DATABASE_URL`/`SQL_LAB_POSTGRES_URL`/API keys are
structurally unreachable, not just "not intentionally passed" (verified directly in
`tests/test_python_lab_security.py`, which asserts on every argument this function passes to
`containers.run()` against a mocked `docker` module).

**Why `docker exec`, not a published port**: `network_mode="none"` makes port publishing impossible, so
the host talks to a running container through `docker exec` instead (rides the Docker daemon's own control
channel, not container networking) invoking `client.py`, which then talks to `server.py`'s Unix socket
*from inside* the container. This is what makes "genuinely no network access" compatible with still
running a persistent, stateful kernel across many calls.

**Docker-out-of-Docker gotcha (host paths vs. container paths)**: when running via `docker compose`, the
`api` container talks to the *host's* Docker daemon (via a mounted `/var/run/docker.sock`) to create
sandbox containers as its **siblings**, not its children. The daemon always resolves a volume-mount spec
against the **host** filesystem — never the caller's own container — so `api`'s own internal view of
`data/sample` (baked into its image at `/app/data/sample`) is *not* a valid mount source. `docker-compose.yml`
works around this by also bind-mounting `./data/sample` into `api` and setting
`Settings.python_lab_host_data_dir` to the matching **host-side** path string (`${PWD}/data/sample`),
which is what actually gets handed to sibling containers — see the comments in `docker-compose.yml` and
`app/core/config.py` for the exact mechanics, including the Windows `${PWD}` caveat.

### Execution model: scratch vs. exercise

Both modes share the exact same `PythonRuntimeManager`/`PythonExecutionService` (`app/python_lab/service.py`)
and the exact same kernel — there is no separate "safe subset" for exercises. **Scratch mode** is a
long-lived runtime tied to a `PythonWorkspace`, reused across many `execute()` calls from the UI.
**Exercise mode** (`app/services/python_exercise_service.py`) creates two short-lived, ephemeral runtimes
per submission — one for the student's code, one for the reference `python_solution_code` — each freshly
created and destroyed within the same request, so grading can never see anything the student defined and
vice versa. Both runtimes get an identical "dataset setup" preamble (`import pandas as pd`, plus one
`pd.read_csv(...)`/`read_parquet(...)` per referenced dataset file) before running their respective code,
so `orders`/`customers`/`payments`-style variables are pre-loaded exactly as the exercise's `prompt`
describes, mirroring the SQL Lab's pre-registered table views.

### Evaluation (`app/python_lab/evaluation.py`) — result-based, never source-text comparison

Mirrors `app/sql/evaluation.py`'s weights and philosophy exactly (Correctness 70 / Edge Cases 15 /
Efficiency 10 / Explanation 5, pass threshold 70) for platform consistency, generalized from "diff two SQL
result sets" to "compare the value of one named result variable" (`python_result_variable`, default
`"result"`): DataFrames (pandas or Polars) are compared column-set-then-cell-by-cell with configurable
row-order independence and numeric tolerance; scalars/lists/dicts are compared with the same tolerance
rules. **Hidden tests** (`python_hidden_tests`) are plain Python snippets — typically `assert` statements —
executed in the *student's own* kernel namespace (so they can reference `result` and anything else the
student defined) after correctness passes; they succeed if they run without raising and fail with the
raised exception's message otherwise. This is deliberately more general than SQL's keyed-row-lookup hidden
tests (Python results aren't always tabular), and needs no hardcoded expected values — a hidden test can
compute its own reference value live, the same way SQL's hidden queries do.

One real constraint this shapes: because `kernel.py` closes and captures matplotlib figures at the end of
*each* `execute()` call, a hidden test running in a *separate* `execute()` call after the student's own
submission can no longer inspect any chart the student's code produced (`plt.get_fignums()` is already
empty by then). Visualization exercises are therefore authored so `python_result_variable` captures the
chart's *underlying data* (e.g. the DataFrame that was plotted), not the figure object itself — hidden
tests check that, and the chart is graded implicitly by the same correctness check.

### Dataset integration

No new dataset model — `PythonExecutionService.list_datasets()` (`app/python_lab/service.py`) reuses
`Dataset` (Phase 1/2) and, where present, `SqlTable` (Phase 3) directly: a dataset with registered
`SqlTable` rows (e.g. `ecommerce`) surfaces one `PythonDatasetFile` per table; a plain `Dataset` with no
`SqlTable` children (e.g. `orders-sample`) surfaces its own single file. Every entry carries a
ready-to-paste `suggested_code` line (`pd.read_csv("/data/...")` etc.) matching the container-side mount
path, for the frontend's dataset browser to insert directly into the editor.

### Difficulty tiers, curriculum, and reuse

Same pattern as the SQL Lab: `ExerciseContentFile` gained a `# --- Python exercises only ---` block
(`python_datasets`, `python_starter_code`, `python_solution_code`, `python_result_variable`,
`python_row_order_matters`, `python_numeric_tolerance`, `python_hidden_tests: list[PythonHiddenTestSpec]`)
rather than a new content-file type, validated the same way (`app/content/validate.py`'s `PYTHON` branch).
Grading reuses the existing `ExerciseAttempt` model exactly as SQL did — `PythonExerciseTestResult` only
adds the per-hidden-test breakdown, FK'd to `exercise_attempts.id`. The curriculum spans the existing
`python-for-analysts` module (extended, never rewritten, from 8 to 14 lessons to reach its originally
intended Fundamentals scope) plus 10 new `python`-domain modules (NumPy, and 7 Pandas modules — DataFrames
Fundamentals, Data Cleaning, Transformation, Aggregation, Combining Data, Time Series, Advanced — plus
Polars and Exploratory Data Analysis) and one new module under the pre-existing (previously empty)
`data-visualization` domain.

### Runtime lifecycle and resource management

`PythonRuntime` rows track `STARTING`/`READY`/`BUSY`/`ERROR`/`STOPPED` status, `container_id` (the backend
handle), and `last_used_at`. Idle runtimes past `Settings.python_lab_runtime_idle_ttl_seconds` are reaped
opportunistically — on every `list_runtimes`/`create_runtime` call (`app/routers/python_lab.py`), not via a
background scheduler or an app-startup hook. That's a deliberate choice, not a simplification cut short: an
earlier version *did* sweep on FastAPI startup via a `lifespan` handler, but that handler needed its own DB
session independent of the request-scoped `get_db` dependency the test suite overrides — in a context
where only the override is ever meant to be reachable (like the test suite, which has no real Postgres),
that session construction hung the entire process trying to connect to the production `DATABASE_URL`
default. Opportunistic sweeping avoids needing any session outside a request's own DI-provided one.
`Settings.python_lab_max_concurrent_runtimes` caps how many runtimes one user can have active at once
(`PythonExecutionService.create_runtime`); exercise grading's ephemeral runtimes are explicitly exempted
from that cap (`count_toward_limit=False`) since they're always destroyed within the same request.

### What could and couldn't be verified in this environment

No Docker daemon was available while building this phase. What WAS verified for real: `kernel.py` directly
(`apps/api/tests/test_python_kernel.py`, importing the sandbox file straight into the API's own test
process against a real pandas/numpy/scipy/statsmodels/scikit-learn/matplotlib/seaborn/plotly — installed
via the `sandbox` extra in `apps/api/pyproject.toml`, never shipped in the `api` image), and the entire
rest of the stack (routers → services → evaluation → exercise grading) through
`tests/python_lab_fakes.py::InProcessKernelBackend`, a `PythonRuntimeBackend` that runs the same real
kernel in-process instead of in a container. What was **not** live-verified: `DockerRuntimeBackend` itself
— covered instead by mock-based tests asserting on the exact arguments it constructs for `docker-py`
(`tests/test_python_lab_security.py`), matching exactly how Phase 3 covered the Postgres SQL engine (no
live instance available there either).

## Frontend (`apps/web`)

See the frontend engineer's own report in the PR/commit history for exact conventions used; at a high
level it consumes `@data-analyst-lab/shared` for every API type and the nav structure, fetches through
TanStack Query against the same-origin `/api/v1` gateway, and renders consistent
loading/empty/error states across every data-driven page. The gateway forwards to the private
`API_PROXY_TARGET`, keeping authentication and CSRF cookies on the web application's host.

## Why a shared `packages/shared`

`packages/shared/src/types.ts` is the single source of truth for the API's JSON shape, written by hand
to match the Pydantic schemas in `apps/api/app/schemas/`. There is no codegen step in Phase 1 — the two
are kept in sync manually, which is acceptable at this scale but is a natural candidate for an
OpenAPI-codegen step in a later phase if the contract grows large enough to drift.

## Database & migrations

- Alembic lives at the repo root (`alembic.ini`) with `script_location = database/migrations` —
  **must be run from the repo root** (`scripts/migrate.sh` does this for you). A relative
  `script_location` containing `..` breaks Mako's template lookup on Windows, which is why `alembic.ini`
  is at the root rather than inside `apps/api`.
- `database/seeds/*.yaml` holds the foundational, structural taxonomy: domains, skills, modules
  (shells), datasets, tags, and assessments. `apps/api/app/db/seed.py` loads and upserts them by
  natural key (slug/email), then runs the content sync (see above) for lessons/exercises — safe to
  re-run.

## Docker

Three services: `postgres`, `api`, `web`. The `api` image's entrypoint
(`infrastructure/docker/api-entrypoint.sh`) applies migrations on every boot (idempotent) before
starting Uvicorn; seeding is a deliberate separate step (`scripts/seed.sh` or
`docker compose exec api uv run python -m app.db.seed`) so seed-data changes are always an explicit
action, never a silent side effect of restarting a container.

## Cross-cutting Platform layer (Phase 12)

A `/api/v1/platform/*` router (`apps/api/app/routers/platform.py`) holds capabilities that don't belong
to any single domain — every one of them is a thin composition over existing services, never a new
scoring system:

- **Next Best Action** (`services/next_best_action_service.py`) — merges the single highest-signal item
  from five already-independent recommendation sources (lesson recommendations, interview weakness
  detection, active-JD skill gaps, portfolio gap detection, career goals) into one small, capped,
  ranked list. A Phase 12 audit found these five systems existed in complete isolation from each other
  before this.
- **System Health** (`services/system_health_service.py`) — a dependency-aware check (database, DuckDB,
  the optional SQL Lab Postgres engine, the Python sandbox, dbt, the AI provider, Kaggle), distinct from
  the pre-existing `GET /api/v1/health`, which is a pure process-liveness check with no dependency
  awareness at all.
- **Data Integrity Audit** (`services/data_integrity_service.py`) — SQLite's foreign-key enforcement is
  not enabled in this app, so this actually checks for orphaned references and duplicate skill slugs
  rather than assuming they can't happen.
- **Job-Ready Checklist** (`services/job_ready_checklist_service.py`) — a real, evidence-based version
  of the spec's example checklist (Technical/Analytics/Data Stack/Applied/Interview/Career), every item
  a genuine boolean derived from mastery scores, completed cases/projects/interviews, and career state.
- **Backup / Restore** (`services/backup_service.py`) — see [`docs/backup-restore.md`](backup-restore.md).

A request-id + duration logging middleware (`app/core/middleware.py`) and an expanded, 9-kind global
search (`app/services/search.py`, up from 5) round out the layer — see
[`docs/security.md`](security.md) and [`docs/troubleshooting.md`](troubleshooting.md).
