from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class EdaWorkspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved, reopenable EDA session against one dataset (section 19/50 of
    the Phase 5 spec) — `state` holds the interactive bits (selected table/
    columns, filters); `overview` caches the last "Generate EDA Overview"
    result (app/dataset_hub/eda_engine.py) so reopening the workspace
    doesn't require recomputation."""

    __tablename__ = "eda_workspaces"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    table_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overview: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    findings: Mapped[list["EdaFinding"]] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", order_by="EdaFinding.created_at"
    )


class EdaFinding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A structured insight captured during EDA (section 51) — the seed for
    a future case-study/portfolio write-up, not free-form notes (see
    `DatasetNote` for those)."""

    __tablename__ = "eda_findings"

    workspace_id: Mapped[str] = mapped_column(ForeignKey("eda_workspaces.id", ondelete="CASCADE"), index=True)
    observation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_implication: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str | None] = mapped_column(Text, nullable=True)

    workspace: Mapped["EdaWorkspace"] = relationship(back_populates="findings")
