# Personal Data Analyst Lab

A local-first, single-user, production-quality personal learning and practice platform for becoming
and staying job-ready as a modern Data Analyst — roughly the 2-year experience level, aimed at strong
product/business/data analytics roles.

This is not a generic course platform. It's an end-to-end environment built around one loop:

```
LEARN → PRACTICE → APPLY → GET EVALUATED → IDENTIFY WEAKNESS → REVIEW → REATTEMPT → MASTER → INTERVIEW
```

The platform optimizes for **"can I independently solve a real business problem using data?"**, not
"did I finish a course?". See [`docs/roadmap.md`](docs/roadmap.md) for the full 12-phase build plan —
this repository implements **all 12 phases**, from the foundational content/learning engine and
SQL/Python/Excel/dbt labs through the Dataset Hub, Statistics/Experimentation/Business/Product Analytics
layer, the Case Study & Project Engine, the Interview & Assessment Engine, the AI Mentor/Tutor/Coaching
layer, the Career Readiness/Portfolio/Resume layer, and a final cross-cutting Platform layer (unified
navigation, a Next Best Action engine, System Health, Backup/Restore, a command palette) that integrates
all of the above rather than adding an unrelated 12th domain (see `docs/roadmap.md`'s phase table for
what each one shipped).

## Overview

- **Frontend**: Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui-style components +
  TanStack Query, at `apps/web`.
