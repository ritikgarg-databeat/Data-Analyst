# AI vs. Deterministic Authority (Phase 10, spec section 50)

This file is the one canonical statement of a rule that every module under
`app/ai/` and every AI-aware service method must follow. When in doubt, this
file wins over a docstring, a prompt, or a model's own claim.

## The deterministic systems always win for

- SQL correctness — `app/sql/evaluation.py`, real DuckDB/Postgres execution.
- Python correctness — `app/python_lab/evaluation.py`, real sandbox execution.
- Statistical/mathematical calculations — `app/stats_engine/`,
  `app/experimentation_engine/`, `app/dataset_hub/product_analytics_engine.py`.
- dbt build/test results — `app/dbt_lab/`, real `dbt` CLI execution.
- Data-modeling validation — `app/data_modeling/validation.py`.
- Case/interview/exercise scores — `app/case_engine/grading.py`,
  `app/interview_engine/scoring.py`, `app/services/grading.py`.
- Readiness/weakness/mastery — `app/interview_engine/readiness.py`,
  `app/interview_engine/weakness.py`, `app/services/mastery.py`.
- Timers — `InterviewService._is_over_time_limit` and friends.
- Dataset metadata — `app/dataset_hub/`, `app/services/dataset_analysis_service.py`.

No AI code may recompute, override, or silently disagree with any of the
above. An AI feature may **narrate, explain, question, or coach around** a
deterministic result; it may never present its own number in place of one
that already exists. Where an AI response needs to reference such a value,
the calling service passes the already-computed value into the model's
context — the model is never asked to compute it itself.

## AI provides

- Explanations of *why* a deterministic result looks the way it does.
- Suggestions, alternative approaches, and coaching questions.
- Reasoning/communication feedback (never a numeric score).
- Socratic tutoring (hints before solutions).
- Conversational interviewing (case/behavioral), bounded by fixed case facts.
- Retrieval-grounded answers to "what does X mean" questions (RAG, section 61-64).

## Concretely, in code

- `app/ai/gateway.py` never touches a domain table. It receives an
  already-built, already-redacted context payload and an already-rendered
  system prompt; it calls a provider and validates the shape of what comes
  back. It has no idea what "correct" means for any exercise.
- Every `app/ai/context/*.py` builder is a pure function: real ORM/schema
  objects in, a small `dict` (or a redacted string) out. None of them invent
  a field that isn't already present on the object they're given.
- `app/services/ai_service.py` / `app/services/ai_coach_service.py` are the
  only places allowed to call both an existing domain service (to fetch real,
  already-computed data) and the Gateway (to get commentary about it) — and
  they never write the domain service's own tables.
- Every structured AI output that makes a claim about the learner's data must
  tag that claim as `OBSERVED` / `INFERRED` / `HYPOTHESIS` / `UNKNOWN`
  (`AIClaimType`, spec section 17) — enforced by the Pydantic response
  schemas in `app/schemas/ai.py`, not left to the model's discretion.
