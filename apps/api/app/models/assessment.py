from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AssessmentAttemptStatus, AssessmentRetryPolicy


class Assessment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A generic assessment attached to a Module — a scored set of Exercise questions."""

    __tablename__ = "assessments"

    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passing_score: Mapped[float] = mapped_column(Float, default=80.0)
    retry_policy: Mapped[AssessmentRetryPolicy] = mapped_column(
        Enum(AssessmentRetryPolicy, native_enum=False, length=20), default=AssessmentRetryPolicy.UNLIMITED
    )
    max_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    module: Mapped["Module"] = relationship()  # noqa: F821
    questions: Mapped[list["AssessmentQuestion"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.display_order"
    )


class AssessmentQuestion(Base):
    """One question in an Assessment — reuses the Exercise question bank rather than duplicating it."""

    __tablename__ = "assessment_questions"

    assessment_id: Mapped[str] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), primary_key=True
    )
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=10)

    assessment: Mapped["Assessment"] = relationship(back_populates="questions")
    exercise: Mapped["Exercise"] = relationship()  # noqa: F821


class AssessmentAttempt(UUIDPrimaryKeyMixin, Base):
    """A single attempt at an Assessment."""

    __tablename__ = "assessment_attempts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assessment_id: Mapped[str] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    status: Mapped[AssessmentAttemptStatus] = mapped_column(
        Enum(AssessmentAttemptStatus, native_enum=False, length=20),
        default=AssessmentAttemptStatus.IN_PROGRESS,
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    answers: Mapped[list["AssessmentAnswer"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan"
    )


class AssessmentAnswer(UUIDPrimaryKeyMixin, Base):
    """One answer within an AssessmentAttempt."""

    __tablename__ = "assessment_answers"

    attempt_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_attempts.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    submitted_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)

    attempt: Mapped["AssessmentAttempt"] = relationship(back_populates="answers")
    exercise: Mapped["Exercise"] = relationship()  # noqa: F821
