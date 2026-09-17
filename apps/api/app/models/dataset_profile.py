"""The Phase 5 profiling/quality data model — populated by
app/dataset_hub/profiling.py + app/dataset_hub/quality.py, one
DatasetProfile (+ its DatasetColumnProfile children) and one
DatasetQualityReport per DatasetTable, regenerated wholesale on every
profiling run (old rows deleted, not updated in place — profiling is cheap
and deterministic, so there is no reason to reconcile field-by-field)."""

from datetime import UTC, datetime

from sqlalchemy import JSON, BigInteger, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin


class DatasetProfile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "dataset_profiles"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    row_count: Mapped[int] = mapped_column(Integer)
    column_count: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    duplicate_row_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )

    columns: Mapped[list["DatasetColumnProfile"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="DatasetColumnProfile.display_order"
    )


class DatasetColumnProfile(UUIDPrimaryKeyMixin, Base):
    """Only the statistics appropriate to `data_type` are populated (section
    13 of the Phase 5 spec: "do not calculate inappropriate statistics for
    every data type") — e.g. mean/std/quantiles stay null for a categorical
    or text column."""

    __tablename__ = "dataset_column_profiles"

    profile_id: Mapped[str] = mapped_column(ForeignKey("dataset_profiles.id", ondelete="CASCADE"), index=True)
    column_name: Mapped[str] = mapped_column(String(150))
    data_type: Mapped[str] = mapped_column(String(20))  # numeric | categorical | datetime | text | boolean
    inferred_sql_type: Mapped[str] = mapped_column(String(50))
    null_count: Mapped[int] = mapped_column(Integer, default=0)
    null_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    unique_count: Mapped[int] = mapped_column(Integer, default=0)
    unique_percentage: Mapped[float] = mapped_column(Float, default=0.0)

    min_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    max_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    median: Mapped[float | None] = mapped_column(Float, nullable=True)
    std_dev: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantiles: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"p25":..,"p50":..,"p75":..}
    zero_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    negative_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outlier_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outlier_method: Mapped[str | None] = mapped_column(String(20), nullable=True)  # iqr | zscore

    top_values: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{"value":..,"count":..,"pct":..}]
    sample_values: Mapped[list | None] = mapped_column(JSON, nullable=True)

    min_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    avg_length: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Format-specific auxiliary info that doesn't warrant its own column
    # (e.g. datetime: {"missing_calendar_days": N, "date_span_days": N}).
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    display_order: Mapped[int] = mapped_column(Integer, default=0)

    profile: Mapped["DatasetProfile"] = relationship(back_populates="columns")


class DatasetQualityReport(UUIDPrimaryKeyMixin, Base):
    """A deterministic, explained-methodology quality score (section 15 of
    the Phase 5 spec) — an analytical aid, never a claim of objective
    correctness. `methodology` is rendered verbatim in the UI so the scoring
    logic is never a black box."""

    __tablename__ = "dataset_quality_reports"

    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    overall_score: Mapped[float] = mapped_column(Float)
    completeness_score: Mapped[float] = mapped_column(Float)
    uniqueness_score: Mapped[float] = mapped_column(Float)
    validity_score: Mapped[float] = mapped_column(Float)
    consistency_score: Mapped[float] = mapped_column(Float)
    duplicate_row_count: Mapped[int] = mapped_column(Integer, default=0)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    methodology: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
