"""Connects the generic Phase 2 exercise system to real SQL execution.

A SQL exercise's content file (`exercise_type: SQL`) carries `dataset`,
`sql_solution_query`, and optional `sql_hidden_tests` — see
app/content/schema.py. Grading always runs against DuckDB (exercises are
authored/verified against DuckDB + the checked-in CSVs), regardless of
which engine the user happens to be exploring with in the open Playground.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.schema import ExerciseContentFile
from app.core.errors import AppError
from app.models.enums import ExerciseAttemptStatus
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.lesson_progress import LessonProgress
from app.models.sql_lab import SqlExerciseTestResult
from app.schemas.sql import (
    SqlExerciseContent,
    SqlTableSummary,
    SqlTestOutcome,
    SubmitSqlExerciseResponse,
)
from app.services.mastery import MasteryService
from app.sql.converters import to_execution_result_schema
from app.sql.engines.base import SqlExecutionResult
from app.sql.evaluation import (
    HiddenTestSpec,
    TestOutcome,
    compare_full_result,
    run_hidden_row_check,
    score_attempt,
)
from app.sql.service import SqlExecutionService

GRADING_ENGINE = "duckdb"


def _to_outcome_schema(outcome: TestOutcome) -> SqlTestOutcome:
    return SqlTestOutcome(
        name=outcome.name, passed=outcome.passed, is_hidden=outcome.is_hidden, message=outcome.message
    )


class SqlExerciseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.sql_service = SqlExecutionService(db)
        self.mastery_service = MasteryService(db)

    def get_exercise_content(self, exercise: Exercise, content: ExerciseContentFile) -> SqlExerciseContent:
        if not content.dataset:
            raise AppError("This SQL exercise has no dataset configured.")

        all_tables = self.sql_service.list_tables(GRADING_ENGINE, content.dataset)
        wanted = set(content.sql_tables) if content.sql_tables else None
        tables = [t for t in all_tables if wanted is None or t.table_name in wanted]

        return SqlExerciseContent(
            business_context=content.business_context,
            dataset=content.dataset,
            tables=[
                SqlTableSummary(
                    table_name=t.table_name, grain=t.grain, row_count=t.row_count, column_count=t.column_count
                )
                for t in tables
            ],
            starter_query=content.sql_starter_query,
            hint_count=len(content.hints),
        )

    def _run_hidden_tests(
        self, content: ExerciseContentFile, student_result: SqlExecutionResult
    ) -> list[TestOutcome]:
        outcomes: list[TestOutcome] = []
        for spec in content.sql_hidden_tests:
            reference = self.sql_service.execute(
                user_id="__system__",
                engine_name=GRADING_ENGINE,
                database_name=content.dataset,  # type: ignore[arg-type]
                query=spec.query,
                log_history=False,
            )
            outcomes.append(
                run_hidden_row_check(
                    student_result, HiddenTestSpec(spec.name, spec.query, spec.key_columns), reference
                )
            )
        return outcomes

    def submit(
        self, user_id: str, exercise: Exercise, content: ExerciseContentFile, submitted_query: str
    ) -> SubmitSqlExerciseResponse:
        if not content.dataset or not content.sql_solution_query:
            raise AppError("This SQL exercise is not fully configured — missing dataset or solution query.")

        student_result = self.sql_service.execute(
            user_id=user_id,
            engine_name=GRADING_ENGINE,
            database_name=content.dataset,
            query=submitted_query,
            log_history=False,
        )

        if not student_result.is_success:
            error_outcome = TestOutcome(
                name="Query executed successfully",
                passed=False,
                is_hidden=False,
                message=student_result.error.message if student_result.error else "Your query failed to run.",
            )
            attempt = self._persist_attempt(
                user_id,
                exercise,
                submitted_query,
                ExerciseAttemptStatus.FAILED,
                0.0,
                student_result.execution_time_ms,
                [error_outcome],
            )
            return SubmitSqlExerciseResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                score=0.0,
                passed=False,
                test_outcomes=[_to_outcome_schema(error_outcome)],
                result=to_execution_result_schema(student_result),
                explanation=None,
            )

        reference_result = self.sql_service.execute(
            user_id=user_id,
            engine_name=GRADING_ENGINE,
            database_name=content.dataset,
            query=content.sql_solution_query,
            log_history=False,
        )

        correctness_outcome = compare_full_result(
            student_result,
            reference_result,
            ignore_row_order=not content.sql_row_order_matters,
            numeric_tolerance=content.sql_numeric_tolerance,
            student_query=submitted_query,
        )
        hidden_outcomes = (
            self._run_hidden_tests(content, student_result) if correctness_outcome.passed else []
        )

        evaluation = score_attempt(
            correctness_outcome=correctness_outcome,
            hidden_outcomes=hidden_outcomes,
            student_execution_time_ms=student_result.execution_time_ms,
            reference_execution_time_ms=reference_result.execution_time_ms,
        )

        status = ExerciseAttemptStatus.PASSED if evaluation.passed else ExerciseAttemptStatus.FAILED
        all_outcomes = [correctness_outcome, *hidden_outcomes]
        attempt = self._persist_attempt(
            user_id,
            exercise,
            submitted_query,
            status,
            evaluation.score,
            student_result.execution_time_ms,
            all_outcomes,
        )

        return SubmitSqlExerciseResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            score=evaluation.score,
            passed=evaluation.passed,
            test_outcomes=[_to_outcome_schema(o) for o in all_outcomes],
            result=to_execution_result_schema(student_result),
            explanation=content.explanation if evaluation.passed else None,
        )

    def _persist_attempt(
        self,
        user_id: str,
        exercise: Exercise,
        submitted_query: str,
        status: ExerciseAttemptStatus,
        score: float,
        execution_time_ms: int,
        outcomes: list[TestOutcome],
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
            submitted_answer=submitted_query,
            execution_time_ms=execution_time_ms,
            attempted_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()

        for i, outcome in enumerate(outcomes):
            self.db.add(
                SqlExerciseTestResult(
                    attempt_id=attempt.id,
                    test_name=outcome.name,
                    is_hidden=outcome.is_hidden,
                    passed=outcome.passed,
                    message=outcome.message,
                    display_order=i,
                )
            )

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
