from datetime import date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import AIConversationRole, AIFeature

"""ORM models for the AI Layer (Phase 10) — see app/ai/AUTHORITY.md for the
deterministic-vs-AI boundary these tables exist inside of. Every deterministic
score/result the AI layer talks about (Interview.score, CaseAttempt.score,
ExerciseAttempt.score, UserSkill.mastery_score, TestResultResponse,
AnalyzeABTestResponse, ...) already lives in its own Phase 1-9 table and is
NEVER duplicated here — these tables only hold what's genuinely new: AI
conversations/messages, an audit trail, AI-only "soft" observations
(mistake memory, skill diagnosis) kept separate from real mastery, per-user
AI preferences, and daily usage counters."""


class AIConversation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One AI Mentor/Coach thread (spec section 41). `feature`/`context_type`/
    `context_id` record what the conversation was about (e.g. feature=
    SQL_TUTOR, context_type="sql_exercise", context_id=<exercise slug>) so it
    can be reopened with the right context re-attached, without persisting
    that context itself here (context is rebuilt fresh from the real,
    current DB state on reopen — see app/ai/context/)."""

    __tablename__ = "ai_conversations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feature: Mapped[AIFeature] = mapped_column(Enum(AIFeature, native_enum=False, length=40), index=True)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    context_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    context_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    last_message_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    messages: Mapped[list["AIMessage"]] = relationship(
        back_populates="conversation", order_by="AIMessage.created_at", cascade="all, delete-orphan"
    )


class AIMessage(UUIDPrimaryKeyMixin, Base):
    """One turn in an AIConversation. `hint_level` (spec section 8) is only
    set for tutoring turns that used the progressive hint ladder. Content is
    plain text — structured data the assistant returned (suggestions/
    confidence/evidence/etc., spec section 44) lives in `structured_output`
    alongside the human-readable `content`, never instead of it."""

    __tablename__ = "ai_messages"

    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[AIConversationRole] = mapped_column(Enum(AIConversationRole, native_enum=False, length=20))
    content: Mapped[str] = mapped_column(Text)
    structured_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    hint_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    conversation: Mapped[AIConversation] = relationship(back_populates="messages")


class AIAuditLog(UUIDPrimaryKeyMixin, Base):
    """One row per AI Gateway call (spec section 47) — feature/model/tokens/
    latency/success, plus a short REDACTED preview of the request (never the
    full prompt: "Do not store full sensitive prompts unnecessarily"). This is
    the append-only audit trail, distinct from AIConversation (which is the
    user-facing, editable/deletable thread)."""

    __tablename__ = "ai_audit_log"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    feature: Mapped[AIFeature] = mapped_column(Enum(AIFeature, native_enum=False, length=40), index=True)
    mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(100))
    context_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    request_preview: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIMistakeMemory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A reusable learning signal the AI has noticed recur (spec section 40)
    — e.g. "frequently forgets duplicate multiplication in many-to-many
    joins". Explicitly NOT mastery: UserSkill.mastery_score is computed only
    by the deterministic MasteryService from real ExerciseAttempt/assessment
    events (app/services/mastery.py) and nothing in this table is ever read
    by it. `occurrences`/`last_observed_at` grow via ordinary UPDATEs (no
    separate event log) since the memory itself, not its full history, is
    what's useful to the learner."""

    __tablename__ = "ai_mistake_memory"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_slug: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    mistake_summary: Mapped[str] = mapped_column(Text)
    first_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    recommended_review: Mapped[str | None] = mapped_column(String(300), nullable=True)


class AISkillDiagnosis(UUIDPrimaryKeyMixin, Base):
    """An AI observation about one exercise attempt (spec section 39) — kept
    entirely separate from UserSkill.mastery_score, which this table never
    writes to and never reads back into. `strength_areas`/`improvement_areas`
    are short human-readable labels, not new skill taxonomy entries."""

    __tablename__ = "ai_skill_diagnoses"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    skill_slug: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    exercise_attempt_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    diagnosis: Mapped[str] = mapped_column(Text)
    strength_areas: Mapped[list] = mapped_column(JSON, default=list)
    improvement_areas: Mapped[list] = mapped_column(JSON, default=list)
    recommended_exercise_slugs: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AISettings(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Per-user AI preferences plus separate administrator entitlement."""

    __tablename__ = "ai_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_ai_settings_user_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_access_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    admin_daily_request_limit: Mapped[int] = mapped_column(Integer, default=25)
    provider_override: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model_override: Mapped[str | None] = mapped_column(String(100), nullable=True)
    response_style: Mapped[str] = mapped_column(String(20), default="balanced")  # concise|balanced|detailed
    learning_mode: Mapped[str] = mapped_column(String(20), default="socratic")  # socratic|direct
    privacy_preference: Mapped[str] = mapped_column(String(20), default="standard")  # minimal|standard
    max_context_chars: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_request_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AIUsageCounter(UUIDPrimaryKeyMixin, Base):
    """One row per (user, day) — backs both the daily request-limit check and
    the "AI usage today" display (spec section 42)."""

    __tablename__ = "ai_usage_counters"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_ai_usage_counter_user_date"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    usage_date: Mapped[date] = mapped_column(Date, index=True)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
