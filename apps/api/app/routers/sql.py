from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.content.loader import load_exercise_file
from app.core.errors import AppError
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import (
    get_exercise_service,
    get_sql_execution_service,
    get_sql_exercise_service,
    get_sql_workspace_service,
)
from app.schemas.sql import (
    CreateSqlSavedQueryRequest,
    CreateSqlWorkspaceRequest,
    ExecuteSqlRequest,
    SqlDatabaseInfo,
    SqlEngineInfo,
    SqlExecutionResultSchema,
    SqlExerciseContent,
    SqlQueryHistoryItem,
    SqlSavedQuerySchema,
    SqlTablePreview,
    SqlTableSchema,
    SqlTableSummary,
    SqlWorkspaceSchema,
    SubmitSqlExerciseRequest,
    SubmitSqlExerciseResponse,
    UpdateSqlSavedQueryRequest,
)
from app.services.exercise_service import ExerciseService
from app.services.sql_exercise_service import SqlExerciseService
from app.services.sql_workspace_service import SqlWorkspaceService
from app.sql.converters import to_execution_result_schema, to_table_preview_schema, to_table_schema_schema
from app.sql.service import SqlExecutionService

router = APIRouter(prefix="/sql", tags=["sql"])


@router.get("/engines", response_model=list[SqlEngineInfo])
def list_engines(
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
) -> list[SqlEngineInfo]:
    return [
        SqlEngineInfo(name=e.name, label=e.label, is_available=e.is_available, reason=e.reason)
        for e in service.list_engines()
    ]


@router.get("/databases", response_model=list[SqlDatabaseInfo])
def list_databases(
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
) -> list[SqlDatabaseInfo]:
    return [
        SqlDatabaseInfo(
            name=d.name, label=d.label, engine=d.engine, description=d.description, table_count=d.table_count
        )
        for d in service.list_databases()
    ]


@router.get("/databases/{database}/tables", response_model=list[SqlTableSummary])
def list_tables(
    database: str,
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
    engine: str = Query(default="duckdb"),
) -> list[SqlTableSummary]:
    return [
        SqlTableSummary(
            table_name=t.table_name, grain=t.grain, row_count=t.row_count, column_count=t.column_count
        )
        for t in service.list_tables(engine, database)
    ]


@router.get("/databases/{database}/tables/{table}/schema", response_model=SqlTableSchema)
def get_table_schema(
    database: str,
    table: str,
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
    engine: str = Query(default="duckdb"),
) -> SqlTableSchema:
    return to_table_schema_schema(service.get_table_schema(engine, database, table))


@router.get("/databases/{database}/tables/{table}/preview", response_model=SqlTablePreview)
def preview_table(
    database: str,
    table: str,
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
    engine: str = Query(default="duckdb"),
) -> SqlTablePreview:
    return to_table_preview_schema(service.preview_table(engine, database, table))


@router.post("/execute", response_model=SqlExecutionResultSchema)
def execute_query(
    payload: ExecuteSqlRequest,
    user_id: CurrentUserId,
    service: Annotated[SqlExecutionService, Depends(get_sql_execution_service)],
) -> SqlExecutionResultSchema:
    result = service.execute(
        user_id=user_id, engine_name=payload.engine, database_name=payload.database, query=payload.query
    )
    return to_execution_result_schema(result)


@router.get("/history", response_model=list[SqlQueryHistoryItem])
def list_history(
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
    status: str | None = Query(default=None),
    engine: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[SqlQueryHistoryItem]:
    return service.list_history(user_id, status=status, engine=engine, limit=limit)


@router.delete("/history/{history_id}", status_code=204)
def delete_history_entry(
    history_id: str,
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
) -> None:
    service.delete_history_entry(user_id, history_id)


@router.get("/workspaces", response_model=list[SqlWorkspaceSchema])
def list_workspaces(
    user_id: CurrentUserId, service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)]
) -> list[SqlWorkspaceSchema]:
    return service.list_workspaces(user_id)


@router.post("/workspaces", response_model=SqlWorkspaceSchema, status_code=201)
def create_workspace(
    payload: CreateSqlWorkspaceRequest,
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
) -> SqlWorkspaceSchema:
    return service.create_workspace(user_id, payload)


@router.get("/saved", response_model=list[SqlSavedQuerySchema])
def list_saved_queries(
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
    workspace_id: str | None = Query(default=None),
) -> list[SqlSavedQuerySchema]:
    return service.list_saved_queries(user_id, workspace_id)


@router.post("/saved", response_model=SqlSavedQuerySchema, status_code=201)
def create_saved_query(
    payload: CreateSqlSavedQueryRequest,
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
) -> SqlSavedQuerySchema:
    return service.create_saved_query(user_id, payload)


@router.patch("/saved/{query_id}", response_model=SqlSavedQuerySchema)
def update_saved_query(
    query_id: str,
    payload: UpdateSqlSavedQueryRequest,
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
) -> SqlSavedQuerySchema:
    return service.update_saved_query(user_id, query_id, payload)


@router.delete("/saved/{query_id}", status_code=204)
def delete_saved_query(
    query_id: str,
    user_id: CurrentUserId,
    service: Annotated[SqlWorkspaceService, Depends(get_sql_workspace_service)],
) -> None:
    service.delete_saved_query(user_id, query_id)


@router.get("/exercises/{slug}", response_model=SqlExerciseContent)
def get_sql_exercise_content(
    slug: str,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    sql_exercise_service: Annotated[SqlExerciseService, Depends(get_sql_exercise_service)],
) -> SqlExerciseContent:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "SQL":
        raise AppError(f"'{slug}' is not a SQL exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return sql_exercise_service.get_exercise_content(exercise, content)


@router.post("/exercises/{slug}/submit", response_model=SubmitSqlExerciseResponse)
def submit_sql_exercise(
    slug: str,
    payload: SubmitSqlExerciseRequest,
    user_id: CurrentUserId,
    exercise_service: Annotated[ExerciseService, Depends(get_exercise_service)],
    sql_exercise_service: Annotated[SqlExerciseService, Depends(get_sql_exercise_service)],
) -> SubmitSqlExerciseResponse:
    exercise = exercise_service.get_model_by_slug(slug)
    if exercise.exercise_type != "SQL":
        raise AppError(f"'{slug}' is not a SQL exercise.")
    content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
    return sql_exercise_service.submit(user_id, exercise, content, payload.submitted_query)
