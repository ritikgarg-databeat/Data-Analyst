from datetime import datetime

from pydantic import BaseModel

from app.schemas.common import ORMSchema


class SqlEngineInfo(BaseModel):
    name: str
    label: str
    is_available: bool
    reason: str | None = None


class SqlDatabaseInfo(BaseModel):
    name: str
    label: str
    engine: str
    description: str | None = None
    table_count: int = 0


class SqlTableSummary(BaseModel):
    table_name: str
    grain: str | None = None
    row_count: int | None = None
    column_count: int | None = None


class SqlColumnInfo(BaseModel):
    name: str
    type: str


class SqlTableColumn(BaseModel):
    name: str
    type: str
    nullable: bool = True


class SqlTableSchema(BaseModel):
    table_name: str
    columns: list[SqlTableColumn]
    row_count: int | None = None


class SqlTablePreview(BaseModel):
    table_name: str
    columns: list[SqlColumnInfo]
    rows: list[list[object]]
    row_count: int
    column_count: int
    sample_row_count: int
    null_counts: dict[str, int] = {}


class SqlErrorInfo(BaseModel):
    message: str
    hint: str | None = None


class SqlExecutionResultSchema(BaseModel):
    status: str
    engine: str
    columns: list[SqlColumnInfo] = []
    rows: list[list[object]] = []
    row_count: int = 0
    truncated: bool = False
    execution_time_ms: int = 0
    error: SqlErrorInfo | None = None
    metadata: dict[str, object] = {}


class ExecuteSqlRequest(BaseModel):
    engine: str
    database: str
    query: str


class SqlQueryHistoryItem(ORMSchema):
    id: str
    engine: str
    database: str
    query: str
    status: str
    row_count: int | None = None
    execution_time_ms: int | None = None
    error_message: str | None = None
    executed_at: datetime


class SqlWorkspaceSchema(ORMSchema):
    id: str
    name: str
    engine: str
    database: str
    created_at: datetime
    updated_at: datetime


class CreateSqlWorkspaceRequest(BaseModel):
    name: str
    engine: str = "duckdb"
    database: str


class SqlSavedQuerySchema(ORMSchema):
    id: str
    workspace_id: str | None = None
    title: str
    description: str | None = None
    query: str
    engine: str
    database: str
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime


class CreateSqlSavedQueryRequest(BaseModel):
    title: str
    description: str | None = None
    query: str
    engine: str
    database: str
    workspace_id: str | None = None
    tags: list[str] = []


class UpdateSqlSavedQueryRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    query: str | None = None
    workspace_id: str | None = None
    tags: list[str] | None = None


# --- SQL exercises ---


class SqlExerciseContent(BaseModel):
    """SQL-specific exercise content — schema/business context/starter query.
    Never includes sql_solution_query or sql_hidden_tests."""

    business_context: str | None = None
    dataset: str
    tables: list[SqlTableSummary]
    starter_query: str | None = None
    hint_count: int


class SubmitSqlExerciseRequest(BaseModel):
    submitted_query: str


class SqlTestOutcome(BaseModel):
    name: str
    passed: bool
    is_hidden: bool
    message: str


class SubmitSqlExerciseResponse(BaseModel):
    attempt_id: str
    status: str
    score: float | None = None
    passed: bool
    test_outcomes: list[SqlTestOutcome]
    result: SqlExecutionResultSchema
    explanation: str | None = None
