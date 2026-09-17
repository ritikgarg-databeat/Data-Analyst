from typing import Annotated

from fastapi import APIRouter, Depends

from app.content.loader import load_exercise_file
from app.core.errors import AppError
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_excel_exercise_service, get_exercise_service
from app.schemas.excel import (
    EvaluateWorkbookRequest,
    EvaluateWorkbookResponse,
    ExcelExerciseContent,
    SubmitExcelExerciseRequest,
    SubmitExcelExerciseResponse,
)
from app.services.exercise_service import ExerciseService
from app.services.excel_exercise_service import ExcelExerciseService

router = APIRouter(prefix="/excel", tags=["excel-lab"])


@router.post("/evaluate", response_model=EvaluateWorkbookResponse)
def evaluate_workbook_preview(
    payload: EvaluateWorkbookRequest,
    excel_service: Annotated[ExcelExerciseService, Depends(get_excel_exercise_service)],
) -> EvaluateWorkbookResponse:
    """Live, ungraded formula evaluation for the spreadsheet grid — no
    exercise context, no persistence."""
    return excel_service.evaluate_preview(payload.sheets)


@router.get("/exercises/{slug}", response_model=ExcelExerciseContent)
def get_excel_exercise_content(
    slug: str,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    excel_service: Annotated[ExcelExerciseService, Depends(get_excel_exercise_service)],
) -> ExcelExerciseContent:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "EXCEL":
        raise AppError(f"'{slug}' is not an Excel exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return excel_service.get_exercise_content(content)


@router.post("/exercises/{slug}/submit", response_model=SubmitExcelExerciseResponse)
def submit_excel_exercise(
    slug: str,
    payload: SubmitExcelExerciseRequest,
    user_id: CurrentUserId,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    excel_service: Annotated[ExcelExerciseService, Depends(get_excel_exercise_service)],
) -> SubmitExcelExerciseResponse:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "EXCEL":
        raise AppError(f"'{slug}' is not an Excel exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return excel_service.submit(user_id, exercise, content, payload.submitted_sheets)
