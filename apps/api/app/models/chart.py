from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Chart(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved chart configuration (section 22-26 of the Phase 5 spec) —
    `config` is the full chart-builder state (x/y/agg/color/filters/sort/
    bins/granularity...), re-run against the live dataset on read rather
    than storing rendered output, so it always reflects the current data.
    `insight_*` are the optional "Add Insight" fields (section 26); left
    null until the user fills them in — this doubles as the Chart/
    ChartConfiguration split from the spec without introducing a second
    table for what is, in practice, always a 1:1 relationship."""

    __tablename__ = "charts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    table_name: Mapped[str] = mapped_column(String(100))
    workspace_id: Mapped[str | None] = mapped_column(
        ForeignKey("eda_workspaces.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200))
    chart_type: Mapped[str] = mapped_column(String(20))  # bar|line|scatter|histogram|box|heatmap|pie
    config: Mapped[dict] = mapped_column(JSON)

    insight_observation: Mapped[str | None] = mapped_column(Text, nullable=True)
    insight_why_it_matters: Mapped[str | None] = mapped_column(Text, nullable=True)
    insight_recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)
