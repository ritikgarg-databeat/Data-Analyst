from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DataQualityRuleType, DataQualityStatus


class DataQualityRule(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved, re-runnable data quality rule (spec sections 9-10, 40-41)
    against a real dataset table via DuckDB — `config` holds rule-specific
    parameters (accepted values, min/max, expected freshness interval,
    related table/column for a relationship check, expected row count)."""

    __tablename__ = "data_quality_rules"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    column_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    rule_type: Mapped[DataQualityRuleType] = mapped_column(
        Enum(DataQualityRuleType, native_enum=False, length=20)
    )
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)

    runs: Mapped[list["DataQualityRun"]] = relationship(
        back_populates="rule", cascade="all, delete-orphan", order_by="DataQualityRun.executed_at.desc()"
    )


class DataQualityRun(UUIDPrimaryKeyMixin, Base):
    """One execution of a DataQualityRule — append-only history."""

    __tablename__ = "data_quality_runs"

    rule_id: Mapped[str] = mapped_column(ForeignKey("data_quality_rules.id", ondelete="CASCADE"), index=True)
    status: Mapped[DataQualityStatus] = mapped_column(Enum(DataQualityStatus, native_enum=False, length=10))
    expected_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    actual_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    rule: Mapped["DataQualityRule"] = relationship(back_populates="runs")
