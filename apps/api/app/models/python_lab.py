"""Python Lab (Phase 4) models. Mirrors app/models/sql_lab.py's shape and
conventions closely — see docs/architecture.md#python-lab-phase-4.

Reuses the existing `ExerciseAttempt` (Phase 2) for every Python exercise
submission (submitted_answer = the submitted source code), exactly as the
SQL Lab reused it for query submissions — `PythonExerciseTestResult` here
only adds the per-hidden-test breakdown, FK'd to `exercise_attempts.id`.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import PythonRuntimeStatus


class PythonWorkspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A named collection of cells (e.g. 'E-commerce EDA', 'Scratch') — see
    Phase 4 spec §29. `selected_dataset` is a `Dataset.slug`, purely a UI
    convenience (which dataset's browser panel/insert-code shortcuts to show
    by default), not a hard binding — any cell can load any dataset."""

    __tablename__ = "python_workspaces"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    selected_dataset: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    cells: Mapped[list[PythonCell]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", order_by="PythonCell.display_order"
    )


class PythonCell(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One notebook-like cell's *saved* code plus its most recent execution
    result (denormalized as one JSON blob — a full `PythonExecutionResultSchema`
    — rather than exploded into a dozen columns; see
    app/schemas/python_lab.py). Re-running is what refreshes `last_result`;
    nothing here holds a live runtime reference — that's `PythonRuntime`."""

    __tablename__ = "python_cells"

    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("python_workspaces.id", ondelete="CASCADE"), index=True
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    code: Mapped[str] = mapped_column(Text, default="")
    last_result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    workspace: Mapped[PythonWorkspace] = relationship(back_populates="cells")


class PythonRuntime(UUIDPrimaryKeyMixin, Base):
    """One live sandbox container. `container_id` is the opaque handle a
    `PythonRuntimeBackend` gave back from `.create()` — this app never talks
    to Docker except through that backend (app/python_lab/docker_backend.py).
    `workspace_id` is nullable: exercise grading creates short-lived,
    workspace-less runtimes that are destroyed immediately after grading."""

    __tablename__ = "python_runtimes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("python_workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(20), default=PythonRuntimeStatus.STARTING)
    container_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=10)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class PythonExecution(UUIDPrimaryKeyMixin, Base):
    """Append-only execution history — every Run, across every workspace,
    independent of whether the runtime that ran it still exists. Mirrors
    `SqlQueryHistory` exactly, including the Python-side `default=` on the
    timestamp (see that model's docstring for why: SQLite's
    `CURRENT_TIMESTAMP` is only second-precision, which made history rows
    sort non-deterministically under the fast in-memory test suite)."""

    __tablename__ = "python_executions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("python_workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20))  # success | error
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )


class PythonExerciseTestResult(UUIDPrimaryKeyMixin, Base):
    """Per-hidden-test pass/fail detail for one Python ExerciseAttempt —
    mirrors `SqlExerciseTestResult` exactly. The attempt itself (score,
    status, submitted code, execution_time_ms) lives on the existing
    `ExerciseAttempt` row."""

    __tablename__ = "python_exercise_test_results"

    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("exercise_attempts.id", ondelete="CASCADE"), index=True
    )
    test_name: Mapped[str] = mapped_column(String(200))
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    passed: Mapped[bool] = mapped_column(Boolean)
    message: Mapped[str] = mapped_column(Text)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
