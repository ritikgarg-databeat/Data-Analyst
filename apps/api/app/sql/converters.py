"""Converts internal `app.sql.engines.base` dataclasses to their Pydantic
API-response mirrors in `app.schemas.sql` — the single place this mapping
happens, used by both the SQL router and the exercise-grading service."""

from app.schemas.sql import (
    SqlColumnInfo,
    SqlErrorInfo,
    SqlExecutionResultSchema,
    SqlTableColumn,
    SqlTablePreview,
    SqlTableSchema,
)
from app.sql.engines.base import SqlExecutionResult, TablePreview, TableSchema


def to_execution_result_schema(result: SqlExecutionResult) -> SqlExecutionResultSchema:
    return SqlExecutionResultSchema(
        status=result.status,
        engine=result.engine,
        columns=[SqlColumnInfo(name=c.name, type=c.type) for c in result.columns],
        rows=result.rows,
        row_count=result.row_count,
        truncated=result.truncated,
        execution_time_ms=result.execution_time_ms,
        error=SqlErrorInfo(message=result.error.message, hint=result.error.hint) if result.error else None,
        metadata=result.metadata,
    )


def to_table_schema_schema(schema: TableSchema) -> SqlTableSchema:
    return SqlTableSchema(
        table_name=schema.table_name,
        columns=[SqlTableColumn(name=c.name, type=c.type, nullable=c.nullable) for c in schema.columns],
        row_count=schema.row_count,
    )


def to_table_preview_schema(preview: TablePreview) -> SqlTablePreview:
    return SqlTablePreview(
        table_name=preview.table_name,
        columns=[SqlColumnInfo(name=c.name, type=c.type) for c in preview.columns],
        rows=preview.rows,
        row_count=preview.row_count,
        column_count=preview.column_count,
        sample_row_count=preview.sample_row_count,
        null_counts=preview.null_counts,
    )
