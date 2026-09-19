"""Connects the generic Phase 2 exercise system to real Python execution —
mirrors app/services/sql_exercise_service.py's shape exactly.

A PYTHON exercise's content file carries `dataset`, `python_solution_code`,
and optional `python_hidden_tests` (see app/content/schema.py). Grading runs
the student's code and the reference solution in TWO separate, freshly
created, ephemeral sandbox runtimes (never the student's own interactive
workspace runtime) — this keeps grading fair (the reference can't see
anything the student defined) and keeps the student's live session
untouched by grading side effects. Both runtimes are destroyed immediately
after grading; only the resulting `ExerciseAttempt` is persisted.
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
from app.models.python_lab import PythonExerciseTestResult
from app.python_lab.base import PythonExecutionResult
from app.python_lab.converters import to_execution_result_schema
from app.python_lab.evaluation import TestOutcome, compare_result_variable, hidden_test_outcome, score_attempt
from app.python_lab.service import PythonExecutionService
from app.schemas.python_lab import (
    PythonDatasetFileSchema,
    PythonExerciseContent,
    PythonTestOutcomeSchema,
    SubmitPythonExerciseResponse,
)
from app.services.mastery import MasteryService


def _to_outcome_schema(outcome: TestOutcome) -> PythonTestOutcomeSchema:
    return PythonTestOutcomeSchema(
        name=outcome.name, passed=outcome.passed, is_hidden=outcome.is_hidden, message=outcome.message
    )


class PythonExerciseService:
    def __init__(self, db: Session, user_id: str | None = None) -> None:
        self.db = db
        self.execution_service = PythonExecutionService(db, user_id=user_id)
        self.mastery_service = MasteryService(db)

    def get_exercise_content(self, exercise: Exercise, content: ExerciseContentFile) -> PythonExerciseContent:
        if not content.dataset:
            raise AppError("This Python exercise has no dataset configured.")

        all_files = self.execution_service.list_datasets()
        wanted = set(content.python_datasets) if content.python_datasets else None
        dataset_files = [
            f
            for f in all_files
            if f.dataset_slug == content.dataset and (wanted is None or f.label.split(".")[0] in wanted)
        ]

        return PythonExerciseContent(
            business_context=content.business_context,
            dataset=content.dataset,
            dataset_files=[PythonDatasetFileSchema(**vars(f)) for f in dataset_files],
            starter_code=content.python_starter_code,
            result_variable=content.python_result_variable,
            hint_count=len(content.hints),
        )

    def _dataset_setup_code(self, content: ExerciseContentFile) -> str:
        all_files = self.execution_service.list_datasets()
        wanted = set(content.python_datasets) if content.python_datasets else None
        lines = ["import pandas as pd", "import numpy as np"]
        for f in all_files:
            if f.dataset_slug != content.dataset:
                continue
            var_name = f.label.split(".")[0]
            if wanted is not None and var_name not in wanted:
                continue
            lines.append(f.suggested_code)
        return "\n".join(lines)

    def _run_hidden_tests(
        self, runtime_id: str, user_id: str, content: ExerciseContentFile
    ) -> list[TestOutcome]:
        outcomes: list[TestOutcome] = []
        for spec in content.python_hidden_tests:
            result = self.execution_service.execute(runtime_id, user_id, spec.code, log_history=False)
            outcomes.append(hidden_test_outcome(spec.name, result.status, result.error))
        return outcomes

    def submit(
        self, user_id: str, exercise: Exercise, content: ExerciseContentFile, submitted_code: str
    ) -> SubmitPythonExerciseResponse:
        if not content.dataset or not content.python_solution_code:
            raise AppError("This Python exercise is not fully configured — missing dataset or solution code.")

        setup_code = self._dataset_setup_code(content)

        student_runtime = self.execution_service.create_runtime(user_id, count_toward_limit=False)
        try:
            self.execution_service.execute(student_runtime.id, user_id, setup_code, log_history=False)
            student_result = self.execution_service.execute(
                student_runtime.id, user_id, submitted_code, log_history=False
            )

            if not student_result.is_success:
                error_outcome = TestOutcome(
                    name="Code executed successfully",
                    passed=False,
                    is_hidden=False,
                    message=student_result.error.message
                    if student_result.error
                    else "Your code failed to run.",
                )
                attempt = self._persist_attempt(
                    user_id,
                    exercise,
                    submitted_code,
                    ExerciseAttemptStatus.FAILED,
                    0.0,
                    student_result.execution_time_ms,
                    [error_outcome],
                )
                return SubmitPythonExerciseResponse(
                    attempt_id=attempt.id,
                    status=attempt.status,
                    score=0.0,
                    passed=False,
                    test_outcomes=[_to_outcome_schema(error_outcome)],
                    result=to_execution_result_schema(student_result),
                    explanation=None,
                )

            student_var = next(
                (v for v in student_result.variables if v.name == content.python_result_variable), None
            )
            reference_result = self._run_reference_solution(user_id, content, setup_code)
            reference_var = next(
                (v for v in reference_result.variables if v.name == content.python_result_variable), None
            )

            correctness_outcome = compare_result_variable(
                student_var,
                reference_var,
                result_variable=content.python_result_variable,
                numeric_tolerance=content.python_numeric_tolerance,
                row_order_matters=content.python_row_order_matters,
            )
            hidden_outcomes = (
                self._run_hidden_tests(student_runtime.id, user_id, content)
                if correctness_outcome.passed
                else []
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
                submitted_code,
                status,
                evaluation.score,
                student_result.execution_time_ms,
                all_outcomes,
            )

            return SubmitPythonExerciseResponse(
                attempt_id=attempt.id,
                status=attempt.status,
                score=evaluation.score,
                passed=evaluation.passed,
                test_outcomes=[_to_outcome_schema(o) for o in all_outcomes],
                result=to_execution_result_schema(student_result),
                explanation=content.explanation if evaluation.passed else None,
            )
        finally:
            self.execution_service.destroy_runtime(student_runtime.id, user_id)

    def _run_reference_solution(
        self, user_id: str, content: ExerciseContentFile, setup_code: str
    ) -> PythonExecutionResult:
        reference_runtime = self.execution_service.create_runtime(user_id, count_toward_limit=False)
        try:
            self.execution_service.execute(reference_runtime.id, user_id, setup_code, log_history=False)
            return self.execution_service.execute(
                reference_runtime.id,
                user_id,
                content.python_solution_code,
                log_history=False,  # type: ignore[arg-type]
            )
        finally:
            self.execution_service.destroy_runtime(reference_runtime.id, user_id)

    def _persist_attempt(
        self,
        user_id: str,
        exercise: Exercise,
        submitted_code: str,
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
            submitted_answer=submitted_code,
            execution_time_ms=execution_time_ms,
            attempted_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()

        for i, outcome in enumerate(outcomes):
            self.db.add(
                PythonExerciseTestResult(
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
