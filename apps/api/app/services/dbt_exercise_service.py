"""Connects the generic Phase 2 exercise system to REAL dbt execution.

A dbt exercise's content file (`exercise_type: DBT`) carries `dbt_model_name`
and `dbt_schema_yml` (see app/content/schema.py). Grading writes the
student's submission into the actual dbt project
(dbt/models/exercises/<model>.sql, plus a generated schema.yml if the
exercise defines tests) and runs a real `dbt build --select <model>` — see
app/dbt_lab/runner.py. There is no solution-string comparison anywhere in
this file: a submission passes because dbt itself says the model built and
its tests passed.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.schema import ExerciseContentFile
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.dbt_lab import artifacts
from app.dbt_lab.paths import DBT_PROJECT_DIR
from app.dbt_lab.runner import DbtRunnerError, run_dbt
from app.models.enums import ExerciseAttemptStatus
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.lesson_progress import LessonProgress
from app.schemas.dbt import DbtExerciseContent, DbtExerciseTestOutcome, SubmitDbtExerciseResponse
from app.services.mastery import MasteryService

EXERCISES_DIR = DBT_PROJECT_DIR / "models" / "exercises"
PROJECT_NAME = "personal_data_analyst_lab"

# The SQL Lab explicitly guards against write/DDL/admin SQL (app/sql/safety.py)
# because it runs untrusted user input through a real DuckDB engine. This
# dbt exercise path has the same shape of risk with no analogous guard at
# all: a submitted model is written verbatim into a real dbt model file and
# built via a real `dbt build` subprocess, and dbt's own `{{ config(...) }}`
# Jinja can declare a pre_hook/post_hook — arbitrary raw SQL dbt executes
# outside any wrapping, with full DDL/admin/file-I/O access to the real
# warehouse DuckDB file. Bounded severity (this is a single-local-user app,
# so the only person affected is whoever submits it, against their own
# local warehouse they already have filesystem access to) but still a real,
# closable gap for a "grading" surface that shouldn't need arbitrary-hook
# privileges to build one model.
_DBT_HOOK_PATTERN = re.compile(r"\b(pre|post)[-_]hook\b", re.IGNORECASE)


class DbtExerciseService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.mastery_service = MasteryService(db)

    def get_exercise_content(self, content: ExerciseContentFile) -> DbtExerciseContent:
        if not content.dbt_model_name:
            raise AppError("This dbt exercise has no model name configured.")
        return DbtExerciseContent(
            business_context=content.business_context,
            dbt_model_name=content.dbt_model_name,
            starter_sql=content.dbt_starter_sql,
            hint_count=len(content.hints),
        )

    def submit(
        self, user_id: str, exercise: Exercise, content: ExerciseContentFile, submitted_sql: str
    ) -> SubmitDbtExerciseResponse:
        if not content.dbt_model_name:
            raise AppError("This dbt exercise is not fully configured — missing a model name.")
        model_name = content.dbt_model_name

        if _DBT_HOOK_PATTERN.search(submitted_sql):
            raise AppError(
                "pre_hook/post_hook config is not allowed in a submitted model — write the model's "
                "actual transformation logic instead."
            )

        self._write_submission_files(model_name, submitted_sql, content.dbt_schema_yml)

        try:
            result = run_dbt(["build", "--select", model_name], settings=self.settings)
        except DbtRunnerError as exc:
            attempt = self._persist_attempt(
                user_id, exercise, submitted_sql, ExerciseAttemptStatus.FAILED, 0.0
            )
            return SubmitDbtExerciseResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                score=0.0,
                passed=False,
                model_built=False,
                test_outcomes=[],
                log=str(exc),
                explanation=None,
            )

        model_result = artifacts.get_node_result(f"model.{PROJECT_NAME}.{model_name}")
        model_built = bool(model_result and model_result.get("status") == "success")
        test_outcomes = self._collect_test_outcomes() if model_built else []

        passed_count = sum(1 for t in test_outcomes if t.passed)
        if not model_built:
            score = 0.0
        elif not test_outcomes:
            score = 100.0
        else:
            score = round(100.0 * passed_count / len(test_outcomes), 1)
        passed = model_built and score == 100.0

        status = ExerciseAttemptStatus.PASSED if passed else ExerciseAttemptStatus.FAILED
        log = (result.stdout + ("\n" + result.stderr if result.stderr else "")).strip()
        attempt = self._persist_attempt(user_id, exercise, submitted_sql, status, score)

        return SubmitDbtExerciseResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            score=score,
            passed=passed,
            model_built=model_built,
            test_outcomes=test_outcomes,
            log=log if not model_built else None,
            explanation=content.explanation if passed else None,
        )

    @staticmethod
    def _write_submission_files(model_name: str, submitted_sql: str, schema_yml: str | None) -> None:
        EXERCISES_DIR.mkdir(parents=True, exist_ok=True)
        (EXERCISES_DIR / f"{model_name}.sql").write_text(submitted_sql, encoding="utf-8")

        yml_path = EXERCISES_DIR / f"{model_name}.yml"
        if schema_yml:
            indented = "\n".join(f"    {line}" for line in schema_yml.splitlines())
            yml_content = f"version: 2\nmodels:\n  - name: {model_name}\n{indented}\n"
            yml_path.write_text(yml_content, encoding="utf-8")
        else:
            yml_path.unlink(missing_ok=True)

    @staticmethod
    def _collect_test_outcomes() -> list[DbtExerciseTestOutcome]:
        # `dbt build --select <model_name>` only ever touches that one model
        # plus tests attached directly to it, so every test result in this
        # run belongs to this submission — no name-matching needed.
        results = artifacts.build_test_results() or []
        return [
            DbtExerciseTestOutcome(name=r.name, passed=r.status == "pass", message=r.message) for r in results
        ]

    def _persist_attempt(
        self,
        user_id: str,
        exercise: Exercise,
        submitted_sql: str,
        status: ExerciseAttemptStatus,
        score: float,
    ) -> ExerciseAttempt:
        had_passed_before = (
            self.db.execute(
                select(ExerciseAttempt).where(
                    ExerciseAttempt.user_id == user_id,
                    ExerciseAttempt.exercise_id == exercise.id,
                    ExerciseAttempt.status == ExerciseAttemptStatus.PASSED,
                )
            ).first()
            is not None
        )

        attempt = ExerciseAttempt(
            user_id=user_id,
            exercise_id=exercise.id,
            status=status,
            score=score,
            submitted_answer=submitted_sql,
            attempted_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()

        if exercise.skill_id:
            self.mastery_service.recalculate(user_id, exercise.skill_id)

        if status == ExerciseAttemptStatus.PASSED and not had_passed_before and exercise.lesson_id:
            progress = self.db.execute(
                select(LessonProgress).where(
                    LessonProgress.user_id == user_id, LessonProgress.lesson_id == exercise.lesson_id
                )
            ).scalar_one_or_none()
            if progress is not None:
                progress.exercises_completed = (progress.exercises_completed or 0) + 1

        self.db.commit()
        self.db.refresh(attempt)
        return attempt
