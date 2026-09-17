from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMSchema


class DataFrameColumnSchema(BaseModel):
    name: str
    dtype: str
    null_count: int
    unique_count: int


class DataFrameSummarySchema(BaseModel):
    row_count: int
    column_count: int
    columns: list[DataFrameColumnSchema] = []
    preview_rows: list[list[object]] = []
    preview_row_count: int = 0
    truncated: bool = False
    memory_usage_bytes: int | None = None


class PythonVariableSchema(BaseModel):
    name: str
    type_name: str
    preview: str
    dataframe: DataFrameSummarySchema | None = None
    shape: list[int] | None = None
    value: object = None


class ChartOutputSchema(BaseModel):
    kind: str
    format: str
    data: str
    title: str | None = None


class PythonErrorSchema(BaseModel):
    error_type: str
    message: str
    line: int | None = None
    traceback_text: str = ""
    hint: str | None = None


class PythonExecutionResultSchema(BaseModel):
    status: str
    stdout: str = ""
    stdout_truncated: bool = False
    display_value: PythonVariableSchema | None = None
    variables: list[PythonVariableSchema] = []
    charts: list[ChartOutputSchema] = []
    error: PythonErrorSchema | None = None
    execution_time_ms: int = 0


# --- Runtimes ------------------------------------------------------------


class PythonRuntimeSchema(ORMSchema):
    id: str
    status: str
    workspace_id: str | None = None
    timeout_seconds: int
    error_message: str | None = None
    created_at: datetime
    last_used_at: datetime


class ExecutePythonRequest(BaseModel):
    code: str
    workspace_id: str | None = None


class PythonAvailabilitySchema(BaseModel):
    available: bool
    reason: str | None = None


# --- Datasets --------------------------------------------------------------


class PythonDatasetFileSchema(BaseModel):
    dataset_slug: str
    dataset_name: str
    label: str
    container_path: str
    file_format: str
    grain: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    suggested_code: str


# --- History -----------------------------------------------------------


class PythonHistoryItemSchema(ORMSchema):
    id: str
    workspace_id: str | None = None
    code: str
    status: str
    error_message: str | None = None
    execution_time_ms: int | None = None
    executed_at: datetime


# --- Workspaces & cells ----------------------------------------------------


class PythonCellSchema(ORMSchema):
    id: str
    workspace_id: str
    display_order: int
    code: str
    last_result: PythonExecutionResultSchema | None = None
    last_executed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PythonWorkspaceSchema(ORMSchema):
    id: str
    name: str
    selected_dataset: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CreatePythonWorkspaceRequest(BaseModel):
    name: str
    selected_dataset: str | None = None
    starter_code: str | None = None


class UpdatePythonWorkspaceRequest(BaseModel):
    name: str | None = None
    selected_dataset: str | None = None
    notes: str | None = None


class CreatePythonCellRequest(BaseModel):
    code: str = ""


class UpdatePythonCellRequest(BaseModel):
    code: str | None = None
    display_order: int | None = None


class RecordCellResultRequest(BaseModel):
    result: PythonExecutionResultSchema


# --- Python exercises --------------------------------------------------


class PythonExerciseContent(BaseModel):
    """Never includes python_solution_code or python_hidden_tests."""

    business_context: str | None = None
    dataset: str | None = None
    dataset_files: list[PythonDatasetFileSchema] = []
    starter_code: str | None = None
    result_variable: str
    hint_count: int


class SubmitPythonExerciseRequest(BaseModel):
    submitted_code: str


class PythonTestOutcomeSchema(BaseModel):
    name: str
    passed: bool
    is_hidden: bool
    message: str


class SubmitPythonExerciseResponse(BaseModel):
    attempt_id: str
    status: str
    score: float | None = None
    passed: bool
    test_outcomes: list[PythonTestOutcomeSchema]
    result: PythonExecutionResultSchema
    explanation: str | None = None
