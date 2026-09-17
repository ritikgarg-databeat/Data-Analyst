from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class SqlTable(UUIDPrimaryKeyMixin, Base):
    """One queryable table within a SQL Lab dataset (a `Dataset` becomes a
    multi-table "database" in the SQL Lab once it has SqlTable children —
    see app/sql/registry.py). `file_path` is repo-root-relative, resolved by
    the DuckDB engine at query time; the source file is never copied."""

    __tablename__ = "sql_tables"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    file_path: Mapped[str] = mapped_column(String(500))
    file_format: Mapped[str] = mapped_column(String(20))  # csv | parquet | json
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    grain: Mapped[str] = mapped_column(String(255))  # e.g. "1 row = 1 customer"
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    dataset: Mapped["Dataset"] = relationship()  # noqa: F821


class SqlWorkspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named container for saved queries (e.g. "Customer Retention", "Scratch")."""

    __tablename__ = "sql_workspaces"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    engine: Mapped[str] = mapped_column(String(20), default="duckdb")
    database: Mapped[str] = mapped_column(String(100))


class SqlSavedQuery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "sql_saved_queries"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("sql_workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    query: Mapped[str] = mapped_column(Text)
    engine: Mapped[str] = mapped_column(String(20))
    database: Mapped[str] = mapped_column(String(100))
    tags: Mapped[str | None] = mapped_column(String(300), nullable=True)  # comma-separated, kept simple


class SqlQueryHistory(UUIDPrimaryKeyMixin, Base):
    """Every ad-hoc query run through the SQL Lab (not exercise attempts —
    those log through the existing ExerciseAttempt model instead)."""

    __tablename__ = "sql_query_history"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    engine: Mapped[str] = mapped_column(String(20))
    database: Mapped[str] = mapped_column(String(100))
    query: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))  # success | error
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Python-side default (microsecond precision) rather than relying solely on
    # server_default=func.now() — SQLite's CURRENT_TIMESTAMP only has second
    # precision, which made same-second history rows sort non-deterministically
    # (ORDER BY executed_at DESC with no tiebreaker) under the fast in-memory
    # test suite. server_default stays as a fallback for raw SQL inserts.
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class SqlExerciseTestResult(UUIDPrimaryKeyMixin, Base):
    """Per-hidden-test pass/fail detail for one SQL ExerciseAttempt — the
    attempt itself (score, status, submitted SQL, execution_time_ms) already
    lives on the existing `ExerciseAttempt` row; this only adds the
    per-test breakdown feedback shown after a submission."""

    __tablename__ = "sql_exercise_test_results"

    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("exercise_attempts.id", ondelete="CASCADE"), index=True
    )
    test_name: Mapped[str] = mapped_column(String(200))
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=True)
    passed: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
