from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import CaseAttemptStatus, CaseCategory, CaseDifficulty, CaseStage


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A real-world business-problem case study (Phase 8) — content-authored
    and synced from `content/cases/*.yaml` exactly like Lesson/Exercise (see
    app/content/sync.py), not hard-coded. Deliberately NOT built on the
    existing Exercise/ExerciseAttempt pipeline the way Phase 6's lighter
    "Analytics Cases" are (see app/services/analytics_case_service.py's own
    docstring) — a case here is a multi-stage workspace (findings,
    hypotheses, evidence, executive summary), not a single-shot Q&A.

    `rubric`, `hints`, and `reference_solution` are never sent to the client
    until submission/review (see app/services/case_service.py) — the same
    "hidden until earned" pattern SQL/Python exercise solutions already use.
    `required_exercise_slugs` lets a case's "Technical Analysis" rubric
    category be scored objectively from real ExerciseAttempt pass/fail
    (reusing Phase 3/4/7's execution-graded SQL/Python/dbt exercises)
    instead of another parallel code-grading engine.
    """

    __tablename__ = "cases"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[CaseCategory] = mapped_column(Enum(CaseCategory, native_enum=False, length=30))
    difficulty: Mapped[CaseDifficulty] = mapped_column(Enum(CaseDifficulty, native_enum=False, length=20))
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=60)

    company_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    stakeholder_name: Mapped[str] = mapped_column(String(150))
    stakeholder_role: Mapped[str] = mapped_column(String(150))
    problem_statement: Mapped[str] = mapped_column(Text)
    business_context: Mapped[str | None] = mapped_column(Text, nullable=True)
    objective: Mapped[str] = mapped_column(Text)
    initial_information: Mapped[str | None] = mapped_column(Text, nullable=True)

    constraints: Mapped[list] = mapped_column(JSON, default=list)
    available_datasets: Mapped[list] = mapped_column(JSON, default=list)  # dataset slugs; not all are relevant
    expected_deliverables: Mapped[list] = mapped_column(JSON, default=list)
    learning_objectives: Mapped[list] = mapped_column(JSON, default=list)
    stages: Mapped[list] = mapped_column(JSON, default=list)  # subset of CaseStage values, in order
    required_exercise_slugs: Mapped[list] = mapped_column(JSON, default=list)
    # Plain slug lists rather than join tables (cf. ExerciseTag/LessonSkill) —
    # a deliberate simplification: at most a few dozen cases ever exist, so
    # in-memory filtering in the service layer (see app/services/case_service.py)
    # is simpler than two more many-to-many tables for this phase's scope.
    tags: Mapped[list] = mapped_column(JSON, default=list)
    skills: Mapped[list] = mapped_column(JSON, default=list)

    # Hidden from the client until the attempt is SUBMITTED/COMPLETED — see
    # app/schemas/case.py's split between the public and reviewer-facing schemas.
    clarification_guidance: Mapped[list] = mapped_column(JSON, default=list)
    rubric: Mapped[list] = mapped_column(JSON, default=list)  # [{category, weight, criteria: [{criterion, points}]}]
    hints: Mapped[list] = mapped_column(JSON, default=list)
    reference_solution: Mapped[dict] = mapped_column(JSON, default=dict)

    version: Mapped[int] = mapped_column(Integer, default=1)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    attempts: Mapped[list["CaseAttempt"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseAttempt(UUIDPrimaryKeyMixin, Base):
    """One user's run through a Case — the multi-stage workspace state.
    `case_version_snapshot` freezes which `Case.version` this attempt was
    made against (spec section 48) so a later content edit to the case
    can't retroactively change what an already-completed attempt was scored
    on. Findings/hypotheses live in the shared `finding`/`hypothesis` tables
    (see app/models/finding.py) so Projects can reuse the exact same
    structures instead of a parallel set."""

    __tablename__ = "case_attempts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    case_version_snapshot: Mapped[int] = mapped_column(Integer)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    status: Mapped[CaseAttemptStatus] = mapped_column(
        Enum(CaseAttemptStatus, native_enum=False, length=20), default=CaseAttemptStatus.NOT_STARTED
    )
    current_stage: Mapped[CaseStage | None] = mapped_column(
        Enum(CaseStage, native_enum=False, length=20), nullable=True
    )

    clarification_questions: Mapped[str | None] = mapped_column(Text, nullable=True)
    problem_framing: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    selected_dataset_slugs: Mapped[list] = mapped_column(JSON, default=list)
    recommendation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    executive_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    reflection: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    hints_used: Mapped[int] = mapped_column(Integer, default=0)
    solution_revealed: Mapped[bool] = mapped_column(default=False)

    rubric_selections: Mapped[dict] = mapped_column(JSON, default=dict)  # {category: [criterion, ...]}
    score: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    time_per_stage_seconds: Mapped[dict] = mapped_column(JSON, default=dict)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    case: Mapped["Case"] = relationship(back_populates="attempts")
