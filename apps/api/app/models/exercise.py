from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import DifficultyLevel, ExerciseType


class Exercise(UUIDPrimaryKeyMixin, Base):
    """A practice exercise, optionally attached to a Lesson.

    Question content (prompt, choices, hints, solution) lives in the content
    file at `content_reference` — this row is metadata + the join point for
    ExerciseAttempt/AssessmentQuestion. `exercise_type` anticipates future
    lab types (SQL/PYTHON execution) — Phase 2 grades only the types listed
    in `app.models.enums.AUTO_GRADABLE_EXERCISE_TYPES` from content-file data;
    execution engines land in Phase 3/4.
    """

    __tablename__ = "exercises"

    lesson_id: Mapped[str | None] = mapped_column(
        ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True, index=True
    )
    skill_id: Mapped[str | None] = mapped_column(
        ForeignKey("skills.id", ondelete="SET NULL"), nullable=True, index=True
    )
    dataset_id: Mapped[str | None] = mapped_column(
        ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True, index=True
    )
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    exercise_type: Mapped[ExerciseType] = mapped_column(Enum(ExerciseType, native_enum=False, length=20))
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=20), default=DifficultyLevel.BEGINNER
    )
    points: Mapped[int] = mapped_column(Integer, default=10)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    lesson: Mapped["Lesson | None"] = relationship(back_populates="exercises")  # noqa: F821
    skill: Mapped["Skill | None"] = relationship()  # noqa: F821
    dataset: Mapped["Dataset | None"] = relationship()  # noqa: F821
