"""Connects the generic Phase 2 exercise system to real Excel formula
evaluation — mirrors app/services/sql_exercise_service.py's shape exactly.

An EXCEL exercise's content file carries `excel_starter_sheets`,
`excel_solution_sheets`, and `excel_check_cells` (see app/content/schema.py).
Grading always evaluates both the student's submitted workbook and the
authored solution workbook for real (app/excel_lab/formula_engine.py), then
compares only the authored check cells — never formula text.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.schema import ExerciseContentFile
from app.excel_lab.evaluation import TestOutcome, grade_excel_submission
from app.excel_lab.formula_engine import evaluate_workbook
from app.models.enums import ExerciseAttemptStatus
from app.models.excel_lab import ExcelExerciseTestResult
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.lesson_progress import LessonProgress
from app.schemas.excel import (
    EvaluatedSheetSchema,
    EvaluateWorkbookResponse,
    ExcelExerciseContent,
    ExcelSheetSchema,
    ExcelTestOutcomeSchema,
    SubmitExcelExerciseResponse,
)
from app.services.mastery import MasteryService


def _to_outcome_schema(outcome: TestOutcome) -> ExcelTestOutcomeSchema:
    return ExcelTestOutcomeSchema(name=outcome.name, passed=outcome.passed, is_hidden=outcome.is_hidden, message=outcome.message)


def _to_workbook(sheets: list[ExcelSheetSchema]) -> dict[str, dict[str, str]]:
    return {s.name: s.cells for s in sheets}


def _to_evaluated_schemas(evaluated: dict[str, dict[str, object]]) -> list[EvaluatedSheetSchema]:
    return [EvaluatedSheetSchema(name=name, cells=cells) for name, cells in evaluated.items()]  # type: ignore[arg-type]


class ExcelExerciseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.mastery_service = MasteryService(db)

    def get_exercise_content(self, content: ExerciseContentFile) -> ExcelExerciseContent:
        return ExcelExerciseContent(
            business_context=content.business_context,
            starter_sheets=[ExcelSheetSchema(name=s.name, cells=s.cells) for s in content.excel_starter_sheets],
            check_cells=content.excel_check_cells,
            hint_count=len(content.hints),
        )

    def evaluate_preview(self, sheets: list[ExcelSheetSchema]) -> EvaluateWorkbookResponse:
        """Live, ungraded formula evaluation — powers the spreadsheet grid
        recomputing displayed values as the learner types, with no
        persistence and no relation to any specific exercise."""
        evaluated = evaluate_workbook(_to_workbook(sheets))
        return EvaluateWorkbookResponse(sheets=_to_evaluated_schemas(evaluated))

    def submit(
        self,
        user_id: str,
        exercise: Exercise,
        content: ExerciseContentFile,
        submitted_sheets: list[ExcelSheetSchema],
    ) -> SubmitExcelExerciseResponse:
        student_workbook = _to_workbook(submitted_sheets)
        solution_workbook = _to_workbook(
            [ExcelSheetSchema(name=s.name, cells=s.cells) for s in content.excel_solution_sheets]
        )
        evaluation = grade_excel_submission(student_workbook, solution_workbook, content.excel_check_cells)

        status = ExerciseAttemptStatus.PASSED if evaluation.passed else ExerciseAttemptStatus.FAILED
        attempt = self._persist_attempt(user_id, exercise, submitted_sheets, status, evaluation.score, evaluation.test_outcomes)

        evaluated_student = evaluate_workbook(student_workbook)
        return SubmitExcelExerciseResponse(
            attempt_id=attempt.id,
            status=attempt.status,
            score=evaluation.score,
            passed=evaluation.passed,
            test_outcomes=[_to_outcome_schema(o) for o in evaluation.test_outcomes],
            evaluated_sheets=_to_evaluated_schemas(evaluated_student),
            explanation=content.explanation if evaluation.passed else None,
        )

    def _persist_attempt(
        self,
        user_id: str,
        exercise: Exercise,
        submitted_sheets: list[ExcelSheetSchema],
        status: ExerciseAttemptStatus,
        score: float,
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

        submitted_json = json.dumps([s.model_dump() for s in submitted_sheets])
        attempt = ExerciseAttempt(
            user_id=user_id,
            exercise_id=exercise.id,
            status=status,
            score=score,
            submitted_answer=submitted_json,
            attempted_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()

        for i, outcome in enumerate(outcomes):
            self.db.add(
                ExcelExerciseTestResult(
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
