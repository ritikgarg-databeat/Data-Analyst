from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import EvidenceType, FindingConfidence, HypothesisStatus


class Finding(UUIDPrimaryKeyMixin, Base):
    """A structured analytical finding (Phase 8, spec section 15) — shared
    by the Case Study Engine and the Project Engine (exactly one of
    `case_attempt_id`/`project_id` is set) rather than two near-duplicate
    tables, the same reasoning Phase 7 used to unify the Data Modeler/
    Architecture/Pipeline graph schema. `evidence` links back to real SQL
    queries/Python executions/charts/etc. (see Evidence's docstring)."""

    __tablename__ = "findings"

    case_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("case_attempts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )

    observation: Mapped[str] = mapped_column(Text)
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    impact: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[FindingConfidence | None] = mapped_column(
        Enum(FindingConfidence, native_enum=False, length=10), nullable=True
    )
    related_analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", foreign_keys="Evidence.finding_id"
    )


class Hypothesis(UUIDPrimaryKeyMixin, Base):
    """A tracked hypothesis (spec section 17) — shared by cases and projects,
    same reasoning as Finding above."""

    __tablename__ = "hypotheses"

    case_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("case_attempts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True
    )

    statement: Mapped[str] = mapped_column(Text)
    status: Mapped[HypothesisStatus] = mapped_column(
        Enum(HypothesisStatus, native_enum=False, length=20), default=HypothesisStatus.UNCHECKED
    )
    evidence_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="hypothesis", cascade="all, delete-orphan", foreign_keys="Evidence.hypothesis_id"
    )


class Evidence(UUIDPrimaryKeyMixin, Base):
    """A link from a Finding or Hypothesis back to the real artifact that
    supports it (spec sections 16, 52) — exactly one of `finding_id`/
    `hypothesis_id` is set. `ref_id` is the referenced row's id
    (SqlQueryHistory/PythonExecution/Chart/Dataset/DataModel — or a dbt
    model *name*, not a row id, for `DBT_MODEL`, since dbt models aren't
    rows in this database). `snapshot` denormalizes just enough of the
    referenced content (the query/code text, a stat's value, a chart's
    title) that a finding stays meaningful even after the referenced row is
    later deleted — see spec section 60's data-integrity requirement."""

    __tablename__ = "evidence"

    finding_id: Mapped[str | None] = mapped_column(
        ForeignKey("findings.id", ondelete="CASCADE"), nullable=True, index=True
    )
    hypothesis_id: Mapped[str | None] = mapped_column(
        ForeignKey("hypotheses.id", ondelete="CASCADE"), nullable=True, index=True
    )

    evidence_type: Mapped[EvidenceType] = mapped_column(Enum(EvidenceType, native_enum=False, length=20))
    ref_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    label: Mapped[str] = mapped_column(String(300))
    snapshot: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    finding: Mapped["Finding | None"] = relationship(back_populates="evidence", foreign_keys=[finding_id])
    hypothesis: Mapped["Hypothesis | None"] = relationship(
        back_populates="evidence", foreign_keys=[hypothesis_id]
    )
