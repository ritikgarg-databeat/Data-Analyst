from pydantic import BaseModel

from app.models.enums import ExerciseAttemptStatus


class ExcelSheetSchema(BaseModel):
    name: str
    cells: dict[str, str] = {}


class ExcelExerciseContent(BaseModel):
    business_context: str | None = None
    starter_sheets: list[ExcelSheetSchema] = []
    check_cells: list[str] = []
    hint_count: int = 0


class EvaluateWorkbookRequest(BaseModel):
    """Live formula-evaluation preview (no grading, no persistence) — powers
    the spreadsheet grid recomputing displayed values as the learner types."""

    sheets: list[ExcelSheetSchema]


class EvaluatedSheetSchema(BaseModel):
    name: str
    cells: dict[str, float | str | bool | None] = {}


class EvaluateWorkbookResponse(BaseModel):
    sheets: list[EvaluatedSheetSchema]


class ExcelTestOutcomeSchema(BaseModel):
    name: str
    passed: bool
    is_hidden: bool
    message: str


class SubmitExcelExerciseRequest(BaseModel):
    submitted_sheets: list[ExcelSheetSchema]


class SubmitExcelExerciseResponse(BaseModel):
    attempt_id: str
    status: ExerciseAttemptStatus
    score: float
    passed: bool
    test_outcomes: list[ExcelTestOutcomeSchema]
    evaluated_sheets: list[EvaluatedSheetSchema]
    explanation: str | None = None
