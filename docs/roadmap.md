# Roadmap

Data Lab is built in 12 phases. Each phase builds on the foundation without requiring
a rewrite of prior work.

| Phase | Focus |
|-------|-------|
| 1 | **Foundation & architecture** — monorepo, FastAPI + Next.js shells, PostgreSQL schema, Docker, migrations, seed data, content architecture, initial tests. *(done)* |
| 2 | **Learning/content engine** — content blocks, prerequisites, completion rules, exercises + hints, assessments, mastery scoring, recommendations, search, content admin, real curriculum content (58 lessons / 24 exercises across 6 domains). *(done)* |
| 3 | **SQL Lab** — DuckDB (default) + PostgreSQL (secondary, architecturally available) execution engines behind one interface, a Monaco-based SQL Playground (schema explorer, results grid, history, saved queries), real-execution SQL exercise grading (result-based, never SQL-text comparison), a realistic 8-table synthetic e-commerce dataset, 9 SQL curriculum modules (100 lessons total), and 30 business-framed SQL challenges. *(done)* |
| 4 | **Python Analytics Lab** — a Docker-isolated Python sandbox (network-disabled, resource-capped, non-root, read-only root filesystem) running Pandas/NumPy/Polars/PyArrow/SciPy/Statsmodels/scikit-learn/Matplotlib/Seaborn/Plotly, a notebook-like multi-cell Python Lab UI with a DataFrame viewer, variable explorer, and chart rendering, real-execution Python exercise grading, and a large Pandas-centric curriculum (Fundamentals, NumPy, 7 Pandas modules, Polars, EDA, Visualization — 11 new modules, 177 lessons total across the whole platform) plus 30 business-framed Python challenges (81 exercises total across the whole platform). *(done)* |
| 5 | **Dataset Hub** — a dataset catalog/search/import UI, Kaggle integration (search/inspect/import via the official API, gracefully degrading when unconfigured), local file import (CSV/Parquet/JSON/XLSX, single files or multi-file "collections") with security-hardened filename/table-name handling, automatic DuckDB-based profiling (numeric/categorical/datetime/text/boolean statistics) and a deterministic weighted data-quality score, schema/column-detail viewers with duplicate and outlier drilldown, dataset relationships and version fingerprinting, an EDA Workspace (deterministic overview generation, question generation, structured findings — no AI), a Visualization Workspace with a point-and-click Chart Builder rendered via Plotly (chart-type recommendations and a deterministic "visualization mistake" detector), one-click integration into SQL Lab and Python Lab, a minimal "Create Project from Dataset" shell (the full project engine is Phase 8), and EDA/dataset-analysis curriculum additions. *(done)* |
| 6 | **Analytical Intelligence Layer** — a Statistics domain (descriptive stats, probability, distributions, sampling, inference, hypothesis testing, correlation/regression) computed for real via scipy/statsmodels running directly in the API process, an Experimentation & A/B Testing domain (experiment design, randomization, sample size, power, pitfalls) with a Sample Size Calculator, an A/B Test Analyzer, and a deterministic-seed Power Simulator, deepened Business Analytics (revenue/customer/marketing/sales/operations/financial analytics, a root-cause-analysis methodology, an analytical decision framework) and Product Analytics (funnels, cohort retention, churn, feature adoption) domains with live Funnel Analyzer and Cohort Retention Explorer tools running against a new synthetic "saas-product" dataset (users/events/subscriptions/two built-in A/B experiments), a 23-metric Metrics Library, and an Analytics Case Library with self-assessed rubric scoring (real, computed scores — not self-reported) for business/product case studies, all reusing the existing SQL Lab/Python Lab/Dataset Hub/exercise-attempt infrastructure rather than duplicating it. *(done)* |
| 7 | **Data Engineering, Warehousing, Data Modeling & dbt Lab** — a real, local dbt Core project (dbt-duckdb, no cloud warehouse) with staging/intermediate/marts layers, seeds, snapshots (a real SCD Type 2 example), macros, and tests over the ecommerce dataset, run for real from a **dbt Lab** UI (project tree, Run/Test/Build/Compile/Docs Generate, a real lineage DAG read from dbt's own `manifest.json`, a docs viewer with real column types from `catalog.json`, a test-results viewer); a visual **Data Modeler** (React Flow canvas — tables/columns/PK-FK/grain, relationships, a real validator for missing keys, invalid FKs, circular relationships, ungrounded fact tables) that doubles as an **Architecture Diagram Builder** and a **Pipeline Playground** via one shared graph schema (`DataModel`/`DataModelTable`/`DataModelRelationship`, discriminated by `model_kind`); a **Data Quality Lab** (NOT_NULL/UNIQUE/ACCEPTED_VALUES/RELATIONSHIP/MIN_MAX/FRESHNESS/ROW_COUNT rules, executed for real via DuckDB against a dataset's own tables); Data Engineering (8 modules), Data Warehousing (10 modules), Data Modeling (6 modules), and Modern Data Stack (9 modules, including cloud warehouses/storage and conceptual Airflow/Kafka/Spark coverage) curricula (55 lessons); and 60 new exercises (15 Data Engineering, 15 Warehousing, 15 Data Modeling, 10 real-execution `DBT`-type exercises graded by an actual `dbt build --select`, 5 pipeline/data-quality reasoning cases) — all reusing the existing exercise-attempt/mastery/content-sync infrastructure. *(done)* |
| 8 | **Case Study Engine & End-to-End Project Engine** — a real-world simulation layer where the platform never reveals the solution upfront: a stakeholder states an ambiguous business problem, and the learner independently clarifies, frames, explores data, analyzes, finds insights, recommends, and communicates before being evaluated. **20 real, content-authored case studies** across all 8 categories (Business/Product/Customer/Marketing Analytics, Operations, Experimentation, Data Quality, Data Architecture) and **8 substantial project templates**, every numeric claim in every case verified against the platform's own real seeded datasets (`ecommerce`/`saas-product`), not invented. A multi-stage **Case Workspace** (a CASE sidebar — context/objective/data-with-SQL-Python-EDA-deep-links/deliverables/a clickable stage tracker with per-stage time tracking/progressive hints — plus a WORKSPACE main area of Clarify/Frame/Analyze/Recommend/Communicate-&-Submit tabs) and a **Project Workspace** (milestones/datasets/artifacts/analysis/data-model-&-dbt-refs/documentation/presentation/submission tabs) share one **Findings/Hypothesis Tracker/Evidence** system (Evidence denormalizes a snapshot of the real query/code/stat it points at, so it stays meaningful even if the referenced row is later deleted). A category-weighted **rubric evaluation engine** (`app/case_engine/`) scores each category either from the learner's own checklist self-assessment or, for a category marked `is_technical`, objectively from real `ExerciseAttempt` pass/fail — with deterministic (non-AI) feedback bucketing. A **My Case Performance** dashboard computes strongest/weakest domain, recurring rubric-category weaknesses, and a next-case recommendation entirely client-side from two existing endpoints, no new analytics endpoint needed. Content Admin gained Cases/Project Templates tabs (activate/deactivate only — both are content-authored, matching the existing Lesson/Exercise admin pattern). *(done)* |
| 9 | **Complete Data Analyst Interview & Assessment Engine** — a dedicated, deterministic (non-AI) interview-readiness system layered on top of every prior phase's grading rather than duplicating it. **335 real interview questions** (50+ SQL, 59 Python, 25 Excel, 30 Statistics, 20 A/B Testing, 30 Product Analytics, 30 Business Analytics, 15 Data Modeling, 15 Data Engineering, 31 Behavioral, plus 30 bonus questions — 15 Data Warehousing, 15 dbt) as thin `InterviewQuestion` wrappers around existing (or newly authored, where a category was genuinely new) `Exercise` rows — never a second grading engine. **6 interview modes** (Practice/Timed/Mock/Company-Style/Weakness-Drill/Final-Readiness) and **14 round types**, including a real, from-scratch **Excel formula engine** (`app/excel_lab/` — tokenizer/parser/evaluator, ~34 functions: SUMIFS/XLOOKUP/INDEX-MATCH/IFERROR/TEXT/date functions, real cross-sheet references, circular-reference detection) powering a lightweight spreadsheet grid, and a Case Study round that reuses the Phase 8 Case Workspace directly via a `case_attempt_id` FK rather than a third question format. Five pure, DB-free, fully unit-tested engines in `app/interview_engine/` implement every scoring rule with a documented formula: **6-dimension weighted scoring** (Technical Correctness 30/Analytical Reasoning 20/Business Understanding 20/Communication 15/Problem Solving 10/Efficiency 5, configurable per template), a **readiness model** (50% skill mastery + 35% recency-weighted-and-individually-capped recent performance + 15% consistency, with a mechanical `MAX_SINGLE_INTERVIEW_SWING` cap so no one assessment dominates), **5-type weakness detection** (Knowledge/Execution/Reasoning/Communication/Speed, each a threshold rule requiring 2+ occurrences), **deterministic adaptive question selection** (unseen-first, then not-yet-mastered, then any; harder after a mastered win, back to intermediate after a fail), a **7-day personalized plan generator**, and a **spaced-review foundation** (a real interval-growth formula from real attempt history, not a stub). Server-side-only timer validation (elapsed time is always computed from stored timestamps, never trusted from the client) backs a visible countdown with pause/resume and automatic submission. **15 short interview-specific cases** (DAU decline, revenue decline, churn increase, conversion drop, campaign underperformance, an A/B-test-interpretation case, feature adoption, customer segmentation, a marketplace supply problem, a delivery delay, a pricing-impact case, a mid-analysis data-quality discovery, a retention-cliff case, a CAC-spike case, and an onboarding-funnel case) and **6 interview templates** (a default 45-minute Mock Interview, 3 generic company-style archetypes — Product Analytics/Business Analyst/Analytics-BI — a compact SQL+Case-Study quick mock, and a Final Readiness Assessment spanning every round type) round out the content. A full **Interview Prep dashboard** (readiness %, strongest/weakest areas, quick-start, recent scores), a session workspace (real Monaco SQL/Python editors, a real spreadsheet grid, MC/rubric-checklist answering, a live server-validated timer), a post-interview **Scorecard**/**Question Review** (hidden answers/tests finally revealed, retry by full/section/question), a **Readiness Trend** chart, **My Interview Review** (bookmarks/notes/spaced-review queue), and Content Admin extensions (Interview Questions/Templates tabs, activate/deactivate only) round out the frontend. *(done)* |
| 10 | **AI Data Analyst Mentor, Tutor & Intelligent Analysis Layer** — a reasoning/coaching layer on top of every deterministic Phase 1-9 engine, never a second scoring system (see `app/ai/AUTHORITY.md`). A generic, env-driven **provider abstraction** (`AIProvider` protocol; `OpenAIProvider`/`AnthropicProvider` are thin direct `httpx` REST clients — no SDK dependency; `LocalProvider` is a deterministic, no-network, no-key-needed default so the whole platform, and this phase's own tests, never require a real API key) resolved by one factory, never hard-coded. A centralized **AI Gateway** (Context Builder → Provider → Response Validator) that never touches a database itself; every structured response is validated against a Pydantic schema and degrades to `structured_valid=false` (never trusted blindly, never crashes) on malformed output. A **Context Engine** (`app/ai/context.py`) builds small, bounded, per-feature payloads from real already-fetched domain objects — never a database dump — passed through **security** (`app/ai/security.py`: secret redaction by pattern, recursive forbidden-key stripping, `<untrusted_data>` prompt-injection wrapping) before ever reaching a prompt. **25 versioned prompt templates** (`app/ai/prompts/`, each with a documented purpose/input schema/output schema) covering: a globally-accessible **AI Mentor** (Socratic by default, a `AIMode` persona axis — Tutor/Coach/Reviewer/Interviewer/Analyst/Explainer — orthogonal to which feature is invoked) with a 4-level hint ladder; **SQL AI Tutor/Review/Debug/Optimization Coach** and **Python AI Tutor/Review** (both "Ask AI" inside their real lab, never auto-replacing the user's query/code); **Natural-Language-to-SQL/Python** (generated, shown, and only executed after explicit user confirmation — never silently run); **Data Analysis/Insight Review** and an **AI EDA Assistant** (observed issues, grounded in the real dataset profile, kept structurally separate from suggested/unverified investigations); one shared **Domain Coach** parameterized by `AIDomain` for Statistics/Experimentation/Product Analytics/Business Analytics/Data Modeling/dbt (a system prompt + a real result payload, not six parallel services); an **AI Case Study Coach** (4 coaching modes — Guided/Standard/Interview/Strict) and a conversational **AI Case Interviewer** (progressive reveal grounded in the case's own real `clarification_guidance` topics, never inventing a data value the case doesn't actually have); an **AI Behavioral Interviewer** (STAR-style follow-ups); an **AI Interview Debrief** (narrates the already-computed real `Interview.score`, supplementary to it, never a replacement); **Communication/Storytelling/Executive-Summary coaches**; a **Learning Planner** explanation layer (explains why each day of the REAL, already-generated deterministic 7-day plan was chosen — never generates a different plan); **AI Skill Diagnosis** and **AI Mistake Memory** (both explicitly stored separate from real `UserSkill.mastery_score`, never written back into it); and an **AI Project Review**. A lightweight local **RAG** (`app/ai/retrieval.py` — plain TF-IDF + cosine similarity over real lesson content and the Metrics Library, computed in-process with `numpy`, no vector database or embedding API) grounds a **Knowledge Search** feature with real lesson/metric citations, explicitly saying "I can't determine this" rather than answering from general knowledge when retrieval finds nothing relevant. **Cost/usage controls** (a daily request-limit hard ceiling, per-request token/latency audit logging via `AIAuditLog`, a visible "AI usage today") and **AI Settings** (enable/disable, provider override, response style, learning mode, privacy preference) round out the platform; a persistent **AI Mentor launcher** and per-feature "Ask AI" panels (SQL Lab, Python Lab, Case Workspace, Interview Review) round out the frontend. *(done)* |
| 11 | **Career Readiness, Portfolio, Resume/JD Intelligence & Job Preparation** — a career-intelligence layer answering "am I ready for a Data Analyst role, what are my gaps, how do I prepare for a specific job?", built entirely on top of the existing deterministic mastery/progress/interview-readiness engines and the Phase 10 AI layer — never a second, competing scoring system (see `app/models/enums.py`'s Phase 11 section header). A **Job Description Analyzer** (paste/save a JD, deterministic keyword-match extraction against the real skill taxonomy as a zero-configuration baseline, optionally enriched by a new `JD_EXTRACTION` AI feature whose every suggested skill slug is re-validated against real `Skill` rows before being trusted) produces a **Skill Gap table** (recomputed fresh on every read, never stale), a **configurable-weight JD Readiness Score** (MUST_HAVE/STRONGLY_PREFERRED/NICE_TO_HAVE weights, explicitly labeled a platform estimate, never a hiring guarantee), a deterministic **Preparation Plan** (real recommended exercise/case/project-template slugs per gapped skill) and **JD-specific Interview Plan**, and a **Job Preparation Workspace** ("Prepare for This Job" — notes/checklist/status, idempotent per JD) plus **JD Comparison** across saved roles. A **Resume Analyzer** (multi-version history, plain-text evidence extraction that only ever quotes a verbatim resume line — never fabricates a metric/employer/achievement — a deterministic, AI-independent quality/clarity/impact scoring heuristic with AI-sourced qualitative issues/suggestions layered on top via a new `RESUME_REVIEW` feature, and Resume Gap Analysis against a target role). A **Portfolio Builder** (projects/case studies/certifications/skill highlights, every new item defaulting to PRIVATE — never PORTFOLIO or PUBLIC_READY without an explicit user action — a deterministic Portfolio Quality Score, an AI `PORTFOLIO_REVIEW` narration layer, and Portfolio Gap Detection recommending real, active project templates). A **Career Readiness Rubric** (8 dimensions — Technical/Analytical/Business/Product/Data-Engineering-Awareness/Communication/Interview/Portfolio — reusing `UserSkill.mastery_score` and `InterviewReadinessService` as real input signals, never recomputed) with a gated **Final Readiness Level** (Foundation → Developing → Intermediate → Interview-Ready → Strong-Candidate → Exceptional): a per-dimension gating minimum means one strong dimension can never mask a real weakness elsewhere, and every score carries a per-dimension explanation plus an explicit "this is not a hiring guarantee" disclaimer. A **Career Skill Matrix** with real per-skill evidence counts (exercises passed/projects/cases/mock-interview score) and a 5-level Evidence-Based Mastery label (Learned/Practiced/Applied/Interview-Ready/Demonstrated, never computed from one test); an auto-generated **Career Progress Timeline** (sync-on-read from real completed projects/cases/interviews/mastered skills, never freeform-authored); a **Career Goal Planner**; a non-excessive 10-badge **Achievement System** (sync-on-read against real counts, idempotent, never a rules-engine reinterpretation of its own seed data); a **Behavioral Story Bank** (12 real categories matching Phase 9's own behavioral-exercise tags, with Interview Story Coverage); a **Career Knowledge Base** (a small feature-scoped note model, matching this codebase's established one-note-model-per-feature convention rather than reusing `InterviewNote`); a **Weekly Career Review** and an exportable **Career Report** (reusing the existing client-side download pattern, no new backend export/PDF infrastructure); and an **AI Career Coach** (a new `CAREER_COACH` feature, explaining real readiness/goal/JD data, never inventing an achievement or promising an interview). 7 generic **Role Templates** (Data/Product/Business/BI/Marketing Analyst, Analytics Engineer Entry/Intermediate) and a 10-badge achievement seed round out the content. 21 new tables in one migration (`4d9c395b6197`), a new top-level **Career** nav section (9 routes), and 29 new backend + 9 new frontend tests (734 backend + 100 frontend total, zero regressions) round out the phase. *(done)* |
| 12 | **Final Integration, Production Hardening & Job-Ready Data Analyst OS** — a cross-cutting Platform layer (`app/routers/platform.py`) that unifies all 11 prior phases rather than adding a 12th domain: a **Next Best Action** engine merging the highest-signal item from five already-independent recommendation sources (lesson recommendations, interview weakness detection, active-JD skill gaps, portfolio gap detection, career goals) that a Phase 12 audit found had never been cross-linked; a dependency-aware **System Health** check (database/DuckDB/SQL Lab Postgres/Python sandbox/dbt/AI provider/Kaggle), distinct from the pre-existing pure-liveness `/health`; a **Data Integrity Audit** (13 real orphaned-reference/duplicate-slug checks — meaningful because this app never enabled SQLite foreign-key enforcement); a **Job-Ready Checklist** (6 groups, ~20 real evidence-based boolean items); the platform's first **Backup/Restore** system (a declarative 34-entity export/import, idempotent by primary key, always previews before writing, restore never happens without explicit confirmation); a request-id + duration **logging middleware** (every error response and log line now carries a correlating `request_id`); and an expanded **9-kind global search** (up from 5) with a dedicated `/search` page and a **command palette** (Ctrl/Cmd+K). The **navigation was unified** into one 10-section structure (Main/Learn/Analyze/Data Stack/Cases & Projects/Interview/AI/Career/Knowledge/Settings, 42 items total) replacing 11 phases' worth of organically-grown top-level routes, and **Settings** became tabbed (Profile/Appearance/AI/Data/System) to hold the new System Health and Backup/Restore panels. A 7-agent parallel research audit (nav/dashboard state, skill-taxonomy consistency, scripts/docs/health-check state, error-handling/logging, test/content-count ground truth, security posture, frontend UI consistency) was run before any implementation to separate "already solid, needs no work" (the unified skill taxonomy, error handling, dark mode, loading/empty/error states, accessibility, SQL/Python/AI sandbox security, CORS, secrets hygiene — all confirmed, none rebuilt) from "genuinely missing" (everything listed above). Two real, measured issues were found and fixed in the process (see below): an N+1 performance bug in the Career Skill Matrix (~4.8x speedup) and a timing-jitter test flake in both SQL/Python exercise grading. *(done)* |

## The learning loop this platform optimizes for

```
LEARN → PRACTICE → APPLY → GET EVALUATED → IDENTIFY WEAKNESS → REVIEW → REATTEMPT → MASTER → INTERVIEW
```

The product principle behind every phase: **"Can I independently solve a real business problem using
data?"** — not "did I finish a course?". See
`content/lessons/data-analyst-foundations/how-to-use-this-lab/the-learning-loop.yaml` for the in-app
explanation of this loop.

## What Phase 1 & 2 deliberately do not build

The following are explicitly deferred to later phases and are *not* implemented yet, even as stubs
beyond a data-model placeholder where one was needed for architectural completeness (e.g.
`Exercise.exercise_type` includes `PYTHON`/`CODE` values, and attempts at those types are still recorded
as `SUBMITTED`, without an execution engine to grade them — only `SQL` was wired up to real execution, in
Phase 3):

Kaggle integration, a Python code execution sandbox, AI features (the recommendation and mastery engines
are fully deterministic/rule-based), Airflow, dbt, Spark, Kafka, cloud integrations, multi-user auth,
payments, real spaced repetition (the `/review` page surfaces low-mastery lessons as an early
approximation only), full case-study/mock-interview engines, and any microservice split beyond
`web` / `api` / `postgres`.

## What Phase 3 deliberately does not build

Explicitly out of scope for the SQL Lab: Python execution, Kaggle, dbt, Airflow, Spark, Kafka, an AI SQL
tutor, a full case-study system, a full timed-interview simulator (only the data model/components for a
future one), and advanced spaced repetition beyond what Phase 2 already approximates. The PostgreSQL SQL
engine is architecturally complete (a real, isolated read-only/timeout-enforced engine, separate
credentials from the app's own database) but could not be live-tested in this environment (no PostgreSQL
instance available) — it was verified by import/type-checking only; live verification against a real
Postgres instance is a good Phase 4 follow-up.

## What Phase 4 deliberately does not build

Explicitly out of scope for the Python Lab: Kaggle, a full statistics engine, full A/B testing, a full ML
curriculum (only a `scikit-learn` foundation — train/test split, a basic regression/classification model,
evaluation metrics), dbt, Airflow, Spark, Kafka, an AI tutor/code reviewer (the execution/output/score data
model is shaped to support one later, per the spec's "AI Extension Point," but no AI review runs today), a
complete case-study engine, and a complete interview simulator. The Docker-based sandbox
(`app/python_lab/docker_backend.py`) is architecturally complete and code-reviewed (mock-verified exact
`network_mode="none"`/resource-limit/capability-drop/secret-free-environment configuration — see
`tests/test_python_lab_security.py`) but could not be live-tested end-to-end against a real Docker daemon
in this environment (none available) — the reusable execution engine underneath it
(`infrastructure/docker/python-sandbox/kernel.py`) WAS fully live-tested, directly and through the whole
API stack via an in-process test double (`tests/python_lab_fakes.py`), just not through an actual
container boundary. Building/running the sandbox image and a full live end-to-end pass (including the
Docker-out-of-Docker volume-mount path — see `docs/architecture.md#python-lab-phase-4`) is the natural
first thing to verify in a real Docker environment.

## What Phase 5 deliberately does not build

Explicitly out of scope for the Dataset Hub: statistics/experimentation (Phase 6), a full case-study/project
engine (`POST /projects` creates a bare shell row today — scoping, deliverables, and grading are Phase 8),
an AI-driven insight or narrative generator (the EDA overview, question generation, chart recommendations,
and the "visualization mistake" detector are all deterministic, rule-based, and reproducible — matching the
same principle Phase 1-4 already established for the mastery/recommendation engines), and cross-dataset
joins inside the profiling/EDA engines (a dataset "collection" imports each file as its own table plus a
best-effort inferred `DatasetRelationship`, but query-time joins across them are just regular SQL Lab
queries, not a dedicated feature). Kaggle integration is architecturally complete (the real `kaggle` package,
lazily imported so it's never a hard dependency, with a protocol-typed client for tests) but could not be
live-tested against the real Kaggle API in this environment (no `KAGGLE_USERNAME`/`KAGGLE_KEY` configured) —
it was verified by unit tests against a test double and by confirming the UI degrades cleanly
("Kaggle isn't configured") when the credentials are absent. As with Phase 4, Docker itself was unavailable
in this environment, so the "Open in Python Lab" integration was verified through the API/service layer and
through the Python Lab dataset browser's file-listing logic, not by actually executing Python against an
imported dataset inside a live container.

While live-verifying Phase 5 in a browser, two pre-existing UI bugs from Phase 3/4 were found and fixed
(not introduced by Phase 5, but caught by it): `react-resizable-panels` was upgraded at some point to a
version where a bare number like `defaultSize={20}` is now interpreted as *pixels*, not percent — silently
collapsing the SQL Lab schema explorer and the Python Lab dataset browser to a sliver a few pixels wide.
Both `sql-playground.tsx` and `python-lab-page.tsx` now pass percentages as strings (`defaultSize="20"`),
per the installed version's documented API. A pre-existing `tests/e2e/sql-lab.spec.ts` assertion
(`getByText("payments")`) was also tightened to `{ exact: true }` after it started matching multiple
elements. A separate, lower-priority flakiness was also observed in that same spec's `setEditorQuery`
helper (Monaco occasionally drops/reorders keystrokes typed via `page.keyboard.type`) — left unfixed as
out of scope for Phase 5, since it's a Phase 3 test-infrastructure issue unrelated to any Phase 5 code.

## What Phase 6 deliberately does not build

Explicitly out of scope for the analytical intelligence layer: a full data-engineering/warehousing/dbt
curriculum (Phase 7), a full ML curriculum beyond Phase 4's `scikit-learn` foundation, a complete
case-study/project engine (Analytics Cases reuse the existing Exercise/ExerciseAttempt pipeline —
submission, rubric scoring, and mastery updates all work today, but there is no dedicated `AnalyticsCase`
table, timed-case simulator, or multi-part case flow; that's Phase 8), and any AI-driven grading or
insight generation (rubric-based case scoring is a deterministic self-assessment checklist — the learner
checks which criteria their own free-text answer satisfies, and the score is computed from checked
points/total points server-side — not an NLP/LLM judge; that's Phase 11's "AI... case-study evaluator").
Persisted, named experiment tracking (saving/reopening a specific A/B test's configuration and result
over time) was also not built — the Sample Size Calculator, A/B Test Analyzer, and Power Simulator are
all stateless computations, matching the spec's emphasis on deterministic, reproducible tools over a
new persistence layer. Regression support covers simple and multiple linear regression only (no
logistic/other GLM families) since the curriculum's framing is interpretation, not a modeling course.

While live-verifying Phase 6, one pre-existing latent bug (present since the API's error-handling
middleware was first written, not introduced by Phase 6) was found and fixed: this FastAPI version's
`RequestValidationError.errors()` embeds the *raw exception object* in each error's `ctx.error` whenever
a `@model_validator`/`@field_validator` raises a plain `ValueError` — not JSON-serializable, so any such
validator (the first one in the app to actually exercise this path was `SummaryStatsRequest`'s "provide
either `values` or `dataset`" check) crashed the validation-error handler itself instead of returning a
clean 422. Fixed in `app/core/errors.py` by stripping the `ctx` key before serializing (the human-readable
`msg` field already carries the same text). A second, more consequential gap was also found and fixed:
`DatasetService.to_schema()` only ever populated `Dataset.tables` from the Phase 5 `DatasetTable`
relationship, so datasets registered purely as SQL Lab databases (`SqlTable` rows only — both the
pre-existing "ecommerce" dataset *and* Phase 6's new "saas-product" dataset) reported an **empty**
`tables` list to the frontend, silently breaking every dataset/table picker's ability to select any table
but an implicit backend default (surfaced by the new Product Analytics workspace, whose Funnel Analyzer
needs the "events" table specifically, not whatever table happens to load first). Fixed with the same
dual-check fallback pattern already used for `sql_ready`/`python_ready`.

## What Phase 7 deliberately does not build

Explicitly out of scope for the Data Engineering/Warehousing/Modeling/dbt Lab phase: a full ML system, an
AI tutor/reviewer, a complete interview engine, an advanced case-study engine, a portfolio generator,
production cloud deployment, and enterprise auth — those belong to later phases (or, for cloud deployment
and enterprise auth, were never on this platform's roadmap at all, per its local-first, single-user
design). A real Airflow/Kafka/Spark runtime was also deliberately not built: Airflow, Kafka, and Spark are
covered conceptually only (a dedicated module each, no local cluster/broker/scheduler) — running any of
them would need Docker (unavailable in this environment, same limitation as Phases 4-6) and would add
real operational complexity (a scheduler process, a broker, a JVM-based cluster) disproportionate to what
a Data *Analyst* — as opposed to a Data Engineer — actually needs to run day-to-day; the platform's own
`analyst-vs-data-engineer-boundary` lesson makes this scope boundary an explicit teaching point rather
than an implementation shortcut. Cloud data warehouses (BigQuery/Snowflake/Databricks) and cloud storage/
compute (AWS/GCP/Azure) are likewise conceptual-only — no cloud account is created or required. SQL Lab
was **not** extended to query dbt's own materialized warehouse output directly (its "databases" are still
backed by `Dataset`/`SqlTable` rows pointing at CSV/Parquet files, not the dbt-duckdb warehouse file) —
querying dbt's real marts happens through the dbt Lab itself (docs/lineage) today; wiring a read-only
"dbt warehouse" database into the SQL Lab's engine registry is a reasonable, well-scoped Phase 8 addition,
deferred here to avoid adding a second DuckDB-connection code path under this phase's time budget. dbt
exercise grading covers model-authoring against `unique`/`not_null`/`accepted_values`/`relationships` only
(dbt-core's actual built-in generic tests, no `dbt_utils` package) and does not exercise a model's
incremental-rebuild behavior across multiple submissions (each submission is graded by one `dbt build
--select`, not a two-run "does it actually skip already-processed rows" check) — the incremental-models
*mechanism* is taught via the real, working `fct_daily_revenue.sql` model and its lesson content instead.

While live-verifying Phase 7, several real, in-development bugs were found and fixed before completion
(all caught by the project's own "verify via real execution" testing philosophy, not by inspection):
a session identity-map staleness bug in `DataModelService.replace_graph` (saving a model's graph and
reading the *same* response back in one request returned a stale, empty `tables`/`relationships` list,
because SQLAlchemy doesn't refresh an already-loaded collection on an already-identity-mapped object —
fixed by calling `db.expire(model)` before the final re-fetch); a staleness bug in the dbt Lab's test-results
endpoint (every dbt subcommand overwrites `run_results.json`, including `docs generate`/`compile`, which
also list test nodes with a generic "success" compile status — indistinguishable from a real test pass
unless gated on `run_results.json`'s own `args.which` field, now checked); a docs-panel bug where a
model's column list came only from `manifest.json` (i.e., only columns someone bothered to document in a
`schema.yml`), silently hiding real, undocumented columns that do exist in the built table — fixed by
making `catalog.json` (the actual built relation) the authoritative column list, enriched with
descriptions from `manifest.json` where present. Two of the ten real dbt exercises' generic tests were
initially too weak to actually verify the transformation they were meant to teach (a missing `where
is_active` filter, and a missing join, both still passed the attached tests as originally written) — caught
by adversarially submitting each exercise's own starter code and confirming it failed before its solution
passed; fixed by tightening the attached tests (an `accepted_values` check on the filtered column itself,
a `not_null` check on the joined-in column) so an incomplete submission genuinely fails. A regression this
phase itself introduced was also caught and fixed before completion: the new "Quality Lab" cross-link
button added to the dataset detail page originally read "Data Quality", colliding (via substring text
matching) with the pre-existing Phase 5 dataset-quality-score tab's own "Data Quality" heading in
`tests/e2e/dataset-hub.spec.ts` — renamed to "Quality Lab" to disambiguate. Separately (not a regression,
but a real finding worth recording): this phase's own new E2E spec initially assumed a data-quality rule
list would always sort "newest first" when locating the rule it had just created — reliable on a fresh
database, but flaky against a long-lived, repeatedly-tested dev database where many same-shaped rules
accumulate with near-identical timestamps. Rather than paper over this in the test alone, it surfaced a
real, small product gap: the Data Quality Lab's rule-creation form had no way to label a rule, even though
the API already supported an optional `name` field — added a "Name (optional)" input to close that gap,
and the E2E test now locates rules by a unique name instead of assumed list order.

The pre-existing Monaco+Playwright typing flakiness first documented in "What Phase 5 deliberately does
not build" (`page.keyboard.type()` occasionally drops/reorders keystrokes inside the SQL Lab/Python Lab
Monaco editors) is still unfixed — confirmed still present and unrelated to any Phase 7 code (it
reproduces identically typing plain SQL into the pre-existing SQL Lab, which Phase 7 never touched), and
still out of scope as a Phase 3/4 test-infrastructure issue. The Python Lab's own E2E tests remain
un-runnable in this environment for the same reason documented in Phase 4/5/6: no Docker daemon available
to back `app/python_lab/docker_backend.py`.

## What Phase 8 deliberately does not build

Explicitly out of scope for the Case Study/Project Engine phase, per the spec's own boundary: a complete
interview simulator, an AI interviewer, an AI case-study evaluator, portfolio/GitHub publishing, advanced
spaced repetition, a company-specific interview engine, and an advanced ML system — all later phases (9,
11, 12). Case/project evaluation is entirely deterministic (rubric self-assessment plus real
`ExerciseAttempt` pass/fail for `is_technical` categories) — no LLM call anywhere in `app/case_engine/`.
The Interview Integration Foundation is limited to what Case/CaseAttempt already store (skills,
difficulty, the rubric, the reference solution, the learner's own final recommendation/executive summary)
— Phase 9 builds the interview system itself on top of this, not introduced here. Case Study Templates
(spec section 62, e.g. "Revenue Investigation"/"Funnel Analysis" authoring shortcuts) were not built as a
separate admin feature — with only 20 cases to author this phase, a shared human author (rather than a
templating UI) was the faster, equally-correct path; a template picker remains a reasonable later addition
if case authoring volume grows. Only 3 real datasets exist on this platform (`orders-sample`/`ecommerce`/
`saas-product`), so cases/projects with a FinTech, food-delivery, or sales-pipeline narrative are honestly
disclosed reframings of the `ecommerce`/`saas-product` data (e.g. subscription MRR narrated as fintech
recurring revenue) rather than fabricated industry-specific datasets — each such project template says so
directly in its own `business_context`.

While building and live-verifying Phase 8, several real, in-development bugs were found and fixed before
completion (all caught by the project's own "verify via real execution" philosophy — live Playwright runs
against a real running server, not just mocked-`apiClient` component tests):

- **A stale-closure data-loss race** in every "save the whole object on blur" form (Case Frame/Recommend/
  Communicate-&-Submit tabs; Project Documentation/Presentation/Submission-reflection tabs): each field's
  `onBlur` handler read the *previous render's* props to build its merged save payload, so tabbing through
  several fields faster than one save round-trip (exactly what a live Playwright `.fill()` sequence does,
  and what a fast human typist or a browser autofill can also do) silently dropped whichever fields hadn't
  finished saving yet — only the *last* field's save survived. Fixed by converting each of these 6 forms to
  local, controlled state (seeded once from the initial prop, never reset from it afterward, since each
  workspace remounts per attempt/project via routing anyway) so every blur's payload reflects every edit
  made so far, regardless of network timing. Caught by the Case Study Engine's own E2E spec, which found
  the "Frame" tab had persisted only 2 of 5 typed fields.
- **Missing `htmlFor`/`id` associations** on the same 6 forms' `<Label>`/`<Textarea>` pairs — present as
  siblings but never linked, so `getByLabel` (and a screen reader) couldn't resolve them at all. Fixed by
  adding matching `id`/`htmlFor` pairs throughout, matching the pattern already used elsewhere in this
  codebase (e.g. `SkillAdminPanel`'s `htmlFor="skill-slug"`/`id="skill-slug"`).
- **Misdiagnosed during Phase 8, correctly root-caused during Phase 9**: every DB-touching route hung
  indefinitely on the first real HTTP request (while `/health` responded instantly), which Phase 8
  attributed to `uv run`'s process-wrapping interacting badly with anyio's worker thread pool, "resolved"
  by invoking uvicorn directly via the venv's `python.exe -m uvicorn`. That diagnosis was wrong — the
  sync/async split and the `uv run` bypass were both coincidental. The real cause, isolated while applying
  Phase 9's own migration: `app/core/config.py`'s `SettingsConfigDict(env_file=".env")` resolves `.env`
  relative to the **process's current working directory**, not `config.py`'s own location. `apps/api/.env`
  holds the correct local `DATABASE_URL`; the repo root has no `.env` (only `.env.example`). Any command
  launched from the repo root without an explicit `DATABASE_URL` silently falls back to `Settings`'s
  hardcoded Postgres default and hangs on a TCP connect to a Postgres server that isn't running —
  `/health` is unaffected only because it never opens a DB connection. Fix: `cd apps/api` first, or pass
  `DATABASE_URL="sqlite:///<repo>/data/dev.db"` explicitly; no `uv run` workaround is needed at all.
- Also confirmed (not a bug, a repeatability property worth recording): the Case Study Engine's own E2E
  spec is, like the Phase 7 Data Quality Lab spec before it, not naturally idempotent against a long-lived
  dev database — re-running it against an attempt it already completed hits a "Submit case" button that
  correctly no longer renders. This is expected (the same case-attempt lifecycle the API test suite
  verifies), not something the test works around; a from-clean-database CI run has no such issue.

## What Phase 9 deliberately does not build

Explicitly out of scope for the Interview & Assessment Engine phase, per the spec's own boundary: an AI
interviewer, an AI voice interviewer, AI-generated questions, AI answer/communication evaluation, resume
analysis, job-description matching, company-specific live research, and an automated application system —
all Phase 10/11. Every scoring rule in this phase is deterministic and documented in
`app/interview_engine/{scoring,readiness,weakness,selection,plan,spaced_review}.py` — no LLM call anywhere
in that package, matching Phase 8's `app/case_engine/` precedent exactly. Communication is scored only via
the existing structured rubric-self-assessment mechanism (the same one Cases and rubric-scored Exercises
already use), not a new evaluation path. The spaced-review system (`spaced_review.py`) is an honest
*foundation* as spec'd, not a full SM-2-style algorithm: a documented, real interval-growth formula (miss →
1 day, shaky → 3, solid → 10, mastered → 30, stretching up to 2x on a consecutive-success streak) computed
from real attempt history, not a stub returning fixed data — but it has no per-item ease factor or
quality-grade input yet. The Assessment Builder extending Content Admin is, like Phase 8's Case/Project
Template admin, activate/deactivate only — new questions/templates are authored as
`content/interview/{questions,templates}/*.yaml` files and synced, not created through a UI; a
template-authoring/question-builder UI remains a reasonable later addition if authoring volume grows.
Question "variants" for anti-memorization rely on the existing adaptive-selection pool (many real
questions per type, unseen-first) rather than a dedicated variant-generation system — there is no
`variant_group` concept; a large, real, non-duplicate question bank was judged sufficient for this phase's
scope. Company-style templates are named generic archetypes (Product Analytics/Business Analyst/
Analytics-BI) exactly as spec'd — deliberately not claims about any specific company's current hiring
process. As with Phase 8, cases/questions with a narrative outside the platform's real seeded datasets
(`ecommerce`/`saas-product`) are honestly reframed (e.g. the DAU-decline Case Study round is a
`saas-product`-backed scenario, not a fabricated dataset) rather than invented from nothing.

While building and live-verifying Phase 9, several real, in-development bugs were found and fixed before
completion (all caught by the project's own "verify via real execution" philosophy — real backend
smoke scripts and live Playwright runs against a running server, not just unit tests in isolation):

- **A latent `AttributeError` in the section-advancement state machine**: `_ensure_current_question`
  called `self._finish_interview_body(interview)` once every section/question in an interview was
  exhausted — a method that was never actually defined (an artifact of an earlier design pass). This
  path was never exercised by the pure-engine unit tests (which don't drive a full DB-backed interview
  to completion) and was only caught by a real end-to-end smoke script that ran a whole ad-hoc interview
  through to its natural finish. Fixed by adding a real `_auto_complete` method that finalizes the
  interview through the same scoring path an explicit "submit" call uses.
- **Ad-hoc interviews silently ignored their requested question count**: `CreateInterviewRequest.
  question_count` was accepted by the schema but never actually stored anywhere a section could read it
  back from, so every ad-hoc (non-template) interview defaulted to a hardcoded 5 questions regardless of
  what was requested. Fixed by adding a real `target_question_count` column to `interview_sections`
  (a small additive migration) and wiring both the template and ad-hoc creation paths to populate it.
- **A real SQL exercise's `ORDER BY` didn't fully disambiguate ties**: a newly authored "3+ consecutive
  months" gaps-and-islands SQL question ordered its result by `streak_length DESC, customer_id` — but a
  single customer can have two separate qualifying streaks of the *same* length, whose relative order
  between two independent query executions (the student's vs. the reference's) isn't guaranteed by that
  ORDER BY. Caught by a real end-to-end submission of the exercise's own reference solution *as* the
  student answer, which should always score 100% and initially didn't. Fixed by grading this exercise
  with `sql_row_order_matters: false` (an order-independent set comparison) instead of trying to force a
  fully stable sort.
- **A pre-existing, unrelated test-isolation gap, surfaced (not caused) by this phase's larger content
  set**: `tests/test_progress.py` asserted that the `DATA_MODELING` skill category's average mastery
  stayed exactly `0.0`, reasoning that no earlier-running test file touched it. `tests/
  test_analytics_cases.py` (Phase 6) has always dynamically picked "any rubric-bearing exercise" to
  exercise its generic rubric-submission flow rather than hardcoding a fragile slug — and a Phase 7
  data-warehousing exercise (`dw-ex-case-scd-type-assignment`, tagged with the `dimensional-modeling`
  skill) was always a candidate for that pick, entirely independent of Phase 9. Root-caused via a
  temporary diagnostic dump of every nonzero `UserSkill` and the exact `ExerciseAttempt` behind it, which
  identified the exact contaminating test. Fixed by removing the fragile category-specific assertion
  from `test_progress.py` rather than trying to protect one arbitrarily-chosen category from every
  current and future test that dynamically picks real content — the correct fix given the test's actual
  intent (verifying the progress endpoint's shape, not skill-mastery isolation, which `test_skills.py`
  already covers).
- **A previously wrong root-cause diagnosis, corrected**: Phase 8 documented every DB-touching route
  hanging indefinitely as a `uv run`/anyio worker-thread-pool incompatibility. Applying this phase's own
  migration reproduced the identical hang for a plain, synchronous `alembic upgrade head` — with no
  `uv run` or anyio involved at all, disproving that theory. The real cause: `app/core/config.py`'s
  `SettingsConfigDict(env_file=".env")` resolves `.env` relative to the **process's current working
  directory**, not `config.py`'s own location; `apps/api/.env` holds the correct local `DATABASE_URL`,
  but the repo root has none (only `.env.example`), so any command launched from the repo root silently
  falls back to `Settings`'s hardcoded Postgres default and hangs on a TCP connect to a Postgres server
  that was never running — `/health` was never affected only because it never opens a DB connection.
  README.md and this file's own Phase 8 section have been corrected to describe the real cause and fix
  (`cd apps/api` first, or pass `DATABASE_URL` explicitly) rather than the `uv run`/anyio misdiagnosis.
- **A Case Study round's case selection outgrew a test/spec assumption of determinism**: both the required
  12-step E2E spec and a backend review test were written against a single, specific interview case
  (`interview-dau-decline-investigation`) as if `_pick_interview_case` would always pick it — true when it
  was the only case tagged `"interview"`, but no longer true once this phase's other 14 interview cases
  existed (the function just takes the first not-yet-used `"interview"`-tagged case ordered by title,
  ignoring category). Both tests started failing on a *different*, equally real case as soon as the content
  set grew — the exact same class of "test assumed determinism that broke once the pool grew" already seen
  with SQL question selection earlier in this phase. Fixed at the right layer for each test's actual intent:
  the E2E smoke test (which only needs *some* real case to complete end-to-end) was made to assert
  structurally instead of on one hardcoded title/dataset name; the backend review test (which specifically
  needs to verify a *known* case's title/score render correctly) got its own `_only_dau_case_is_selectable`
  fixture — mirroring the existing SQL-question one — to pin selection back to one case for the duration of
  that test only.
- **Case Study rounds never contributed to the readiness breakdown by round type**: `_interview_type_
  breakdown` only ever read `attempt.exercise_attempt_id`, so a completed Case Study round (which scores
  via `case_attempt_id` instead — the thin-wrapper reuse of Phase 8's Case/CaseAttempt) silently contributed
  nothing to the per-type breakdown, the strongest/weakest ranking, or the plan's "lowest scoring domain"
  fallback, no matter how many case studies a user completed. Not caught by the pure-engine tests (which
  feed `compute_readiness` synthetic per-type dicts, not real attempts) — found while investigating why the
  E2E spec's readiness page only ever needed a passing SQL round to render a non-empty breakdown card.
  Fixed by adding the missing `case_attempt_id` branch (reading `CaseAttempt.score["overall"]`), covered by
  a new backend test that completes a Case Study round and asserts `"CASE_STUDY"` appears in the breakdown.
- **Confirmed, not a Phase 9 bug**: a full 10-file, 23-test E2E regression pass run at Phase 9 completion
  showed `interview-engine.spec.ts` passing reliably (3 consecutive runs, including inside the full-suite
  run) while 8 tests across `analytics`/`case-studies`/`learning-loop`/`python-lab`/`sql-lab`.spec.ts — none
  of them touched by this phase — failed consistently on two separate runs. Re-running confirmed this is
  the same non-idempotent-against-a-long-lived-dev-database property already noted in Phase 8's bug log
  above, not flakiness or a regression: `case-studies.spec.ts`'s "Attach evidence" strict-mode violation
  went from 3 matching buttons to 4 between the two runs (one more each time the non-idempotent test
  re-attaches evidence to the same, already-submitted case attempt), and `sql-lab.spec.ts` picked up an
  extra, visibly-garbled saved-query-history entry between runs. Both are the shared dev SQLite database
  accumulating state across a great many E2E runs over this project's whole lifetime, not something
  introduced here — a from-clean-database CI run of the full suite would not exhibit either. Left as-is:
  rewriting five unrelated phases' E2E specs to be idempotent, or resetting the long-lived dev database, are
  both out of scope for this phase and the latter is destructive enough to warrant an explicit ask first.

## What Phase 10 deliberately does not build

Explicitly out of scope, per the spec's own boundary: a voice interviewer, an avatar interviewer,
autonomous agents, autonomous database modification, automatic cloud deployment, autonomous job
applications, and fully autonomous data-pipeline creation. No live provider-side tool-calling loop either
(the model never decides mid-conversation which tool to call) — `app/ai/tools.py`'s `AIToolbox` exists and
is scoped/read-only/audited exactly as the spec asks, but every feature's context need is already knowable
from which endpoint was called, so the DB-aware service layer calls the toolbox directly rather than
handing tool definitions to the provider; OpenAI's and Anthropic's function-calling wire formats differ
enough that building a provider-agnostic version of both would roughly double this phase's surface area for
a benefit (the model choosing a tool) that doesn't change what any of the 25 implemented features actually
need. No real external AI credentials are configured in this environment — `AI_PROVIDER=local` is this
project's own default specifically so the platform (and every one of this phase's 66 backend + 8 frontend +
1 E2E tests) works with zero configuration; setting `AI_PROVIDER=openai`/`=anthropic` and a matching key
(see `.env.example`) is a deployment-time choice, not something this phase could safely make on a shared
lab machine on the user's behalf. Structured-output validation is prompt-instruction-based (ask the model
for JSON, validate what comes back) rather than either provider's own native structured-output/function-
calling feature, to keep `app/ai/gateway.py` provider-agnostic — a real provider that ignores the
instruction degrades to `structured_valid=false` and a plain-text reply rather than a hard failure, which
is exercised by `tests/test_ai_gateway.py` but can only be confirmed against a REAL provider's actual
behavior once one is configured, not from this environment.

While building and live-verifying Phase 10, two real, in-development issues were found and fixed before
completion (via this project's own "verify via real execution" philosophy — real backend integration tests
against real seeded content, and a live Playwright run against a running server):

- **A latent `uv run --project` CWD bug, now fixed at its root**: every documented setup/dev command in
  this repo (`make migrate`/`make seed`/`make dev-api`, `scripts/migrate.sh`, `scripts/seed.sh`) invokes
  `uv run --project apps/api <command>` from the REPO ROOT. `--project` sets uv's dependency-resolution
  root; it does **not** change the process's actual working directory (confirmed directly: `uv run --project
  apps/api python -c "import os; print(os.getcwd())"` from repo root prints the repo root, not `apps/api`).
  Since `app/core/config.py`'s `Settings.model_config = SettingsConfigDict(env_file=".env")` resolved that
  path relative to the process's cwd, every one of those commands was silently looking for `.env` at the
  repo root (where only `.env.example` exists, never `apps/api/.env`, the real one) and falling back to
  `database_url`'s hard-coded Postgres default — which then HANGS (rather than failing fast) connecting to
  a Postgres that was never running, on this Windows environment's networking stack. This is the exact same
  root cause Phase 9 already diagnosed and fixed for one call site (`cd apps/api` first, or pass
  `DATABASE_URL` explicitly) — but that fix was a workaround at each call site, not a fix to the actual bug,
  so it silently persisted in every script/Makefile target that was never personally re-run from a plain
  repo-root shell this way before. Found while applying this phase's own migration via the documented
  `./scripts/migrate.sh`, which hung for the first time all project. Fixed at the root instead of adding a
  fourth workaround: `Settings.model_config`'s `env_file` is now an absolute path anchored to `config.py`'s
  own file location (`Path(__file__).resolve().parent.parent.parent / ".env"`), so `.env` resolution no
  longer depends on the invoking process's cwd at all, for any command, forever — verified directly (`uv run
  --project apps/api python -c "from app.core.config import get_settings; print(get_settings().database_url)"`
  from repo root now correctly prints the real sqlite path) and via a full clean backend suite re-run
  afterward (703 passed, 1 skipped, no regressions from the change).
- **A Playwright locator ambiguity, not a real bug**: the AI Layer's own E2E spec first failed asserting the
  learner's own chat message rendered, because `LocalProvider`'s deterministic reply text intentionally
  echoes the question back (`'Your message was received but not analyzed: "..."'`), so a non-exact text
  locator matched both the user's own message bubble and the assistant's much longer reply containing that
  same substring. Fixed by asserting `{ exact: true }` on the user-message check — the same class of
  "strict-mode locator ambiguity" already seen and fixed the same way during Phase 9's own E2E work.
- **`explain_plan`'s empty-fallback bug, then a real orphaned-process red herring while verifying the fix**:
  the Learning Planner explanation endpoint originally fell back to `AIPlanExplanationResult(day_
  explanations=[])` whenever the provider didn't return valid structured JSON — which is EVERY call under
  this platform's zero-configuration `AI_PROVIDER=local` default, so the feature produced nothing at all
  out of the box. Fixed by degrading to one explanation per real plan day using the provider's raw text
  instead of an empty list (mirroring `search_knowledge`'s and `diagnose_skill`'s existing graceful
  fallbacks — this was the one coach method that hadn't gotten the same treatment), covered by a new test
  asserting every real day number gets a non-empty explanation. While *verifying* this fix against the live
  dev server, the API kept returning the old empty-list behavior even after editing the file and even after
  what looked like a clean `Stop-Process`-then-restart of the backend — `uv run --project apps/api uvicorn
  --reload` spawns a separate reloader process and a child worker process, and killing the reloader's PID
  does not reliably kill its child; the child kept running, orphaned, still bound to port 8000 and still
  serving the pre-fix code, while a freshly started reloader+worker pair sat immediately behind it unable to
  actually receive traffic. Diagnosed by comparing `Get-Process` (which no longer listed the reloader's old
  PID at all) against `Get-NetTCPConnection -LocalPort 8000`'s `OwningProcess` (which still named it) —
  confirming the code fix was correct by calling `AICoachService.explain_plan` directly in a one-off script
  first (7 real explanations, immediately), which narrowed the discrepancy to "something is intercepting
  the HTTP layer" rather than a logic bug. Fixed by explicitly killing the orphaned worker PID (found by
  process start-time, well before the current session's restart) rather than trusting the reloader's exit
  to have cleaned it up. A new, Windows-specific variant of the general "verify the actual running process
  is serving current code, don't assume `--reload` guarantees it" lesson already on record from Phase 9.

## What Phase 11 deliberately does not build

Explicitly out of scope, per the spec's own boundary: no automatic job applications, no automatic
recruiter messaging, no LinkedIn automation, no scraping of restricted websites, no automatic email
applications, no guaranteed job matching, and no autonomous career decisions — the platform remains a
personal preparation and career-intelligence system, never a job-application bot. No PDF-generation
backend was added for the Career Report — it reuses the existing client-side download pattern already
established for CSV exports (`results-grid.tsx`) rather than introducing a new export dependency.
Resume/JD file upload (`ResumeSource`/`JDSource` include `UPLOADED`) accepts pasted text as the only
implemented path in this environment — no `python-docx`/PDF-text-extraction dependency exists yet, so a
real `.docx`/`.pdf` upload endpoint is a natural, self-contained Phase 12 add-on rather than something
this phase needed to build to satisfy its own spec (paste already covers the full analyzer pipeline).
Assessment-percentage-per-skill (`CareerSkillMatrixEntry.assessment_pct`) is deliberately left `null` —
no existing join path from `AssessmentAnswer` to a single skill was clean enough to compute honestly in
this pass without overstating precision; every other Career Skill Matrix field (mastery, exercises
passed, projects, cases, mock-interview score) is a real, joined count.

While building and live-verifying Phase 11, one real, in-development bug was found and fixed before
completion:

- **A same-second `computed_at` ordering bug in SQLite, caught by the phase's own 12-step E2E test**: `JDAnalysis`/`SkillGap`/`CareerAssessment` all originally used `server_default=func.now()` for their
  "when was this computed" column, exactly like the existing `ReadinessSnapshot` precedent. SQLite's
  `CURRENT_TIMESTAMP` only has 1-second resolution, so when a test computed a `CareerAssessment` and then
  immediately asked for "the latest one" (well within the same second), `ORDER BY computed_at DESC` had a
  tie with no deterministic secondary sort key — SQLite is free to return either row on a tie, and it
  returned the wrong one. Found by the phase's own required 12-step E2E test
  (`tests/test_career_readiness_and_e2e.py`) asserting the just-computed assessment's id matched what
  "latest" returned — it didn't, reproducibly, once other tests in the same file had already created a
  couple of assessments moments earlier. Fixed at the model level (`app/models/career.py`'s `_utcnow()`
  helper), not by patching the one call site: every affected column now also carries a Python-side
  microsecond-resolution `default=_utcnow` alongside its existing `server_default`, so "latest" is never
  ambiguous regardless of how quickly two rows are inserted — verified by re-running the full Phase 11
  suite (29 passed) and then the complete backend suite (734 passed, 1 skipped, zero regressions).

## What Phase 12 deliberately does not build

A 7-agent parallel research audit ran before any implementation specifically to avoid rebuilding what
already existed (the spec's own explicit instruction) — see the Phase 12 table row above for what that
audit found already solid (skill taxonomy, error handling, dark mode, loading/empty/error states,
accessibility, sandbox/AI security, CORS, secrets hygiene) versus genuinely missing (Next Best Action,
System Health, Data Integrity Audit, Job-Ready Checklist, Backup/Restore, request-id logging, expanded
search, command palette). Beyond that split, several spec items were consciously scoped out rather than
built as low-quality filler:

- **No separate visual "Skill Graph" explorer page.** The real prerequisite data that would back one
  already exists and already powers recommendations/locking (`LessonPrerequisite`, Phase 2) — what wasn't
  built is a dedicated new graph-visualization UI for it. The dbt Lab's own lineage DAG (Phase 7) remains
  the one real graph-visualization surface on the platform.
- **No separate "Offline Mode" toggle or banner.** The platform is offline-capable by construction (no
  feature outside AI/Kaggle requires network access, and both of those degrade to a clear "not configured"
  state — see `docs/troubleshooting.md`) — there was no missing capability to add, only a UI affordance
  that would announce a property the platform already has. A literal toggle/banner remains a reasonable
  small addition if user testing shows people don't realize this.
- **No "Reset Lab" or "Demo Mode."** Reset Lab would need an `is_demo`/reset-safe flag threaded through
  roughly 35 tables to distinguish "seed content" from "a real user's progress" — a real schema change
  across most of the platform, not a Phase 12-sized addition. Demo Mode has the same dependency and
  additionally needs hand-authored sample progress data (a content task, not a code task). Both are
  reasonable candidates for their own dedicated future phase rather than a rushed, risky addition here.
  `docs/backup-restore.md` covers the platform's actual data-safety story today (back up before you
  experiment).
- **No static-site Portfolio export or ZIP Project export.** The Career layer's Portfolio (Phase 11)
  already structures everything a static export would need (projects, cases, certifications, skill
  highlights, a quality score); what's missing is only the file-generation step itself, deferred rather
  than rushed.
- **No unified cross-system Lineage Explorer beyond the dbt Lab's own.** The dbt Lab's lineage DAG (Phase
  7, read from dbt's real `manifest.json`) already satisfies the dbt-specific portion of this ask; a
  broader explorer spanning datasets/SQL Lab/Python Lab lineage as well would be a substantial new
  feature, not a Phase 12 integration task.
- **No general HTTP rate-limiting middleware.** Accepted as a reasonable local-first, single-user
  tradeoff (see `docs/security.md`'s "out of scope" section) — only the AI daily-request-limit and the
  Python Lab's per-user concurrent-container cap exist. Revisit before ever exposing this API beyond
  localhost.
- **5 new focused docs, not ~17 thin stubs.** `docs/security.md`, `docs/backup-restore.md`,
  `docs/troubleshooting.md`, `docs/ai.md`, and `docs/career.md` cover the spec's documentation asks
  consolidated by topic rather than split into many single-paragraph files — each is real, audit-verified
  content, not a placeholder.

## Found while building and live-verifying Phase 12

- **A real N+1 performance bug, measured and fixed**: the Career Skill Matrix (`GET /career/skill-matrix`)
  measured at ~725ms p50 because `career_evidence.py::compute_skill_evidence` ran ~5 queries per skill,
  re-fetching the same "all completed projects"/"all completed case attempts" result sets 38 times over —
  once per skill. Fixed with a new `compute_all_skill_evidence()` that fetches each source table exactly
  once and aggregates in Python; p50 dropped to ~151ms (~4.8x), verified via a dedicated regression test
  (`test_career_evidence_performance.py`) asserting the batch function's output is identical, skill by
  skill, to the original per-skill function's for all 38 real skills.
- **A real, reproducible test flake, root-caused rather than retried away**: `score_attempt()` in both
  `app/python_lab/evaluation.py` and `app/sql/evaluation.py` compute an efficiency-score component from
  `student_execution_time_ms / reference_execution_time_ms`. For near-instantaneous (sub-20ms)
  executions, ordinary OS scheduling jitter alone can push that ratio into a penalty band, intermittently
  scoring a genuinely correct submission below 100 — confirmed via a 25x-repeat probe (24/25 scored
  100.0, one scored 95.0). Fixed with a `MIN_MEANINGFUL_TIME_MS = 50` noise floor in both files (full
  efficiency credit whenever both times are ≤50ms; a genuinely slow submission still gets penalized since
  its own time exceeds the floor), covered by new fast unit tests rather than relying on the slow probe.
- **Another instance of the recurring Windows "orphaned reloader child" bug** (first documented in
  Phase 10's entry above): two new `platform` router endpoints (`/data-integrity`, `/job-ready-checklist`)
  returned 404 against the running dev server even though their code was correct and their sibling
  endpoints in the same file worked — the process actually bound to port 8000 had started ~15 minutes
  before those two routes were added to the file, and `uvicorn --reload`'s file-watcher had silently
  failed to pick up the change. Confirmed via the same diagnostic `docs/troubleshooting.md` already
  documents (comparing `Get-Process` against `Get-NetTCPConnection`'s `OwningProcess`); fixed by killing
  the stale process tree and starting a clean instance, after which both endpoints returned correct data
  immediately.
- **The Phase 12 nav/Settings redesign broke several pre-existing E2E locators — a real, expected
  consequence of an intentional UI change, fixed at the test layer**: `dashboard.spec.ts` and
  `learning-loop.spec.ts` asserted a nav *link* literally named "Learn"; the new grouped nav
  (Main/Learn/Analyze/Data Stack/Cases & Projects/Interview/AI/Career/Knowledge/Settings) makes "Learn" a
  section *heading*, with "Curriculum" as the actual link — both specs updated accordingly (plus
  `exact: true` where a substring match now also caught unrelated headings/buttons containing the same
  word, e.g. a dashboard "Browse the curriculum" quick action). `ai-layer.spec.ts` asserted an "AI
  Settings" heading was immediately visible on `/settings`; Settings is now tabbed
  (Profile/Appearance/AI/Data/System), so the spec now clicks the "AI" tab first — and again after a
  `page.reload()`, since tabs correctly reset to their default on a fresh mount. While fixing the second
  of these, an unrelated, genuinely pre-existing locator ambiguity was also found and fixed:
  `learning-loop.spec.ts`'s "already completed" check (`getByText("Completed")`) also non-exact-matched a
  `'completed'` string literal inside the SELECT lesson's own SQL code sample — tightened to
  `exact: true`. A second unrelated, genuinely pre-existing issue was found while chasing an apparent
  flake in the same file: two tests shared an implicit ordering dependency (one completes a lesson, the
  next checks the dashboard reflects it) that the config's `fullyParallel: true` doesn't honor — the two
  tests were racing, previously invisible only because both tests always failed at the earlier "Learn"
  link step before either issue could surface. Fixed with `test.describe.configure({ mode: "serial" })`
  for this file's describe block. None of the other 6 E2E failures observed this phase are Phase-12-caused
  regressions: the Python Lab's 2 failures reproduce the same "no Docker daemon available in this
  environment" limitation documented since Phase 4; `case-studies.spec.ts`'s "Attach evidence"
  strict-mode violation and `sql-lab.spec.ts`'s saved-query-history/`order_id` strict-mode violation are
  both the same non-idempotent-long-lived-dev-database property already documented in Phase 8/9's entries
  above (more accumulated runs, more matching elements); `data-engineering.spec.ts`'s dbt-lab timeout was
  not reproduced on a clean re-run and is treated as incidental flakiness, not a Phase 12 regression — as
  was a one-off `interview-engine.spec.ts` checkbox-click timeout (passed cleanly every time it was
  re-run individually). One full-suite run this phase also came back with 9 unrelated-looking failures
  (including a Playwright "session closed" protocol error mid-test) after an unusually long ~2.4-hour
  runtime versus this same suite's normal ~1-2 minutes — strong evidence the host machine itself was
  suspended mid-run; a clean re-run immediately after reproduced none of those 9 failures, confirming
  they weren't real.

## Phase 12 polish pass — a second, deeper audit after initial completion

After Phase 12's own scope was done, a further round was run at the user's explicit request to find and
fix any remaining real bugs/imperfections and add genuinely valuable missing pieces — not a re-litigation
of what was deliberately deferred above. This started with 5 parallel research agents auditing the AI
layer, Career layer, the new Platform layer, frontend UI polish, and content integrity, each instructed to
report only real, traced findings. Real, confirmed issues found and fixed:

- **A real Backup/Restore bug that could zero out an entire restore**: `AISettings`/`CareerProfile`/
  `Portfolio` are lazily auto-created (a fresh id) the first time their feature is touched — e.g. simply
  loading the dashboard's Next Best Action card creates a `CareerProfile`. Restoring an older backup whose
  bundle carries the SAME logical row under a DIFFERENT id crashed on that table's real `UniqueConstraint(
  "user_id")`, aborting the whole restore with zero rows recovered — arguably the primary real-world use
  case for the feature. Fixed by matching these three singleton-per-user tables by `user_id` instead of
  `id` and updating the existing row's fields in place; a first pass of this fix over-counted every match
  as "restored" even when nothing actually changed, breaking the existing no-op test — caught and fixed
  with a second, deterministic regression test that doesn't depend on incidental test ordering. Also fixed
  a real, related UI bug: the restore-confirmation checkbox said "this will overwrite your current data,"
  directly contradicting the actual (additive/idempotent) behavior — reworded, and `docs/backup-restore.md`
  now documents the singleton-row exception explicitly.
- **A real AI-layer security gap**: `gateway.call` only ever redacts the CURRENT turn's message —
  conversation history was spliced into every later provider call verbatim, so a secret pasted into an
  earlier turn (stored as-is in `AIMessage.content`) would be replayed unredacted to a real OpenAI/
  Anthropic call on every subsequent turn in the same conversation. Fixed by redacting each history message
  before it's used, with a regression test that stores a secret-shaped message and asserts it comes back
  redacted from `_history_as_provider_messages`.
- **Four real AI-layer logic bugs**: `AISkillDiagnosisResult.improvement_areas` included every observed
  skill, including ones already flagged as `strength_areas` (a forgotten filter — fixed to exclude
  "strong" observations); `daily_request_limit=0` (meaning "block everything") was silently overridden by
  the global default because `or` treats `0` as falsy (fixed to an explicit `is not None` check, with a
  new test); a 2xx response with a non-JSON body (e.g. a proxy in front of a real provider) crashed
  instead of degrading to the Gateway's documented clean-fallback contract, in both the OpenAI and
  Anthropic provider clients (fixed by catching `ValueError` alongside the existing `httpx` exceptions);
  and the daily usage counter had a lost-update race (two near-simultaneous requests, e.g. two open tabs,
  could each read the same count and silently drop one increment, or both slip past the limit check before
  either committed) — fixed with a SQL-level atomic compare-and-increment plus a `SAVEPOINT`-protected
  first-request-of-the-day insert, rather than the prior Python-side read-increment-write.
- **Real file uploads for resume/JD, replacing a client-side stopgap**: "Uploaded" previously only ever
  read a file's text via the browser's `file.text()` and submitted it through the paste endpoint — fine
  for `.txt`, silent garbage for `.docx`/`.pdf` (a real, traced bug: `file.text()` decodes binary content
  as UTF-8 with silent replacement characters, and a literal NUL byte in that garbage text made Postgres
  reject the save with **zero user-facing error**, since neither mutation had an `onError` handler). Fixed
  with real server-side extraction (`app/core/file_extraction.py` — `python-docx` for `.docx`, `pypdf` for
  `.pdf`, encoding-fallback text decoding for `.txt`/`.md`, a NUL-byte strip as defense in depth) behind two
  new upload endpoints, and the frontend now uploads the real file via `apiClient.postFile` instead of
  reading it client-side — both resume and JD save mutations also gained `onError` toasts they never had.
- **A real, actually-broken command-palette keyboard bug**: list items were plain, independently-tabbable
  `<Link>`s with no `tabIndex`, so a keyboard user could Tab onto a different item than whatever
  `activeIndex` (the only thing Enter ever activated) last pointed at via the arrow keys, silently
  activating the wrong destination on Enter — confirmed live. Fixed with the standard ARIA combobox/
  listbox pattern (items are `role="option"`/`tabIndex={-1}`, no longer separate tab stops; the input owns
  `aria-activedescendant`), covered by two new tests (one using `@testing-library/user-event` to drive a
  real Tab keypress, since `fireEvent` can't simulate native tab-order traversal). The palette also had no
  touch/mobile entry point at all (`hidden ... sm:flex`) — added a mobile-visible icon button in the top
  bar using the same trigger.
- **Two real frontend UX bugs**: the dashboard's `CareerSnapshotTile` read `isLoading`/`data` but never
  `isError`, silently rendering nothing on a genuine fetch failure — indistinguishable from "no assessment
  computed yet" — while its sibling `NextBestActionCard` already handled this correctly; fixed to match.
  It was also the only dashboard block not wrapped in the shared `<Section>` component, breaking the
  page's heading hierarchy (h3 instead of h2) and looking visually inconsistent — fixed. Separately, the
  full-page `/ai/mentor` route never suppressed the always-rendered floating "AI Mentor" launcher, so
  clicking it opened a second, entirely independent chat panel stacked on top of the same page — fixed by
  hiding the launcher on that one route.
- **The `ai_configured`/local-mode disclosure banner never fired under the platform's own default
  config**: `Settings.ai_configured` (by design, per its own docstring) returns `true` for local mode,
  since local mode needs no key to function — but 5 frontend components gated a "you're seeing a local,
  no-network placeholder" disclosure banner on `!ai_configured`, which is therefore never true under
  `AI_PROVIDER=local` (this platform's zero-config default). The banner text was correct; the condition
  checked the wrong field. Fixed by checking the `effective_provider`/`provider` field every relevant
  response already carried (`=== "local"`) instead — no backend schema change needed. One test that forced
  the old (wrong) condition was updated to test the real one, and a new negative-case test confirms the
  banner correctly disappears once a real provider is configured.
- **A genuine, systemic content-quality gap, fixed with real per-file data verification**: all 15
  `content/cases/interview-*.yaml` reference solutions were generic, hedged template language ("traces to
  one specific channel," "a particular driver") instead of the concrete, verified answers every other case
  file has — since a case's `reference_solution` is revealed to the learner verbatim as the real worked
  answer to check against, a hedged one gives them nothing to verify. Fixed by computing genuine answers
  directly against the real seeded datasets (DuckDB against `data/sample/ecommerce`/`saas_product`) for all
  15 files — content validation confirms the same real counts (325 lessons/354 exercises/35 cases/etc.)
  with 0 problems both before and after. Where the data genuinely didn't support the hedge's implied
  "one clean culprit" story, the fix says so honestly instead of inventing one: two `saas-product` cases
  (DAU decline, retention cliff) found the effect was within normal noise or an instrumentation artifact
  rather than a real, isolable cause, and three `ecommerce` cases discovered the schema itself can't
  answer the literal question as posed (no ship/delivery timestamp exists anywhere for the two delivery-
  timing cases; no price-history mechanism exists at all for the pricing-impact case — verified by
  checking `order_items.unit_price` against `products.unit_price` for all 12,627 line items in the full
  order history, an exact match with zero exceptions) — each of those reference solutions pivots to the
  best real available proxy, states the real numbers it produces, and explicitly credits a learner who
  reaches the same "this is the actual limitation" conclusion, which is itself a genuine, valuable
  real-world analyst skill the original hedge never taught.
- Also fixed as a small doc-accuracy issue found during the audit: `app/ai/tools.py`'s module docstring
  claimed `AIToolbox` "is used directly by `app/services/ai_service.py`/`ai_coach_service.py`" — traced
  and confirmed false (`AIService.build_toolbox` exists and is constructible, but nothing in the codebase
  actually calls it during a real request); reworded to describe it accurately as an unused-so-far scaffold
  for a future live tool-calling loop.

Not pursued in this pass, as genuinely lower-value or out of proportion to the risk/effort: a TOCTOU race
on two truly concurrent restore calls (a real but low-likelihood edge case for a manually-confirmed,
single-user, local action); building frontend UI for the several real Phase 10 backend features an audit
found have no page calling them yet (domain coach, EDA Assist, Review Analysis/Insight, Communication/
Storytelling/Executive-Summary coaches, Project Review, Skill Diagnosis, and Phase 11's Resume/Portfolio/
JD/Career-coach AI endpoints) — a large scope of net-new UI work, not a bug fix, and a reasonable candidate
for its own future phase.

## Post-Phase-12 audit-and-fix pass — a further, broader sweep across every remaining subsystem

At the user's explicit, deliberately broad request ("fix all bugs, imperfections, failures, errors,
loading, data leakage, UI issues, and repo cleanliness... make it overall best... as much features as you
want"), a further round audited every subsystem not already covered by the Phase 12 polish pass above —
SQL Lab, Python Lab, Dataset Hub, Data Quality, Excel Lab, dbt exercises, the Career layer, JD/Interview
N+1s, a full frontend `isError`-handling sweep, and repo cleanliness — fixing every real, confirmed
finding and completing two genuinely unfinished features rather than just patching bugs. Real, confirmed
issues found and fixed:

- **A real SQL Lab sandbox-escape gap**: `DuckDbEngine` registered every dataset table as a `CREATE VIEW`
  over the real file path, so `enable_external_access=false` (meant to block arbitrary file reads/writes
  from student SQL) never actually took effect — a view still needs file access at query time. Fixed by
  materializing each table as a real `CREATE TABLE ... AS SELECT` before disabling external access,
  verified directly (both that `read_csv_auto`/`read_text`/`COPY TO` are now blocked AND that legitimate
  table queries still work). Two more real gaps in the same area: `EXPLAIN ANALYZE` actually executes the
  wrapped statement (unlike plain `EXPLAIN`), bypassing the forbidden-keyword check entirely — fixed by
  rejecting it outright; and the comment/statement splitter wasn't quote-aware, so a forbidden keyword
  hidden inside a string literal or a `--` sequence inside a quoted string could confuse the safety parser
  — rewritten as a proper char-by-char, quote-aware scanner.
- **A real SQL-grading gap**: a submitted query with an always-false predicate (`WHERE 1=0`) legitimately
  produces an empty result set, which is indistinguishable from a genuinely correct empty result using
  result-comparison alone — the platform's own stated grading philosophy never compares SQL text. Reasoned
  through explicitly and fixed with the narrowest defensible exception: when the expected result is empty,
  a submitted query is additionally checked for a literal `1=0`/`0=1` pattern and rejected as vacuous —
  scoped only to that one case, not a general retreat to text comparison.
- **Real Python Lab reliability bugs**: a division-by-zero producing `inf`/`-inf` crashed cell-output
  JSON serialization (only `nan` was guarded, not `inf`); a sandbox timeout silently returned a normal
  "success" result instead of raising, hiding a real failure from the caller; a container that died
  mid-session (OOM-killed, manually removed) raised an unhandled Docker API error on the next execute/
  restart instead of a clean, recoverable error; and runtimes stuck in `STARTING` past a grace period were
  never reaped, unlike every other terminal state.
- **Real Dataset Hub bugs**: profiling numeric columns crashed on a literal `NaN`/`Infinity` value in the
  source data (`isfinite` wasn't checked); and two files that slugify to the same table name (e.g.
  `Customer Data.csv` and `customer-data.csv`) silently overwrote each other's table during import instead
  of being deduplicated.
- **Real Data Quality engine bugs**: a `ROW_COUNT` or `FRESHNESS` rule created with no threshold at all
  silently evaluated as a pass/no-op instead of surfacing a clear configuration error; `FRESHNESS` against
  a non-date column crashed instead of reporting a clean ERROR status.
- **A real, inherited Excel Lab formula bug**: `VLOOKUP`'s approximate-match mode (`range_lookup` omitted
  or `TRUE`) was never actually implemented — a variable named `exact` was assigned the raw, un-inverted
  `range_lookup` value, silently masked because both old code branches happened to use equality checks
  either way. Fixed with a real approximate-match branch (last row where `key <= lookup_value`, mirroring
  `MATCH`'s own `match_type=1` algorithm) and the variable correctly inverted. Also fixed: `COUNTIFS`/
  `SUMIFS` with zero condition pairs silently returned 0 instead of Excel's real `#VALUE!`, and `COUNT`/
  `COUNTA` didn't propagate an error value found among their arguments before their own type checks.
- **A real dbt exercise sandbox gap**: a submitted model's `config()` could declare a `pre-hook`/`post-hook`
  that runs arbitrary SQL against the real warehouse outside the exercise's own sandboxed scope — fixed by
  rejecting any submission containing one before it ever reaches dbt.
- **Two real Career layer bugs**: `get_dashboard`/`get_report` counted `UserAchievement` rows without ever
  calling `AchievementService.sync_for_user` first, so a badge earned by something just completed only
  showed up once the user separately opened the Achievements panel — fixed by having `sync_milestones`
  (which both already call) sync achievements first. Separately, the Career Progress Timeline deduped
  milestones on title alone, so a second genuine completion of the same case/interview/project template (a
  fully supported retry) was silently dropped as a false duplicate — fixed by deduping on `(title,
  achieved_at)` instead, a lower-risk fix than a schema migration that still correctly tells a real retry
  apart from a true duplicate sync. While in this area, two of `CareerMilestoneType`'s three previously
  unused values were wired in for real: `ACHIEVEMENT_EARNED` (one Timeline entry per earned badge) and
  `READINESS_LEVEL_UP` (recorded only the first time a NEW PEAK readiness level is reached, not every
  recomputation, since readiness legitimately fluctuates run to run) — `ASSESSMENT_PASSED` was left
  deliberately unused since there's no real, modeled "assessment" event distinct from what cases/exercises/
  interviews already cover, and inventing one would violate the model's own "never invented" docstring.
- **Real N+1 query patterns fixed**: `JDService.compute_skill_gaps` and `.generate_preparation_plan`
  re-queried Skill/UserSkill per requirement and re-scanned the full Case/ProjectTemplate tables once per
  gap in a loop; `InterviewService._pick_candidate` issued a `db.get()` pair per prior attempt plus a lazy
  `.exercise` load per question on every single question pick; `CareerProfileService._sync_case_milestones`
  lazy-loaded `.case` per attempt; `PortfolioService._covered_skill_slugs` issued a `db.get()` plus a lazy
  relationship load per portfolio item. All rewritten to batch-fetch with `selectinload`/`IN` queries.
- **A real Kaggle zip-slip vulnerability**: `KaggleClient.download_file` called `zipfile.extractall`
  directly on a network-fetched, third-party archive with no member-path validation, so a malicious member
  name containing `../` segments could write outside the intended destination directory. Fixed with a
  `_safe_extract` helper that validates every member's resolved path stays under the destination first.
- **A real unbounded-upload vulnerability**: the resume/JD upload endpoints called a plain `await
  file.read()`, buffering an entire upload into memory BEFORE `extract_text`'s own 10MB size check could
  ever run — a multi-GB upload would be fully read into memory regardless of that limit. Fixed with a
  `read_upload_bounded` helper that reads in fixed 1MB chunks and rejects the upload the moment the running
  total crosses the limit, never buffering the excess.
- **A systemic frontend `isError` gap, fixed across 9 components (10 call sites)**: `visualization-
  workspace.tsx`, `product-analytics-workspace.tsx` (datasets + schema queries), `eda-launcher.tsx`,
  `notes-panel.tsx`, `relationships-panel.tsx`, `dataset-detail.tsx` (schema + quality queries), `data-
  quality-workspace.tsx`'s `RunHistory`, `kaggle-search-dialog.tsx`, and `project-data-model-tab.tsx` each
  checked `isLoading` and fell through empty/data branches but never checked `isError`, making a genuine
  fetch failure indistinguishable from "no data yet" with no retry affordance — all now show a real
  `ErrorState` with retry, matching the pattern already established elsewhere. The same conflation was
  found and fixed in the Weekly Review card (dashboard + Career Analytics) — a fetch error rendered the
  same "isn't available yet" copy as a genuine quiet week, with no retry option. `project-data-model-
  tab.tsx` also had a hardcoded `hover:bg-black/10` that was nearly invisible in dark mode — replaced with
  the theme-aware `hover:bg-foreground/10`; and `table-editor-sheet.tsx` had a fixed `w-[26rem]` sheet width
  that would overflow a phone-width viewport — fixed to `w-full max-w-[26rem]`, matching the responsive
  pattern every other sheet in the app already uses.
- **Two features finished rather than left half-built**: the **EDA Assist** AI feature (flagged as
  arguably the single highest-value invisible AI feature — a fully-built backend with zero frontend caller)
  now has a real "Ask AI to help explore this dataset" panel on the EDA Workspace, calling both the
  grounded Assist and the goal-directed Explore-with-AI endpoints. Building it surfaced one more real gap:
  `DATA_EXPLORATION`'s own prompt documented an optional `user_goal` input that was never actually accepted
  or forwarded anywhere in `EdaAssistRequest`/`eda_assist()`/the router — wired through end to end, verified
  with a regression test against the deterministic `local` provider's verbatim message echo. Separately,
  **SQL Workspaces** (a named engine+database grouping for saved queries) had a fully-built backend
  (model/service/router/schema) and a `workspace_id` prop already threaded through `SavedQueriesPanel`, but
  no picker anywhere ever set it — so it was always `undefined` in practice, and its own hook file
  (`use-sql-workspaces.ts`) had zero callers. Rather than deleting real, working, already-tested backend
  code, added a `WorkspaceSelector` (list/create, scoped to the current engine+database pairing) to the SQL
  Lab toolbar and wired it through.
- Also fixed as small polish found along the way: `error.tsx`'s root error boundary used
  `window.location.assign()` instead of `useRouter().push()` (a Next.js lint rule specifically flags this)
  and carried a redundant `eslint-disable` comment that no longer suppressed anything.

Every fix above has a dedicated regression test verifying the real behavior (not just that the code
compiles) — new/updated backend suites: SQL security, SQL evaluation, Python kernel/security/runtime
recovery, dataset profiling/import, data quality, Excel formula engine, dbt exercises, Kaggle (zip-slip),
file upload extraction (bounded read), EDA workspaces (AI assist), and three new Career-layer test classes
(dashboard/report achievement sync, Timeline retry-vs-duplicate dedup, readiness-level-up and achievement-
earned milestones). Final verification: the full backend suite (836 tests) and full frontend suite (119
tests across 37 files) both pass with zero regressions, alongside a clean full-project TypeScript typecheck
and ESLint run (0 errors, 0 warnings).

Not pursued in this pass, as genuinely lower-value or explicitly out of scope: ~15 FK relationships in
`data_integrity_service.py` with no matching integrity check (a real gap only on SQLite — Postgres already
enforces these at the schema level in production); `AchievementService`'s bounded ~9-badge-per-call check
pattern (already explicitly documented as low-priority in that module's own reasoning); and LOW-severity
test-coverage gaps on a handful of lower-traffic endpoints/frontend features (`users.py`/`portfolio.py`/
`jobs.py`, and the data-modeling/product-analytics/dbt-lab/findings/analytics-cases frontend features) —
these are coverage gaps on already-working code, not bugs, and a reasonable candidate for a future,
dedicated test-writing pass rather than folded into a bug-fix sweep.

## Personalization pass — app identity and removing a placeholder email

At the user's request, the app's identity moved from a generic `APP_NAME`/`APP_TAGLINE`
("Data Lab") (`packages/shared/src/
constants.ts`, the single source both the sidebar brand mark and the dashboard heading/tagline read
from), the root `<title>`/meta description (`apps/web/src/app/layout.tsx`, now reading the same
constants instead of a second hardcoded copy), and the AI Mentor's own system preamble (`app/ai/
prompts/base.py`) so it refers to itself correctly.

Separately, the placeholder seed email (`app.db.seed.SEED_USER_EMAIL`) was blanked out — removed from
the seed script, the live dev database, and an existing backup snapshot's manifest. Doing this surfaced
a real bug: `UserProfile.email` was typed `EmailStr`, which rejects an empty string outright, so
`GET /users/me` (and anything calling it) started 500ing the moment the email went blank. Fixed by
relaxing that one field to a plain `str` — this is a single-user local app where email is never used
for auth or notifications, so RFC-strict validation added no real value and directly blocked the
requested change. Also fixed the one UI spot depending on the old assumption that email was always
non-empty: the user-menu dropdown's second line (`components/layout/user-menu.tsx`) now hides itself
when there's no email instead of rendering a blank line. `_seed_user`'s matching logic was also
changed from "does a user with this email exist" to "does any user row exist" — matching by email was
never a safe natural key once the email itself is expected to be blank, and this closes a latent
duplicate-user-row risk for good, not just for the current blank value.

Confirmed via the full backend suite (836 tests, including the EmailStr regression) and full frontend
suite (119 tests) both passing, plus a clean typecheck/lint on both sides.

## Visual design overhaul — colorful, animated, modern shell

At the user's request ("looks very plain/ordinary... I want fully colorful, with icons, logos, visuals,
effects, live animations, modern"), the frontend's visual language moved off the stock shadcn/ui
near-monochrome palette toward a colorful, animated, section-coded design system — applied at the
highest-leverage layer (shared primitives + shell) rather than by hand-editing every route, so it
propagates to virtually every page automatically:

- **A ten-color section-accent system** (`apps/web/src/app/globals.css`'s `--section-*` tokens, mapped
  from each `NAV_SECTIONS` label in `packages/shared/src/section-theme.ts`): Learn=blue, Analyze=purple,
  Data Stack=teal, Cases & Projects=amber, Interview=rose, AI=pink, Career=emerald, Knowledge=gold,
  Settings=slate, Main=violet — plus brand gradient (`.gradient-brand`/`.text-gradient-brand`), a subtle
  animated mesh background (`.bg-mesh`), glassmorphism (`.glass`), a hover-lift (`.card-hover`), a glow
  shadow, and shimmer/float keyframes, all reduced-motion-aware.
- **`framer-motion` added** for real spring/staggered animation (previously zero animation library beyond
  static Tailwind transitions).
- **A new animated, colorful logo** (`BrandMark`, gradient chip + hover tilt) and a real generated favicon
  (`app/icon.tsx`, previously none existed at all).
- **The sidebar** now color-codes each section (a colored dot per section heading, a colored icon chip on
  the active item) with a framer-motion `layoutId`-animated active-pill that slides between items —
  namespaced per sidebar instance (desktop vs. the mobile sheet) since both stay mounted simultaneously
  and would otherwise fight over one shared layout animation.
- **Core primitives upgraded**: `Button` gained a `gradient` variant plus tactile press/hover feedback;
  `Progress`'s fill is now the brand gradient; `Skeleton` shimmers instead of a flat pulse; `Card` animates
  its shadow.
- **The Dashboard's four stat cards** now each carry a distinct section color, a gradient icon chip, and
  an `AnimatedNumber` count-up (a small framer-motion component, careful to only call `setState`
  synchronously inside its reduced-motion early-return path — an initial version tripped the
  `react-hooks/set-state-in-effect` lint rule by doing so unconditionally); the dashboard's own hero
  heading got a gradient-text treatment over the new mesh background.
- **Every one of ~29 feature pages' headers picked up the new colorful, icon-chip, animated treatment for
  free**: they already funneled through one shared `<PageHeader title=".." subtitle=".." />` component
  (discovered only after an initial mistake — a first pass created a NEW `page-header.tsx` with an
  invented, incompatible prop contract, silently overwriting the real one and breaking all ~29 callers,
  caught immediately by `tsc --noEmit`). The rebuilt version keeps the exact original `{title, subtitle?,
  action?}` contract those callers already use, and adds new optional `icon`/`color` props alongside an
  auto-detection path (`lib/nav-lookup.ts`'s longest-prefix match against `NAV_SECTIONS`) so a page with no
  explicit override still gets the right icon and section color purely from its own route — verified live
  against several different sections (`/sql-lab` renders 7 purple accents, `/learn` 7 blue, `/career` 7
  emerald, confirming each page really does resolve its own section rather than one fixed color).

Verified via a clean `tsc --noEmit`, a clean ESLint run, the full 119-test frontend suite, and a full
production `next build` (50 routes, including the new `/icon` route) all passing with zero errors.

Not done in this pass, as a much larger page-by-page effort rather than a shell/design-system change:
bespoke visual redesigns of individual feature workspaces' own internal content (the SQL/Python Lab
editor chrome, dataset/case/project list cards, chart containers, admin panels, etc.) — these already
inherit the upgraded Button/Card/Progress/Skeleton primitives and their page's own colorful header, but
have not each been individually reworked beyond that.

## Progress/test-history reset — a fresh start with content untouched

At the user's request, cleared all accumulated development/testing activity from `data/dev.db` while
leaving every content/catalog table untouched — every model in `apps/api/app/models/` was individually
classified as either content (never touched: domains, modules, lessons, exercises, skills, tags,
assessments, cases, project templates, interview questions/templates, role templates, metric
definitions, the achievement catalog, and the 3 seeded practice datasets) or the user's own
activity/history (cleared: lesson progress, skill mastery, exercise/assessment/case attempts, SQL/Python
Lab workspaces and history, projects, interviews, career milestones/goals/assessments/achievements,
resumes, portfolio, job descriptions, AI conversations, EDA workspaces, charts, data models, dbt runs,
findings/hypotheses/evidence, and 7 leftover `e2e-products-*` datasets identified as stray Playwright test
fixtures, along with their profiling data). The single `users` row and `ai_settings` (a preference row,
not activity history) were left alone. 721 rows removed; a full sanity check afterward confirmed every
content table's count unchanged and the live `/progress/summary`/`/career/dashboard` endpoints reflecting
a genuine 0%/blank fresh start.

Two full safety nets were taken before any deletion: a complete raw file copy of `data/dev.db`
(trivially restorable by copying it back) and a JSON export via the platform's own Backup feature.
Exporting that JSON backup surfaced a real, previously-undiscovered bug: `BackupService.export_bundle`
assumed every backed-up model has a synthetic `id` primary key, but `LessonProgress` uses a composite
`(user_id, lesson_id)` key — so the export crashed with an `AttributeError` the moment any real lesson
progress existed (which, after this platform's own extensive development/testing, it did). The same
`.id`-assuming bug was also present in `preview_restore` (falsely flagging every `LessonProgress` row as
corrupted) and in `restore_bundle`'s idempotency check (`row["id"]` would `KeyError`). Fixed generically —
a `_row_identity` helper builds the correct scalar-or-tuple key for `Session.get()` from a model's real
primary-key columns, used consistently by all three code paths — rather than special-casing
`LessonProgress` alone, so any future composite-key entity added to the backup system is handled
correctly too. Covered by a new regression test that round-trips a real composite-key row through
export → preview → restore.

Verified via the full backend suite (836 tests; one unrelated, pre-existing order-dependent flaky test —
`test_python_exercises_integration.py`'s exercise-submission test — passes cleanly in isolation and is
unaffected by anything in this pass) and a clean ruff check on both changed files.
