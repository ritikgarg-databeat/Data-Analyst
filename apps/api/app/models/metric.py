from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class MetricDefinition(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One entry in the Metrics Library (Phase 6, spec section 42) — a
    reference definition of a business/product metric, independent of any
    lesson/exercise. Seeded read-only data (`database/seeds/metrics.yaml`),
    analogous to `Tag`/`Domain` rather than user-authored content."""

    __tablename__ = "metric_definitions"

    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    category: Mapped[str] = mapped_column(String(50), index=True)  # revenue|customer|marketing|product|...
    definition: Mapped[str] = mapped_column(Text)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    sql_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    python_example: Mapped[str | None] = mapped_column(Text, nullable=True)
    common_mistakes: Mapped[list] = mapped_column(JSON, default=list)
    related_metrics: Mapped[list] = mapped_column(JSON, default=list)  # list of metric slugs
    business_questions: Mapped[list] = mapped_column(JSON, default=list)
    interview_questions: Mapped[list] = mapped_column(JSON, default=list)  # list of {question, answer}
    display_order: Mapped[int] = mapped_column(default=0)
