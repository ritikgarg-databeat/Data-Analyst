"""DuckDB engine — the default, always-available analytical SQL engine.

Each instance is scoped to one logical "database" (e.g. "ecommerce"): an
in-memory DuckDB connection with one VIEW per registered table, pointing
directly at the source CSV/Parquet file (data is never copied into DuckDB's
own storage — "prefer querying source files directly"). A fresh connection
is created per execution rather than pooled: DuckDB connections aren't safe
to share across concurrent requests, this is a single-user local app where
the overhead is negligible, and it guarantees no state leaks between runs.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from pathlib import Path

import duckdb

from app.sql.engines.base import (
    ColumnInfo,
    SqlEngine,
    SqlEngineError,
    SqlError,
    SqlExecutionResult,
    TableColumn,
    TablePreview,
    TableSchema,
    to_json_safe,
)
from app.sql.safety import UnsafeQueryError, assert_safe_query

_READ_FUNCTION_BY_FORMAT = {
    "csv": "read_csv_auto",
    "parquet": "read_parquet",
    "json": "read_json_auto",
}


@dataclass
class DuckDbTableSource:
    table_name: str
    file_path: str  # absolute path to the CSV/Parquet/JSON source file
    file_format: str  # "csv" | "parquet" | "json"


class DuckDBEngine(SqlEngine):
    name = "duckdb"

    def __init__(self, database_name: str, tables: list[DuckDbTableSource]) -> None:
        self.database_name = database_name
        self.tables = {t.table_name: t for t in tables}

    def _connect(self) -> duckdb.DuckDBPyConnection:
        con = duckdb.connect(database=":memory:")
        for table in self.tables.values():
            read_fn = _READ_FUNCTION_BY_FORMAT.get(table.file_format)
            if read_fn is None:
                continue
            path = Path(table.file_path).as_posix()
            # A real TABLE (materialized now, while filesystem access is still
            # enabled), not a VIEW — a VIEW re-reads its source file lazily on
            # every query, which would still need filesystem access AFTER the
            # enable_external_access=False below, breaking every subsequent
            # query. Perf is unaffected: a fresh connection is opened per
            # execution regardless (see module docstring), so the CSV/Parquet
            # read happens exactly once either way.
            con.execute(f"CREATE TABLE {table.table_name} AS SELECT * FROM {read_fn}('{path}')")
        # Disable ALL filesystem/network access for the untrusted query that
        # runs on this connection from here on — closes a real, live-confirmed
        # vulnerability where a plain SELECT calling a file-reading table
        # function (`read_text`, `read_csv_auto`, `glob`, ...) could read (or,
        # combined with an EXPLAIN ANALYZE-wrapped COPY, write/overwrite) any
        # file the API process can access. The keyword denylist in
        # app/sql/safety.py can never catch this class of issue on its own,
        # since it never inspects function calls inside an otherwise-ordinary
        # SELECT. Set AFTER materializing tables above, since disabling it
        # first would also block the legitimate CSV/Parquet reads needed to
        # populate them.
        con.execute("SET enable_external_access=false")
        return con

    def list_tables(self) -> list[str]:
        return sorted(self.tables.keys())

    def get_table_schema(self, table_name: str) -> TableSchema:
        if table_name not in self.tables:
            raise SqlEngineError(f"Table '{table_name}' is not part of database '{self.database_name}'.")
        con = self._connect()
        try:
            rows = con.execute(f"DESCRIBE {table_name}").fetchall()
            columns = [TableColumn(name=r[0], type=r[1], nullable=(r[2] == "YES")) for r in rows]
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            return TableSchema(table_name=table_name, columns=columns, row_count=row_count)
        finally:
            con.close()

    def preview_table(self, table_name: str, *, sample_rows: int = 20) -> TablePreview:
        if table_name not in self.tables:
            raise SqlEngineError(f"Table '{table_name}' is not part of database '{self.database_name}'.")
        con = self._connect()
        try:
            row_count = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
            cursor = con.execute(f"SELECT * FROM {table_name} LIMIT {sample_rows}")
            columns = [ColumnInfo(name=d[0], type=str(d[1])) for d in cursor.description]
            rows = [[to_json_safe(v) for v in row] for row in cursor.fetchall()]

            null_counts: dict[str, int] = {}
            for col in columns:
                null_count = con.execute(
                    f'SELECT COUNT(*) FROM {table_name} WHERE "{col.name}" IS NULL'
                ).fetchone()[0]
                null_counts[col.name] = null_count

            return TablePreview(
                table_name=table_name,
                columns=columns,
                rows=rows,
                row_count=row_count,
                column_count=len(columns),
                sample_row_count=len(rows),
                null_counts=null_counts,
            )
        finally:
            con.close()

    def execute(self, query: str, *, timeout_seconds: float, row_limit: int) -> SqlExecutionResult:
        try:
            statement = assert_safe_query(query)
        except UnsafeQueryError as exc:
            return SqlExecutionResult(status="error", engine=self.name, error=SqlError(message=str(exc)))

        con = self._connect()
        start = time.monotonic()

        def _run() -> duckdb.DuckDBPyConnection:
            return con.execute(statement)

        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run)
            try:
                future.result(timeout=timeout_seconds)
            except FutureTimeoutError:
                con.interrupt()
                con.close()
                return SqlExecutionResult(
                    status="error",
                    engine=self.name,
                    execution_time_ms=int((time.monotonic() - start) * 1000),
                    error=SqlError(
                        message=f"Query exceeded the {timeout_seconds:.0f}s time limit and was cancelled.",
                        hint="Try narrowing the data scanned (add a WHERE filter) or simplifying the query.",
                    ),
                )
            except duckdb.Error as exc:
                con.close()
                return SqlExecutionResult(
                    status="error",
                    engine=self.name,
                    execution_time_ms=int((time.monotonic() - start) * 1000),
                    error=SqlError(message=str(exc), hint=_derive_hint(str(exc))),
                )

        try:
            cursor_description = con.description or []
            columns = [ColumnInfo(name=d[0], type=str(d[1])) for d in cursor_description]
            fetched = con.fetchmany(row_limit + 1)
            truncated = len(fetched) > row_limit
            rows = [[to_json_safe(v) for v in row] for row in fetched[:row_limit]]
            execution_time_ms = int((time.monotonic() - start) * 1000)
            return SqlExecutionResult(
                status="success",
                engine=self.name,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                execution_time_ms=execution_time_ms,
                metadata={"database": self.database_name},
            )
        finally:
            con.close()


def _derive_hint(error_message: str) -> str | None:
    lowered = error_message.lower()
    if "does not exist" in lowered and "column" in lowered:
        return "Check the column name for typos, or expand the schema explorer to see valid column names."
    if "does not exist" in lowered and ("table" in lowered or "catalog" in lowered):
        return "Check the table name for typos, or expand the schema explorer to see available tables."
    if "syntax error" in lowered:
        return "Check for a missing comma, parenthesis, or keyword near the reported location."
    if "ambiguous" in lowered:
        return "Two tables in your JOIN share a column name — qualify it with the table name or an alias."
    if "group by" in lowered:
        return "Every non-aggregated column in SELECT must also appear in GROUP BY."
    return None
