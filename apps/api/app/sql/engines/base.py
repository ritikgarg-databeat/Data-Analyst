"""Engine-agnostic types + the SqlEngine interface every engine implements.

Kept as plain dataclasses (not Pydantic) deliberately — this is the internal
execution layer, not the API contract. `app/schemas/sql.py` maps these onto
the Pydantic response models at the router boundary, the same separation
`app/models` (ORM) vs `app/schemas` (API) already uses elsewhere.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any


def to_json_safe(value: Any) -> Any:
    """Coerces a raw DB value into something `json.dumps`/Pydantic can serialize."""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return value


@dataclass
class ColumnInfo:
    name: str
    type: str  # engine-reported type name, e.g. "BIGINT", "VARCHAR", "integer"


@dataclass
class SqlError:
    message: str
    """The raw, unmodified error message from the database engine — never
    fabricated. `hint` (below) is Data Lab's own derived,
    best-effort guidance and is None when we don't have anything useful to add."""
    hint: str | None = None


@dataclass
class SqlExecutionResult:
    status: str  # "success" | "error"
    engine: str
    columns: list[ColumnInfo] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    execution_time_ms: int = 0
    error: SqlError | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        return self.status == "success"


@dataclass
class TableColumn:
    name: str
    type: str
    nullable: bool = True


@dataclass
class TableSchema:
    table_name: str
    columns: list[TableColumn]
    row_count: int | None = None


@dataclass
class TablePreview:
    table_name: str
    columns: list[ColumnInfo]
    rows: list[list[Any]]
    row_count: int
    column_count: int
    sample_row_count: int
    null_counts: dict[str, int] = field(default_factory=dict)


class SqlEngineError(Exception):
    """Raised for engine-level failures that aren't a query syntax/runtime error
    (e.g. the requested database/table doesn't exist, connection failed)."""


class SqlEngine(ABC):
    """Common interface implemented by DuckDBEngine and PostgresEngine.

    A single instance is scoped to one logical "database" (e.g. the
    "ecommerce" DuckDB catalog, or a Postgres practice database) — engines
    never see or touch the application's own PostgreSQL metadata database.
    """

    name: str

    @abstractmethod
    def execute(self, query: str, *, timeout_seconds: float, row_limit: int) -> SqlExecutionResult:
        """Executes exactly one read-only statement and returns a normalized result.

        Implementations must enforce `timeout_seconds` and cap returned rows
        at `row_limit` (setting `truncated=True` when more rows existed)."""

    @abstractmethod
    def list_tables(self) -> list[str]:
        """Table names visible in this engine's current database/schema."""

    @abstractmethod
    def get_table_schema(self, table_name: str) -> TableSchema:
        """Raises SqlEngineError if the table isn't registered/visible."""

    @abstractmethod
    def preview_table(self, table_name: str, *, sample_rows: int = 20) -> TablePreview:
        """Raises SqlEngineError if the table isn't registered/visible."""
