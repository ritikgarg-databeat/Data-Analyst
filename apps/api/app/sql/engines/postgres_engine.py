"""PostgreSQL engine — relational SQL practice (joins, constraints, relational
behavior). Deliberately connects to a SEPARATE practice database/credentials
from the application's own metadata database (`Settings.database_url`) —
user SQL must never be able to reach `domains`, `users`, `lesson_progress`,
etc. If `Settings.sql_lab_postgres_url` isn't configured, this engine is
simply reported unavailable (see `app/sql/registry.py`) rather than falling
back to the app database, which would defeat the isolation entirely.

Every execution runs inside a READ ONLY transaction with a server-enforced
`statement_timeout` — both native Postgres mechanisms, stronger than
DuckDB's thread-interrupt approach, which Postgres doesn't need.
"""

from __future__ import annotations

import time

import psycopg
from psycopg import sql as psycopg_sql

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


class PostgresEngine(SqlEngine):
    name = "postgres"

    def __init__(self, connection_url: str, schema: str = "public") -> None:
        self.connection_url = connection_url
        self.schema = schema

    def _connect(self) -> psycopg.Connection:
        return psycopg.connect(self.connection_url, autocommit=False)

    def list_tables(self) -> list[str]:
        with self._connect() as con, con.cursor() as cur:
            cur.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = %s ORDER BY table_name",
                (self.schema,),
            )
            return [row[0] for row in cur.fetchall()]

    def get_table_schema(self, table_name: str) -> TableSchema:
        with self._connect() as con, con.cursor() as cur:
            cur.execute(
                "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                "WHERE table_schema = %s AND table_name = %s ORDER BY ordinal_position",
                (self.schema, table_name),
            )
            rows = cur.fetchall()
            if not rows:
                raise SqlEngineError(f"Table '{table_name}' was not found in schema '{self.schema}'.")
            columns = [TableColumn(name=r[0], type=r[1], nullable=(r[2] == "YES")) for r in rows]

            count_query = psycopg_sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                psycopg_sql.Identifier(self.schema), psycopg_sql.Identifier(table_name)
            )
            cur.execute(count_query)
            row_count = cur.fetchone()[0]
            return TableSchema(table_name=table_name, columns=columns, row_count=row_count)

    def preview_table(self, table_name: str, *, sample_rows: int = 20) -> TablePreview:
        schema_info = self.get_table_schema(table_name)
        with self._connect() as con, con.cursor() as cur:
            query = psycopg_sql.SQL("SELECT * FROM {}.{} LIMIT %s").format(
                psycopg_sql.Identifier(self.schema), psycopg_sql.Identifier(table_name)
            )
            cur.execute(query, (sample_rows,))
            columns = [ColumnInfo(name=d.name, type=str(d.type_code)) for d in cur.description]
            rows = [[to_json_safe(v) for v in row] for row in cur.fetchall()]

            null_counts: dict[str, int] = {}
            for col in schema_info.columns:
                null_query = psycopg_sql.SQL("SELECT COUNT(*) FROM {}.{} WHERE {} IS NULL").format(
                    psycopg_sql.Identifier(self.schema),
                    psycopg_sql.Identifier(table_name),
                    psycopg_sql.Identifier(col.name),
                )
                cur.execute(null_query)
                null_counts[col.name] = cur.fetchone()[0]

            return TablePreview(
                table_name=table_name,
                columns=columns,
                rows=rows,
                row_count=schema_info.row_count or 0,
                column_count=len(columns),
                sample_row_count=len(rows),
                null_counts=null_counts,
            )

    def execute(self, query: str, *, timeout_seconds: float, row_limit: int) -> SqlExecutionResult:
        try:
            statement = assert_safe_query(query)
        except UnsafeQueryError as exc:
            return SqlExecutionResult(status="error", engine=self.name, error=SqlError(message=str(exc)))

        start = time.monotonic()
        timeout_ms = int(timeout_seconds * 1000)
        try:
            with self._connect() as con:
                con.read_only = True
                with con.cursor() as cur:
                    cur.execute(psycopg_sql.SQL("SET LOCAL statement_timeout = {}").format(timeout_ms))
                    cur.execute(statement)
                    columns = (
                        [ColumnInfo(name=d.name, type=str(d.type_code)) for d in cur.description]
                        if cur.description
                        else []
                    )
                    fetched = cur.fetchmany(row_limit + 1) if cur.description else []
                    truncated = len(fetched) > row_limit
                    rows = [[to_json_safe(v) for v in row] for row in fetched[:row_limit]]
                    con.rollback()  # read-only session — never persist, even implicitly

            return SqlExecutionResult(
                status="success",
                engine=self.name,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                execution_time_ms=int((time.monotonic() - start) * 1000),
                metadata={"schema": self.schema},
            )
        except psycopg.errors.QueryCanceled:
            return SqlExecutionResult(
                status="error",
                engine=self.name,
                execution_time_ms=int((time.monotonic() - start) * 1000),
                error=SqlError(
                    message=f"Query exceeded the {timeout_seconds:.0f}s time limit and was cancelled.",
                    hint="Try narrowing the data scanned (add a WHERE filter) or simplifying the query.",
                ),
            )
        except psycopg.Error as exc:
            return SqlExecutionResult(
                status="error",
                engine=self.name,
                execution_time_ms=int((time.monotonic() - start) * 1000),
                error=SqlError(message=str(exc).strip(), hint=None),
            )
