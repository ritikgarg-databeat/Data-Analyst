from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import (
    InterviewMode,
    InterviewQuestionType,
    InterviewStatus,
    InterviewTargetType,
)


class InterviewQuestion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A thin interview-specific wrapper around an existing `Exercise`
    (Phase 9) — content-authored and synced from `content/interview/
    questions/*.yaml`, exactly like Case/ProjectTemplate. Deliberately does
    NOT duplicate the exercise's own prompt/hints/solution/grading: an
    interview question's real work (SQL/Python/Excel execution, rubric
    scoring, MC/short-answer grading) is 100% the existing Phase 2-4/9
    Exercise pipeline, reached via `exercise_id`. This row only adds what's
    specific to using that exercise *inside a timed interview*: its round
    type, time limit, follow-up chain, and which company archetypes it
    belongs to."""

    __tablename__ = "interview_questions"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    interview_type: Mapped[InterviewQuestionType] = mapped_column(
        Enum(InterviewQuestionType, native_enum=False, length=30)
    )
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Other InterviewQuestion ids, asked as interviewer follow-ups after this
    # one is answered correctly (spec section 9) — e.g. "your query works,
    # what if a customer has multiple subscriptions?".
    follow_up_question_ids: Mapped[list] = mapped_column(JSON, default=list)
    company_archetypes: Mapped[list] = mapped_column(JSON, default=list)

    version: Mapped[int] = mapped_column(Integer, default=1)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    exercise: Mapped["Exercise"] = relationship()  # noqa: F821


class InterviewTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A configurable mock/company-style interview structure (spec sections
    32, 46) — content-authored from `content/interview/templates/*.yaml`.
    `sections` is an ordered list of `{interview_type, title,
    duration_minutes, question_count, difficulty}`; `rubric_weights` is the
    6-dimension scoring weight breakdown (spec section 37), which can differ
    per template (e.g. a Business Analyst template weights Business
    Understanding higher than a Product Analytics one)."""

    __tablename__ = "interview_templates"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    target_profile: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sections: Mapped[list] = mapped_column(JSON, default=list)
    rubric_weights: Mapped[dict] = mapped_column(JSON, default=dict)
    tags: Mapped[list] = mapped_column(JSON, default=list)

    version: Mapped[int] = mapped_column(Integer, default=1)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    interviews: Mapped[list["Interview"]] = relationship(back_populates="template")


class Interview(UUIDPrimaryKeyMixin, Base):
    """One interview session/attempt (spec section 33's state machine) —
    either an instance of an `InterviewTemplate` (mock/company-style) or an
    ad-hoc single-round session (practice/timed/weakness-drill), identified
    by `mode`. `score`/`feedback` are computed once, deterministically, by
    `app/interview_engine/scoring.py` on submit — mirrors the Case Study
    Engine's `CaseAttempt.score`/`feedback` convention exactly."""

    __tablename__ = "interviews"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    mode: Mapped[InterviewMode] = mapped_column(Enum(InterviewMode, native_enum=False, length=20))
    status: Mapped[InterviewStatus] = mapped_column(
        Enum(InterviewStatus, native_enum=False, length=20), default=InterviewStatus.NOT_STARTED
    )
    title: Mapped[str] = mapped_column(String(200))

    total_time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    current_section_index: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    template: Mapped["InterviewTemplate | None"] = relationship(back_populates="interviews")
    sections: Mapped[list["InterviewSection"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan", order_by="InterviewSection.display_order"
    )
    question_attempts: Mapped[list["InterviewQuestionAttempt"]] = relationship(
        back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestionAttempt.display_order"
    )


class InterviewSection(UUIDPrimaryKeyMixin, Base):
    """One timed round within an Interview (e.g. "SQL — 15 min") — seeded
    from the template's `sections` when the interview starts; an ad-hoc
    single-round session gets exactly one."""

    __tablename__ = "interview_sections"

    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    interview_type: Mapped[str] = mapped_column(String(30))  # InterviewQuestionType value, or "CASE_STUDY"
    title: Mapped[str] = mapped_column(String(200))
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # How many non-follow-up questions this section should ask before
    # advancing — from the template's `question_count` for a template-backed
    # interview, or the ad-hoc `CreateInterviewRequest.question_count`
    # otherwise (never a hardcoded default once set).
    target_question_count: Mapped[int] = mapped_column(Integer, default=5)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    interview: Mapped["Interview"] = relationship(back_populates="sections")
    question_attempts: Mapped[list["InterviewQuestionAttempt"]] = relationship(back_populates="section")


class InterviewQuestionAttempt(UUIDPrimaryKeyMixin, Base):
    """One question presented within an Interview. `exercise_attempt_id`
    links to the REAL `ExerciseAttempt` created by submitting through the
    existing Exercise/SQL/Python/Excel grading services — this row is only
    the interview-context bookkeeping (which section, how long spent, follow-
    up chain), never a second copy of the answer or its grade."""

    __tablename__ = "interview_question_attempts"

    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), index=True)
    section_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_sections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    interview_question_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_questions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    case_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("case_attempts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    exercise_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("exercise_attempts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    parent_attempt_id: Mapped[str | None] = mapped_column(
        ForeignKey("interview_question_attempts.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_follow_up: Mapped[bool] = mapped_column(default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)

    interview: Mapped["Interview"] = relationship(back_populates="question_attempts")
    section: Mapped["InterviewSection | None"] = relationship(back_populates="question_attempts")
    interview_question: Mapped["InterviewQuestion | None"] = relationship()
    exercise_attempt: Mapped["ExerciseAttempt | None"] = relationship()  # noqa: F821
    case_attempt: Mapped["CaseAttempt | None"] = relationship()  # noqa: F821


class InterviewBookmark(UUIDPrimaryKeyMixin, Base):
    """A saved-for-later reference (spec section 52) — question/case/
    assessment (InterviewTemplate). Powers "My Interview Review"."""

    __tablename__ = "interview_bookmarks"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[InterviewTargetType] = mapped_column(Enum(InterviewTargetType, native_enum=False, length=20))
    target_id: Mapped[str] = mapped_column(String(100), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InterviewNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A personal note (spec section 55) on a question/skill/interview/case."""

    __tablename__ = "interview_notes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_type: Mapped[InterviewTargetType] = mapped_column(Enum(InterviewTargetType, native_enum=False, length=20))
    target_id: Mapped[str] = mapped_column(String(100), index=True)
    note: Mapped[str] = mapped_column(Text)


class InterviewPlan(UUIDPrimaryKeyMixin, Base):
    """A generated personalized interview-prep plan (spec section 41) —
    `days` is `[{day_number, focus_area, title, task_type, task_ref,
    description}]`, deterministically derived from the readiness/weakness
    engines at generation time (`readiness_snapshot` freezes the inputs that
    produced this specific plan, for later reference)."""

    __tablename__ = "interview_plans"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    days: Mapped[list] = mapped_column(JSON, default=list)
    readiness_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)


class ReadinessSnapshot(UUIDPrimaryKeyMixin, Base):
    """One point-in-time readiness computation (spec section 42's trend
    chart) — `breakdown` is `{interview_type: score}`."""

    __tablename__ = "readiness_snapshots"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    overall_score: Mapped[float] = mapped_column(Float)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