- **Backend**: FastAPI + SQLAlchemy 2.0 + Alembic + Pydantic, at `apps/api`.
- **Database**: PostgreSQL (production/Docker), with tests running against SQLite for speed.
- **Content**: YAML lesson & exercise content (12 structured content-block types) under `content/`,
  kept out of the database and out of React components, validated and synced by
  `apps/api/app/content/` — see [`content/README.md`](content/README.md) and
  [`docs/architecture.md`](docs/architecture.md#content--learning-engine-phase-2).
- **Learning engine**: prerequisites, server-enforced completion rules, exercises with progressive
  hints, assessments, skill mastery scoring, deterministic recommendations, and search — see
  [`docs/architecture.md`](docs/architecture.md).
- **SQL Lab**: a DuckDB (default) + PostgreSQL (secondary) query execution engine behind one interface,
  a Monaco-based SQL Playground (schema explorer, results grid, history, saved queries), real-execution
  SQL exercise grading (result-based, never text comparison) against a realistic 8-table synthetic
  e-commerce dataset — see [`docs/architecture.md`](docs/architecture.md#sql-lab-phase-3).
- **Python Lab**: a Docker-isolated Python execution sandbox (network-disabled, resource-capped,
  non-root, read-only root filesystem — see [Requirements](#requirements)) running
  Pandas/NumPy/Polars/PyArrow/SciPy/Statsmodels/scikit-learn/Matplotlib/Seaborn/Plotly, a notebook-like
  multi-cell Python Lab UI (DataFrame viewer, variable explorer, chart rendering), and real-execution
  Python exercise grading — see [`docs/architecture.md`](docs/architecture.md#python-lab-phase-4).
- **Case Studies & Projects**: multi-stage, deliberately ambiguous business-problem simulations and
  milestone-driven capstones, scored by a deterministic rubric engine — see
  [Case Studies & Projects](#case-studies--projects).
- **Interview & Assessment Engine**: SQL/Python/Excel/Statistics/A-B-Testing/Product/Business/Behavioral
  interview rounds, mock interviews, server-validated timers, and deterministic readiness/weakness
  scoring — see [Interview Engine & Excel Lab](#interview-engine--excel-lab).
- **AI Layer**: a provider-agnostic AI Mentor/Tutor/Coach/Interviewer (OpenAI/Anthropic/local, the last
  needing no API key) layered on top of every deterministic engine above — never a second scoring
  system — plus a lightweight local knowledge-search RAG. See [AI Layer](#ai-layer).
- **Infrastructure**: Docker Compose (`postgres`, `api`, `web`, plus a build-only `python-sandbox` image).

See [`docs/architecture.md`](docs/architecture.md) for a deeper walkthrough of each layer.

## Requirements

- [Docker](https://www.docker.com/) + Docker Compose (recommended path — no other local installs needed).
  **The Python Lab specifically requires Docker** — it's the actual execution sandbox, not an optional
  extra (see [Python Lab](#python-lab)); every other feature (learning content, SQL Lab, progress) works
  without it.
- Or, for local (non-Docker) development: Node.js ≥ 20, Python ≥ 3.12, [uv](https://docs.astral.sh/uv/),
  and a local PostgreSQL instance — the Python Lab will report itself unavailable in this mode unless you
  separately have Docker running and reachable

## Installation

```bash
git clone <this-repo>
cd data-analyst-lab
cp .env.example .env
```

### Option A — Docker (recommended)

```bash
docker compose up --build
```

This builds and starts `postgres`, `api` (applying migrations automatically on boot), and `web`. Once
healthy:

```bash
docker compose exec api uv run python -m app.db.seed   # first run only — populates seed data
docker compose build python-sandbox                     # once — the Python Lab's execution image (not auto-built by `up`)
```

- Frontend: http://localhost:3000
- API: http://localhost:8000 (docs at http://localhost:8000/docs)

### Option B — Local development (no Docker)

Requires a running PostgreSQL instance reachable at the `DATABASE_URL` in your `.env`.

```bash
npm install                                  # installs apps/web + packages/shared (npm workspaces)
uv sync --project apps/api --extra dev       # installs the backend virtualenv

./scripts/migrate.sh                         # apply migrations
./scripts/seed.sh                            # seed foundational content

npm run dev:web                              # frontend dev server → http://localhost:3000
uv run --project apps/api uvicorn app.main:app --reload --app-dir apps/api  # API → http://localhost:8000
```

`scripts/setup.sh` runs the install + migrate + seed steps above in one shot (assumes Postgres is
already reachable).

## Database

Migrations live at `database/migrations` (Alembic), configured via the **repo-root** `alembic.ini` —
always run Alembic from the repo root (the provided scripts do this for you):

```bash
./scripts/migrate.sh      # apply all pending migrations
./scripts/seed.sh         # idempotent — safe to re-run; upserts by slug/email
```

To create a new migration after changing a model in `apps/api/app/models/`:

```bash
uv run --project apps/api alembic -c alembic.ini revision --autogenerate -m "describe the change"
```

Seed data lives in `database/seeds/*.yaml` — **domains, skills, module shells, datasets, tags, and
assessments** (structural taxonomy). Lessons and exercises are *not* seeded from YAML — they're authored
as content files and synced in (see below).

## Content

Lesson and exercise content lives under `content/lessons/` and `content/exercises/` as YAML files, cases
under `content/cases/`, project templates under `content/projects/`, and interview questions/templates
under `content/interview/{questions,templates}/` (see [`content/README.md`](content/README.md) for the
full authoring guide and block-type reference). After editing content:

```bash
./scripts/validate-content.sh   # or .ps1 — schema + cross-reference checks, no DB needed
./scripts/sync-content.sh       # or .ps1 — upserts Lesson/Exercise rows from content/ (requires migrate+seed already run once)
```

`./scripts/seed.sh` already runs both of these for you on a fresh setup — only run `sync-content`
standalone when you've edited content and want to push the change without a full reseed. A
[`Makefile`](Makefile) wraps all of these (`make validate-content`, `make sync-content`, ...) for
machines with `make` installed; the `scripts/` versions are the primary, always-available path.

## SQL Lab

The SQL Lab (`/sql-lab`) queries `data/sample/ecommerce/*.csv` directly via DuckDB — no server process,
no copying data in. A second practice database, `data/sample/saas_product/*.csv` (users/events/
subscriptions/experiment_assignments), backs the Phase 6 Statistics/Experimentation/Product Analytics
curriculum — funnels, cohort retention, and the two built-in A/B experiments (`checkout_redesign`,
`onboarding_email`). Both are checked in and regenerated deterministically (same `SEED`, same output
every time) if you ever need to:

```bash
uv run --project apps/api python -m app.sql.generate_dataset       # regenerate data/sample/ecommerce/*.csv
uv run --project apps/api python -m app.sql.generate_saas_dataset  # regenerate data/sample/saas_product/*.csv
uv run --project apps/api python -m app.sql.sync                   # recompute row/column counts into sql_tables
```

`./scripts/seed.sh` already calls the sync step for you on a fresh setup. PostgreSQL is a secondary,
optional SQL Lab engine — set `SQL_LAB_POSTGRES_URL` in `.env` to a **separate** database/credentials
(never your app's own `DATABASE_URL`) to enable it; left unset, `/sql-lab` simply reports it unavailable
and DuckDB remains the default.

## Python Lab

The Python Lab (`/python-lab`) runs every submitted Python program inside an isolated, ephemeral Docker
container of the `python-sandbox` image (`infrastructure/docker/python-sandbox/`) — network disabled,
memory/CPU/process-count capped, read-only root filesystem, non-root user. The `api` process itself never
imports pandas/numpy/etc and has no ability to execute arbitrary Python on its own; it only orchestrates
sandbox containers via the Docker socket. Build the image once (not part of `docker compose up`, since
it's an on-demand template, not a long-running service):

```bash
docker compose build python-sandbox
```

Practice datasets are mounted read-only into every sandbox from `data/sample/` (the same files the SQL
Lab uses). On Docker Compose specifically, if `PYTHON_LAB_HOST_DATA_DIR` (see `.env.example`) doesn't
auto-resolve correctly on your platform, set it explicitly to your repo's absolute `data/sample` path —
see [`docs/architecture.md`](docs/architecture.md#python-lab-phase-4) for exactly why this is needed
(Docker-out-of-Docker volume mounts always resolve against the *host* filesystem).

To work on the sandbox's execution engine itself (`infrastructure/docker/python-sandbox/kernel.py`)
without rebuilding the image every time, install the `sandbox` extra locally and run its test suite
directly:

```bash
uv sync --project apps/api --extra dev --extra sandbox
cd apps/api && uv run pytest tests/test_python_kernel.py -v
```

## dbt Lab

The dbt Lab (`/dbt-lab`) runs a real, local dbt Core project — `dbt/` at the repo root — against DuckDB,
with **no cloud warehouse and no Docker**. `dbt-core`/`dbt-duckdb` are core `apps/api` dependencies (see
`apps/api/pyproject.toml`), so `uv sync --project apps/api --extra dev` installs everything needed. The
API shells out to the real `dbt` executable installed in that same virtualenv (`app/dbt_lab/runner.py`)
and reads dbt's own `target/manifest.json`/`catalog.json`/`run_results.json` for lineage, docs, and test
results — nothing about a run, a lineage edge, or a test result is simulated.

The project reads `data/sample/ecommerce/*.csv` directly (`dbt-duckdb`'s `external_location`, no separate
load step) and writes to `data/warehouse/dev.duckdb` by default. Both paths are resolved by
`app/dbt_lab/paths.py` and can be overridden via the `DBT_DATA_DIR`/`DBT_WAREHOUSE_PATH` env vars (mainly
useful for tests, which point `DBT_WAREHOUSE_PATH` at a scratch file so runs never touch the dev
warehouse). To drive the same project directly from a terminal instead of the UI:

```bash
cd dbt
DBT_DATA_DIR="/absolute/path/to/data/sample/ecommerce" DBT_WAREHOUSE_PATH="/absolute/path/to/data/warehouse/dev.duckdb" \
  uv run --project ../apps/api dbt build --profiles-dir profiles
```

(On Windows, use real Windows-style paths — `C:/Users/you/...` — even under Git Bash; DuckDB rejects
MSYS-style `/c/Users/...` paths.) dbt exercises (`exercise_type: DBT`) are graded the same way: a
submission is written to `dbt/models/exercises/<model>.sql` (plus a generated `schema.yml` for that
exercise's tests) and graded by an actual `dbt build --select <model>` — see
`app/services/dbt_exercise_service.py`.

## Case Studies & Projects

Case Studies (`/case-studies`) and Projects (`/projects`) are content-authored the same way as lessons/
exercises — YAML files under `content/cases/` and `content/projects/`, synced via the same
`validate-content`/`sync-content` scripts above. A Case is a multi-stage, deliberately ambiguous business
problem: the stakeholder's framing, hints, and rubric are served to the learner as they go, but the
`reference_solution` is withheld until the attempt is submitted (`POST /cases/{slug}/start`, then
`PATCH`/`POST .../attempts/{id}/...` through Clarify → Frame → Analyze → Recommend → Communicate & Submit).
A Project instantiates a longer, milestone-driven capstone from a `ProjectTemplate`
(`POST /projects/from-template`), referencing the SQL Lab/Python Lab/EDA Workspace/Data Modeler/dbt Lab
rather than duplicating them. Both share one Findings/Hypothesis Tracker/Evidence system
(`GET/POST /findings`, `/hypotheses`, `.../evidence`) and one rubric-scoring engine
(`app/case_engine/grading.py` — each rubric category is either self-assessed or, if marked
`is_technical`, scored objectively from real `ExerciseAttempt` pass/fail). Evaluation is entirely
deterministic — no AI/LLM call anywhere in this phase; see `docs/roadmap.md`'s Phase 8 entry for what's
deliberately deferred to later phases.

## Interview Engine & Excel Lab

Interview Prep (`/interview`) is a dedicated readiness system layered on top of every other phase's
grading rather than a second one. An `InterviewQuestion` (`content/interview/questions/*.yaml`) is a thin
wrapper around an existing `Exercise` — real SQL/Python execution, the real Excel formula engine, or
MC/short-answer/rubric-self-assessment grading, all reused as-is (`app/interview_engine/` and
`app/excel_lab/` add zero new grading paths of their own). An `Interview` (`POST /interviews`, then
`.../start`, `.../answer`, `.../pause`/`.../resume`, `.../submit`) tracks a state machine
(`NOT_STARTED → IN_PROGRESS ⇄ PAUSED → COMPLETED`/`ABANDONED`) with server-side-only elapsed-time
tracking — the client's timer is a display only; the API always computes and enforces elapsed time from
its own stored timestamps and auto-submits once a limit is exceeded. `InterviewTemplate`
(`content/interview/templates/*.yaml`) defines a multi-round Mock/Company-Style structure; a `CASE_STUDY`
round reuses the Phase 8 Case Workspace directly via a `case_attempt_id` FK rather than a third question
format. Five pure functions in `app/interview_engine/{scoring,readiness,weakness,selection,plan,
spaced_review}.py` implement the 6-dimension weighted scorecard, the readiness formula (mastery + capped
recent performance + consistency), 5-type weakness detection, deterministic adaptive question selection,
7-day plan generation, and a spaced-review interval formula — every one deterministic, no AI/LLM call
anywhere in this phase (see `docs/roadmap.md`'s Phase 9 entry for exactly what's deferred to later
phases). The Excel Lab (`app/excel_lab/formula_engine.py`) is a real, from-scratch tokenizer/parser/
evaluator (not a simulated grader) covering ~34 functions (SUMIFS, XLOOKUP, INDEX/MATCH, IFERROR, TEXT,
date functions, cross-sheet references) behind a lightweight spreadsheet grid — deliberately not a full
Excel clone.

## AI Layer

A reasoning/coaching layer (`apps/api/app/ai/`) on top of every deterministic engine above it — it
never recomputes or overrides a real score; see `app/ai/AUTHORITY.md` for the exact boundary. An
`AIProvider` protocol (`app/ai/provider.py`) is resolved by one factory (`app/ai/providers/factory.py`)
from `AI_PROVIDER`/`AI_MODEL`/`AI_API_KEY` env vars — `openai`/`anthropic` are thin direct `httpx` REST
clients (no SDK dependency), and `local` (the default, needing no key or network access at all) is a
deterministic placeholder so the whole platform — and this phase's own test suite — works with zero AI
configuration. `app/ai/gateway.py` is the single choke point every AI feature calls through: Context
Builder → Provider → Response Validator, never touching a database itself, never trusting a provider's
output blindly (a malformed/off-schema JSON response degrades to `structured_valid: false` rather than
crashing). `app/ai/context.py` builds small, bounded context payloads from real already-fetched domain
objects (never a database dump), passed through `app/ai/security.py` (secret redaction, forbidden-key
stripping, `<untrusted_data>` prompt-injection wrapping) before ever reaching a prompt. 25 versioned
prompt templates (`app/ai/prompts/`) cover a Socratic AI Mentor with a 4-level hint ladder, SQL/Python
"Ask AI" (tutor/review/debug/optimize — never auto-replacing the user's query/code), natural-language-
to-SQL/Python (generated and shown, only executed after explicit user confirmation), analysis/insight
review, an EDA assistant, one shared Domain Coach for Statistics/Experimentation/Product/Business
Analytics/Data Modeling/dbt, an AI Case Coach (4 coaching modes) and a conversational AI Case
Interviewer (grounded in a case's own real `clarification_guidance`, never inventing a data value),
a Behavioral Interviewer, an Interview Debrief (narrates the real, already-computed `Interview.score`),
Communication/Storytelling/Executive-Summary coaches, a Learning Planner explanation layer (explains
the real deterministic 7-day plan, never generates a different one), AI Skill Diagnosis and AI Mistake
Memory (both stored separately from real `UserSkill.mastery_score`), and an AI Project Review. A
lightweight local RAG (`app/ai/retrieval.py` — plain TF-IDF + cosine similarity over real lesson content
and the Metrics Library, computed with `numpy`, no vector database) grounds a Knowledge Search feature
with real citations. A persistent AI Mentor launcher (every route) and per-feature "Ask AI" panels (SQL
Lab, Python Lab, Case Workspace, Interview Review) make it reachable from the frontend; AI Settings
(`/settings`) covers enable/disable, provider override, response style, learning mode, and privacy
preference — see `docs/roadmap.md`'s Phase 10 entry for exactly what's deliberately deferred.

## Career Layer

A career-readiness and job-preparation layer (`/career`, `apps/api/app/routers/{career,jobs,resume,
portfolio}.py`) answering "am I ready, what are my gaps, how do I prepare for this specific job?" —
entirely on top of the existing mastery/interview-readiness engines and the Phase 10 AI layer, never a
competing scoring system. A **JD Analyzer** matches a pasted job description's text against the real
skill taxonomy deterministically (works with zero AI configuration), optionally enriched by a new
`JD_EXTRACTION` AI feature whose suggested skills are always re-validated against real `Skill` rows —
producing a live **Skill Gap table**, a configurable-weight **JD Readiness Score** (explicitly a platform
estimate, never a hiring guarantee), a real **Preparation Plan** (recommended exercise/case/project-
template slugs per gap) and JD-specific **Interview Plan**, plus a **Job Preparation Workspace** and
**JD Comparison**. A **Resume Analyzer** extracts evidence as verbatim quoted resume lines only (never a
fabricated metric or employer), scores quality/clarity/impact deterministically (AI only adds qualitative
suggestions on top), and runs Resume Gap Analysis against a target role. A **Portfolio Builder** defaults
every new item to PRIVATE, with a deterministic Quality Score and Portfolio Gap Detection. An 8-dimension
**Career Readiness Rubric** (Technical/Analytical/Business/Product/Data-Engineering-Awareness/
Communication/Interview/Portfolio) computes a gated Final Readiness Level — one strong dimension can
never mask a real weakness elsewhere — with a per-dimension "why" explanation and an explicit non-
guarantee disclaimer. A **Career Skill Matrix** (real evidence counts + a 5-level Evidence-Based Mastery
label), an auto-generated **Career Progress Timeline**, a **Career Goal Planner**, a 10-badge
**Achievement System**, a 12-category **Behavioral Story Bank**, a **Career Knowledge Base**, a **Weekly
Review**, an exportable **Career Report**, and an **AI Career Coach** (`CAREER_COACH`) round out the
layer — see `docs/roadmap.md`'s Phase 11 entry for exactly what's deliberately deferred.

## Platform Layer

A cross-cutting layer (`/api/v1/platform/*`, `apps/api/app/routers/platform.py`) that integrates all 11
prior phases rather than adding a 12th domain — every capability below is a thin composition over
existing services, never a new scoring system. Navigation was unified into one 10-section structure
(Main/Learn/Analyze/Data Stack/Cases & Projects/Interview/AI/Career/Knowledge/Settings, 42 routes total,
`packages/shared/src/constants.ts`'s `NAV_SECTIONS`) replacing 11 phases' worth of organically-grown
top-level routes, paired with a global command palette (Ctrl/Cmd+K) listing every real nav destination
plus a handful of verified quick actions. A **Next Best Action** engine merges the single highest-signal
item from five previously-isolated recommendation sources (lesson recommendations, interview weakness
detection, active job-description skill gaps, portfolio gap detection, career goals) into one small,
ranked dashboard card. A dependency-aware **System Health** check (database, DuckDB, the optional SQL
Lab Postgres engine, the Python sandbox, dbt, the AI provider, Kaggle) is distinct from the pre-existing
pure-liveness `GET /api/v1/health`. A **Data Integrity Audit** runs 13 real orphaned-reference/duplicate-
slug checks (meaningful because this app's SQLite backend never enables foreign-key enforcement), and a
**Job-Ready Checklist** turns the spec's example checklist into ~20 real, evidence-based boolean items
across 6 groups. The platform's first **Backup/Restore** system exports every row that's genuinely yours
(progress, attempts, projects, cases, career/interview/AI state — never secrets, dataset files, or
generated warehouse artifacts) to one timestamped JSON bundle, restores idempotently by primary key, and
never writes anything without an explicit preview + confirmation step — see
[`docs/backup-restore.md`](docs/backup-restore.md). A request-id + duration logging middleware
(`app/core/middleware.py`) means every error response and server log line now carries a correlating
`request_id`. Global search expanded from 5 to 9 content kinds (adding cases, projects, interview
questions, and metrics) behind a dedicated `/search` page. Settings became tabbed
(Profile/Appearance/AI/Data/System) to hold the new System Health and Backup/Restore panels alongside
the existing preferences — see [`docs/security.md`](docs/security.md) and
[`docs/troubleshooting.md`](docs/troubleshooting.md) for the full security/ops picture, and
`docs/roadmap.md`'s Phase 12 entry for exactly what's deliberately deferred.

## Development

- Backend hot-reload: `uv run --project apps/api uvicorn app.main:app --reload --app-dir apps/api`
  - **Always run backend commands from `apps/api`, or set `DATABASE_URL` explicitly.** `app/core/config.py`
    resolves `.env` relative to the process's current working directory, not relative to `config.py`
    itself. `apps/api/.env` holds the correct local `DATABASE_URL` (a SQLite file); the repo root has no
    `.env` (only `.env.example`). Any DB-touching command launched from the repo root without an explicit
    `DATABASE_URL` silently falls back to `Settings`'s hardcoded Postgres default and then hangs
    indefinitely trying to connect to a Postgres server that isn't running — `/api/v1/health` still
    responds instantly because it never opens a DB connection, which is what makes this look like a
    request-specific hang rather than a config issue. Fix: `cd apps/api` first, or pass
    `DATABASE_URL="sqlite:///$(pwd)/data/dev.db"` explicitly.
- Frontend hot-reload: `npm run dev:web`
- API interactive docs: http://localhost:8000/docs (Swagger) once the API is running
- Lint/format backend: `uv run --project apps/api ruff check .` / `ruff format .`
- Lint/typecheck frontend: `npm run lint:web` / `npm run typecheck:web`

## Testing

```bash
# Backend — pytest against an in-memory SQLite DB (migrated schema + full seed data)
uv run --project apps/api pytest -v

# Frontend — Vitest + Testing Library
npm run test:web

# End-to-end — Playwright, against a running frontend + seeded API
# (start `docker compose up` or the local dev servers first, then:)
npm run e2e
```

## Project structure

```
apps/
  web/            Next.js frontend
  api/            FastAPI backend (routers → services → repositories → models)
    app/ai/       Phase 10 AI layer — provider/gateway/context/security/retrieval/prompts (deterministic
                  engines it coaches around, e.g. app/interview_engine/, app/case_engine/, are unchanged)
    app/models/career.py, app/services/{career_*,jd_service,resume_service,portfolio_service,
                  achievement_service,ai_career_service}.py, app/routers/{career,jobs,resume,portfolio}.py
                  Phase 11 Career layer — reuses UserSkill/Project/Case/Interview data, never recomputes it
packages/
  shared/         TypeScript types/constants shared by the frontend, mirroring the API contract
content/
  lessons/<domain>/<module>/<lesson>.yaml   Lesson content (12 content-block types)
  exercises/<domain>/<exercise>.yaml        Exercise content (prompt/hints/solution)
  cases/<case-slug>.yaml                    Phase 8 Case Study Engine content (35 cases: 20 general +
                  15 short interview-specific ones tagged "interview", reused by Phase 9's Case Study
                  interview rounds with zero new backend code)
  projects/<template-slug>.yaml             Phase 8 Project Engine templates (8 templates)
  career/role_templates/<slug>.yaml         Phase 11 — generic Role Templates (7: Data/Product/Business/
                  BI/Marketing Analyst, Analytics Engineer Entry/Intermediate)
  interview/
    questions/<category>/<slug>.yaml        Phase 9 — thin wrappers around an existing exercise
                  (335 questions across 10 required + 2 bonus categories)
    templates/<template-slug>.yaml          Phase 9 — Mock/Company-Style multi-round structures (6)
  schema/         JSON Schema mirrors of apps/api/app/content/schema.py
  case-studies/   Phase 6's lighter "Analytics Cases" (a rubric-scored Exercise subtype — distinct
                  from Phase 8's cases/ above, which are a full multi-stage workspace)
  datasets/ domains/ modules/    Reserved for later phases (domains/modules/datasets are
                  actually seeded from database/seeds/*.yaml, not from content/)
  Authored learning content — see content/README.md
data/
  raw/ processed/ sample/     Dataset files (sample/ is seeded; raw/processed/ are Phase 5+)
  sample/ecommerce/           SQL Lab + Python Lab's shared practice dataset (8 CSVs)
  sample/saas_product/        Phase 6's second practice dataset — funnels/cohorts/A-B tests (4 CSVs)
database/
  migrations/     Alembic (script_location target; alembic.ini lives at repo root)
  seeds/          YAML seed data (domains/skills/modules/datasets/tags/metrics/assessments/achievements) —
                  NOT lessons/exercises
infrastructure/
  docker/
    api-entrypoint.sh          Container entrypoint script
    python-sandbox/            The Python Lab's execution image — kernel.py/server.py/client.py + Dockerfile
tests/
  e2e/            Playwright smoke tests (one spec per phase, e.g. case-studies.spec.ts, interview-engine.spec.ts,
                  ai-layer.spec.ts)
  integration/    Reserved for cross-service integration tests (see tests/integration/README.md)
docs/
  architecture.md roadmap.md
scripts/
  migrate.sh/.ps1  seed.sh/.ps1  setup.sh
  validate-content.sh/.ps1  sync-content.sh/.ps1     Convenience wrappers
Makefile          Wraps the scripts above for machines with `make`
docker-compose.yml
.env.example
```

## Roadmap

| Phase | Focus |
|---|---|
| 1 | **Foundation & architecture** *(this repo)* |
| 2 | **Learning/content engine + curriculum structure** *(this repo)* |
| 3 | **SQL Lab — DuckDB/PostgreSQL execution + exercises + evaluation** *(this repo)* |
| 4 | **Python Analytics Lab — Docker sandbox + Pandas/NumPy/Polars + exercises** *(this repo)* |
| 5 | **Dataset Hub — Kaggle/import + profiling + EDA/Visualization workspaces** *(this repo)* |
| 6 | **Statistics + experimentation + business/product analytics** *(this repo)* |
| 7 | **Data engineering + warehousing + data modeling + dbt Lab** *(this repo)* |
| 8 | **Case Study Engine + end-to-end Project Engine** *(this repo)* |
| 9 | **Interview & Assessment Engine — SQL/Python/Excel/statistics/A-B-testing/product/business/behavioral, mock interviews, readiness scoring** *(this repo)* |
| 10 | **AI Mentor/Tutor/Coach/Interviewer layer — provider-agnostic (OpenAI/Anthropic/local), Socratic tutoring, SQL/Python review, natural-language-to-SQL/Python, case & behavioral interviewing, interview debrief, learning-plan explanation, knowledge-search RAG** *(this repo)* |
| 11 | **Career Readiness, Portfolio, Resume/JD Intelligence & Job Preparation — JD analyzer with configurable-weight readiness scoring, resume analyzer, portfolio builder, an 8-dimension gated readiness rubric, career skill matrix, goals/timeline/achievements, behavioral story bank, AI career coach** *(this repo)* |
| 12 | **Final Integration, Production Hardening & Job-Ready Data Analyst OS — unified 10-section navigation + command palette, a Next Best Action engine, System Health, Data Integrity Audit, Job-Ready Checklist, Backup/Restore, request-id logging, 9-kind global search** *(this repo)* |

See [`docs/roadmap.md`](docs/roadmap.md) for details on what each phase deliberately defers.
