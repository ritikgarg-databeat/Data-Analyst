from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import LessonProgressStatus


class LessonProgress(Base):
    """Tracks a user's progress through a single Lesson."""

    __tablename__ = "lesson_progress"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)

    status: Mapped[LessonProgressStatus] = mapped_column(
        Enum(LessonProgressStatus, native_enum=False, length=20), default=LessonProgressStatus.NOT_STARTED
    )
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    # Opaque resume marker (e.g. a block index) — interpreted by the frontend only.
    last_position: Mapped[str | None] = mapped_column(String(50), nullable=True)
    exercises_completed: Mapped[int] = mapped_column(Integer, default=0)

    lesson: Mapped["Lesson"] = relationship()  # noqa: F821
