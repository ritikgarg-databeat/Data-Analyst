from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import DbtCommand, DbtRunStatus


class DbtRun(UUIDPrimaryKeyMixin, Base):
    """A record of one `dbt <command>` invocation against the local dbt Lab
    project (spec sections 28-34). dbt's own rich state (compiled SQL, the
    full DAG, per-column docs) already lives in its own artifacts on disk
    (target/manifest.json, target/run_results.json) — this table is just
    run *history* (what ran, when, pass/fail/error counts, captured log),
    not a duplicate mirror of those artifacts."""

    __tablename__ = "dbt_runs"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    command: Mapped[DbtCommand] = mapped_column(Enum(DbtCommand, native_enum=False, length=20))
    selector: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[DbtRunStatus] = mapped_column(Enum(DbtRunStatus, native_enum=False, length=10))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    log: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
