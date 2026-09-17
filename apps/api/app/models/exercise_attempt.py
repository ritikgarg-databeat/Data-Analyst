from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import UUIDPrimaryKeyMixin
from app.models.enums import ExerciseAttemptStatus


class ExerciseAttempt(UUIDPrimaryKeyMixin, Base):
    """A record of one attempt at an Exercise.

    `submitted_answer` holds the actual submitted value (MCQ choice text,
    short-answer text, etc.) for the Phase 2 content-graded exercise types.
    `answer_reference` is reserved for future file/execution-based
    submissions (e.g. SQL/Python code) once execution engines exist.
    """

    __tablename__ = "exercise_attempts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)

    status: Mapped[ExerciseAttemptStatus] = mapped_column(
        Enum(ExerciseAttemptStatus, native_enum=False, length=20), default=ExerciseAttemptStatus.PENDING
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    submitted_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    solution_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
