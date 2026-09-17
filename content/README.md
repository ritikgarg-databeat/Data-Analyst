# Content

This directory is the content-driven counterpart to the `database/` structural data. The database
stores *structure and progress* (which domains/modules/lessons exist, in what order, how far the user
has gotten, prerequisites, tags); this directory stores the *authored material itself* as YAML files,
referenced from the database via `content_reference` columns (`Lesson.content_reference`,
`Exercise.content_reference`) and reconciled into the database by `apps/api/app/content/sync.py`.

Lessons should never be hard-coded into React components — always author them here.

## Layout

- `lessons/<domain-slug>/<module-slug>/<lesson-slug>.yaml` — lesson content: metadata (title,
  objectives, difficulty, prerequisites, skills, tags, datasets, completion_criteria, key_takeaways,
  common_mistakes, interview_questions, resources) plus a `blocks:` list — the lesson body, as a
  sequence of typed content blocks. Schema: `schema/lesson.schema.json` (Pydantic-enforced at
  `apps/api/app/content/schema.py::LessonContentFile`; mirrored in TypeScript at
  `packages/shared/src/content-types.ts`).
- `exercises/<domain-slug>/<exercise-slug>.yaml` — exercise content: prompt, `exercise_type`, optional
  `choices`/`correct_answer` (for auto-gradable types), progressive `hints`, `solution`, `explanation`.
  Schema: `schema/exercise.schema.json` / `ExerciseContentFile`. `exercise_type: SQL` exercises additionally
  carry `dataset` (a real `Dataset` slug), `business_context`, `sql_tables` (which tables to surface),
  `sql_starter_query`, `sql_solution_query` (never sent to the client — see `/api/v1/sql/exercises/{slug}`),
  `sql_row_order_matters`/`sql_numeric_tolerance` (comparison config), and optional `sql_hidden_tests`
  (extra keyed-lookup checks against the *student's own* result — see
  `docs/architecture.md#sql-lab-phase-3`). They're graded by real execution, never by comparing SQL text.
  `exercise_type: PYTHON` exercises carry the analogous fields: `dataset`, `business_context`,
  `python_datasets` (dataset files to pre-load as DataFrames, e.g. `orders`/`customers`/`payments`),
  `python_starter_code`, `python_solution_code` (never sent to the client), `python_result_variable`
  (default `"result"` — the variable name both student and solution code must define),
  `python_row_order_matters`/`python_numeric_tolerance`, and optional `python_hidden_tests` — Python
  snippets (typically `assert` statements) run in the *student's own* kernel namespace after correctness
  passes. See `docs/architecture.md#python-lab-phase-4`.
  `exercise_type: DBT` exercises carry `dbt_model_name` (the model name a submission is written to, as
  `dbt/models/exercises/<name>.sql`), `dbt_starter_sql`, and `dbt_schema_yml` (never sent to the client —
  the `columns:`/tests block nested under that model in a generated `schema.yml`). Graded by running an
  actual `dbt build --select <model>` against the real local dbt project (`dbt/` at the repo root) — a
  submission passes because dbt itself reports the model built and its tests passed, never by comparing
  SQL text against `solution`. See the "dbt Lab" section of the top-level `README.md`.
  `exercise_type: EXCEL` exercises carry `excel_starter_sheets`/`excel_solution_sheets` (each a list of
  `{name, cells}`, where `cells` maps a cell ref like `"B2"` to a literal or a formula string starting
  with `=`) and `excel_check_cells` (e.g. `["Summary!B2"]` — the only cells actually compared between the
  student's and the solution's workbook). Both workbooks are evaluated for real by
  `apps/api/app/excel_lab/formula_engine.py` (a real tokenizer/parser/evaluator, ~34 functions), never by
  comparing formula text — a student is free to build whatever helper columns they like en route to the
  check cells.
- `cases/<case-slug>.yaml` — Phase 8 Case Study Engine content: a stakeholder problem statement, a
  `stages:` sequence, `clarification_guidance`, a weighted `rubric` (categories of criteria, one category
  optionally `is_technical` and scored from real `ExerciseAttempt` pass/fail via `required_exercise_slugs`
  instead of self-assessment), `hints`, and a `reference_solution` withheld until submission. Tag a case
  `"interview"` (plus keep it short — fewer stages, ~25-30 `estimated_minutes`) for it to be eligible as a
  Phase 9 interview Case Study round; see `apps/api/app/content/schema.py::CaseContentFile`.
