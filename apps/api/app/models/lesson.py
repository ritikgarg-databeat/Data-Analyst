from sqlalchemy import JSON, Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DifficultyLevel, LessonContentType


class Lesson(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single lesson within a Module.

    `content_reference` points at a content file under `content/lessons/`
    (Markdown/YAML/JSON) rather than storing lesson body text in Postgres —
    the database holds structure and progress, the content/ directory holds
    the authored material. See docs/architecture.md.
    """

    __tablename__ = "lessons"

    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_type: Mapped[LessonContentType] = mapped_column(
        Enum(LessonContentType, native_enum=False, length=20), default=LessonContentType.READING
    )
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=20), default=DifficultyLevel.BEGINNER
    )
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=10)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # {"type": "reading_percent" | "exercise_score" | "assessment_score", "threshold": float}
    # See app.models.enums.CompletionRuleType and app.services.completion_rules.
    completion_criteria: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    module: Mapped["Module"] = relationship(back_populates="lessons")  # noqa: F821
    exercises: Mapped[list["Exercise"]] = relationship(  # noqa: F821
        back_populates="lesson", cascade="all, delete-orphan"
    )
