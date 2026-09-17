"""Converts `app.python_lab.base` dataclasses to their Pydantic API mirrors
in `app.schemas.python_lab` — the single place this mapping happens, shared
by the router and the exercise-grading service, mirroring
app/sql/converters.py."""

from app.python_lab.base import (
    ChartOutput,
    DataFrameSummary,
    PythonError,
    PythonExecutionResult,
    PythonVariable,
)
from app.schemas.python_lab import (
    ChartOutputSchema,
    DataFrameColumnSchema,
    DataFrameSummarySchema,
    PythonErrorSchema,
    PythonExecutionResultSchema,
    PythonVariableSchema,
)


def to_dataframe_summary_schema(summary: DataFrameSummary | None) -> DataFrameSummarySchema | None:
    if summary is None:
        return None
    return DataFrameSummarySchema(
        row_count=summary.row_count,
        column_count=summary.column_count,
        columns=[DataFrameColumnSchema(**vars(c)) for c in summary.columns],
        preview_rows=summary.preview_rows,
        preview_row_count=summary.preview_row_count,
        truncated=summary.truncated,
        memory_usage_bytes=summary.memory_usage_bytes,
    )


def to_variable_schema(variable: PythonVariable | None) -> PythonVariableSchema | None:
    if variable is None:
        return None
    return PythonVariableSchema(
        name=variable.name,
        type_name=variable.type_name,
        preview=variable.preview,
        dataframe=to_dataframe_summary_schema(variable.dataframe),
        shape=variable.shape,
        value=variable.value,
    )


def to_error_schema(error: PythonError | None) -> PythonErrorSchema | None:
    if error is None:
        return None
    return PythonErrorSchema(
        error_type=error.error_type,
        message=error.message,
        line=error.line,
        traceback_text=error.traceback_text,
        hint=error.hint,
    )


def to_chart_schema(chart: ChartOutput) -> ChartOutputSchema:
    return ChartOutputSchema(kind=chart.kind, format=chart.format, data=chart.data, title=chart.title)


def to_execution_result_schema(result: PythonExecutionResult) -> PythonExecutionResultSchema:
    return PythonExecutionResultSchema(
        status=result.status,
        stdout=result.stdout,
        stdout_truncated=result.stdout_truncated,
        display_value=to_variable_schema(result.display_value),
        variables=[to_variable_schema(v) for v in result.variables],
        charts=[to_chart_schema(c) for c in result.charts],
        error=to_error_schema(result.error),
        execution_time_ms=result.execution_time_ms,
    )