- `projects/<template-slug>.yaml` — Phase 8 Project Engine templates: milestones, suggested datasets,
  required skills, and an optional rubric for a longer, learner-driven capstone.
- `interview/questions/<category>/<slug>.yaml` — Phase 9: a thin wrapper around an *existing*
  `exercise_slug` (never a copy of its prompt/hints/solution), adding only `interview_type` (one of the 14
  round types, e.g. `SQL`/`EXCEL`/`BEHAVIORAL`), an optional `time_limit_seconds`, `follow_up_slugs`
  (other interview-question slugs asked as an interviewer follow-up once this one is answered correctly),
  and `company_archetypes`. See `apps/api/app/content/schema.py::InterviewQuestionContentFile`.
- `interview/templates/<template-slug>.yaml` — Phase 9: a Mock/Company-Style interview structure — an
  ordered `sections:` list (`{interview_type, title, duration_minutes, question_count, difficulty}`,
  where `interview_type` can also be the literal `"CASE_STUDY"` to reuse a tagged `cases/` file for that
  round) plus `rubric_weights` (the 6 scoring-dimension weights, must sum to 100).
- `domains/`, `modules/` — reserved; dedicated domain/module landing content is a possible later addition
  (domains/modules themselves are seeded from `database/seeds/*.yaml`, not authored here).
- `datasets/` — reserved for dataset documentation/profiles (the actual data files live under top-level
  `data/`, referenced by `Dataset.file_path`).
- `schema/` — JSON Schema mirrors of the enforced Pydantic models, for reference/tooling.

## Why YAML, not Markdown+frontmatter

A lesson body is a sequence of **12 distinct block types** (text, heading, callout, code, output, table,
formula, image, example, question, checklist, comparison) — a comparison table or an inline
multiple-choice knowledge check isn't cleanly expressible in Markdown without inventing custom directive
syntax. YAML expresses this directly and stays fully human-editable. `text`/`callout`/`example` block
`body` fields support light inline Markdown (`**bold**`, `*italic*`, `` `code` ``, `[text](url)`) rendered
by the frontend.

## Authoring a lesson

Look at an existing file for the exact shape, e.g.
`content/lessons/data-analyst-foundations/how-to-use-this-lab/the-learning-loop.yaml` (short) or
`content/lessons/sql/sql-fundamentals/select.yaml` (a fuller technical lesson with a `code` block and an
inline `question` knowledge check). Required top-level fields: `slug`, `module_slug` (must reference a
module already defined in `database/seeds/modules.yaml`), `title`, `description`, `difficulty`,
`estimated_minutes`, `display_order`, `objectives`, `key_takeaways`, `blocks` (at least one). `slug`
values referenced in `prerequisites`/`soft_prerequisites`/`related_lessons` must be real lesson slugs;
`skills`/`datasets`/`tags` values must match slugs in the corresponding `database/seeds/*.yaml` file.

Use a YAML block scalar (`>` or `|`) for any multi-line prose field — a plain unquoted scalar containing
`: ` (colon-space) gets misparsed by YAML as a nested mapping instead of a string. This bit real content
files during authoring; `python -m app.content.validate` catches it (as a Pydantic "not a valid string"
error) but writing prose with block scalars from the start avoids it entirely.

## Validating and syncing

```bash
./scripts/validate-content.sh   # schema + cross-reference checks — no database needed
./scripts/sync-content.sh       # validates, then upserts Lesson/Exercise rows + relations into the DB
```

`sync-content` refuses to run against invalid content. It requires the database to already have the
taxonomy seeded (`./scripts/seed.sh`, which calls `sync-content` automatically at the end) since lessons
reference `module_slug` and skills/datasets/tags that must already exist as rows.

A lesson or exercise that's removed from `content/` (or renamed) is **deactivated**
(`is_active = false`) the next time sync runs, never deleted — so any progress history referencing it by
UUID is preserved.
