from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
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
from app.models.enums import (
    BehavioralStoryCategory,
    CareerGoalStatus,
    CareerGoalType,
    CareerMilestoneType,
    CareerReadinessLevel,
    JDRequirementKind,
    JDRequirementPriority,
    JDSource,
    JobPrepStatus,
    PortfolioItemType,
    PrivacyLevel,
    ResumeSource,
    TargetRoleCategory,
)

"""ORM models for Career Readiness, Portfolio, Resume/JD Intelligence & Job
Preparation (Phase 11) — see the Phase 11 section of app/models/enums.py for
the deterministic-vs-AI boundary. Every score this layer produces
(readiness, skill gaps, evidence levels) is computed here from real rows
already in the DB (UserSkill, ExerciseAttempt, Project, CaseAttempt,
Interview, ReadinessSnapshot) — AI (Phase 10) only explains/coaches around
these numbers, never computes them."""


def _utcnow() -> datetime:
    """A Python-side (not DB `server_default=func.now()`) timestamp default,
    used wherever code orders rows by "most recent" (e.g. latest
    JDAnalysis/CareerAssessment/SkillGap). SQLite's CURRENT_TIMESTAMP only
    has 1-second resolution, so two rows inserted within the same second via
    the server default tie — and an `ORDER BY ... DESC` with no secondary
    sort key on a tie is not guaranteed to return the most-recently-inserted
    row. Microsecond-resolution Python timestamps make "latest" unambiguous."""
    return datetime.now(UTC)


class CareerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One per user — the root of the Career dashboard. Holds free-text
    identity fields only; every score/gap/readiness number is computed live
    by the career services, never cached here."""

    __tablename__ = "career_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_career_profiles_user_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    headline: Mapped[str | None] = mapped_column(String(200), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_target_role_id: Mapped[str | None] = mapped_column(
        ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True
    )


class RoleTemplate(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A generic role template (spec section 4) — content-authored and
    synced from `content/career/role_templates/*.yaml`, exactly like Case/
    ProjectTemplate. Identifies overlapping vs. role-specific skills without
    claiming to represent every employer's actual requirements."""

    __tablename__ = "role_templates"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    category: Mapped[TargetRoleCategory] = mapped_column(
        Enum(TargetRoleCategory, native_enum=False, length=40)
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    core_skills: Mapped[list] = mapped_column(JSON, default=list)  # skill slugs common across most employers
    preferred_skills: Mapped[list] = mapped_column(JSON, default=list)
    nice_to_have_skills: Mapped[list] = mapped_column(JSON, default=list)
    typical_responsibilities: Mapped[list] = mapped_column(JSON, default=list)

    version: Mapped[int] = mapped_column(Integer, default=1)
    content_reference: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    target_roles: Mapped[list["TargetRole"]] = relationship(back_populates="role_template")


class TargetRole(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A role a user is actively preparing for — a user may hold several at
    once (spec section 3's "not hard-coded to one path"), optionally based on
    a RoleTemplate or fully custom."""

    __tablename__ = "target_roles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_template_id: Mapped[str | None] = mapped_column(
        ForeignKey("role_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    custom_title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    role_template: Mapped["RoleTemplate | None"] = relationship(back_populates="target_roles")


class JobDescription(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A saved job description (spec section 5) — pasted or uploaded, always
    kept as `raw_text` alongside its extracted JDRequirement rows so the
    original source stays available for re-analysis."""

    __tablename__ = "job_descriptions"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_role_id: Mapped[str | None] = mapped_column(
        ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    title: Mapped[str] = mapped_column(String(200))
    source: Mapped[JDSource] = mapped_column(Enum(JDSource, native_enum=False, length=20))
    raw_text: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    requirements: Mapped[list["JDRequirement"]] = relationship(
        back_populates="job_description", cascade="all, delete-orphan"
    )


class JDRequirement(UUIDPrimaryKeyMixin, Base):
    """One requirement extracted from a JobDescription (spec sections 6-8).
    `matched_skill_slug` is only ever a slug that already exists in the
    platform's skill taxonomy (database/seeds/skills.yaml) — AI extraction is
    validated against known skills, never allowed to invent a new one
    silently; unmatched requirements keep `matched_skill_slug = None`."""

    __tablename__ = "jd_requirements"

    job_description_id: Mapped[str] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[JDRequirementKind] = mapped_column(Enum(JDRequirementKind, native_enum=False, length=30))
    priority: Mapped[JDRequirementPriority] = mapped_column(
        Enum(JDRequirementPriority, native_enum=False, length=30)
    )
    raw_text: Mapped[str] = mapped_column(Text)
    matched_skill_slug: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )

    job_description: Mapped["JobDescription"] = relationship(back_populates="requirements")


class JDAnalysis(UUIDPrimaryKeyMixin, Base):
    """One computed JD Readiness Score run (spec section 9) — kept as an
    append-only history (not a 1:1 row) so re-running analysis after closing
    skill gaps shows visible progress. `weights` records the configurable
    dimension weights used for this specific run so the score stays
    explainable after the fact. Explicitly a platform-estimated readiness
    signal, never a claim about actual hiring outcome."""

    __tablename__ = "jd_analyses"

    job_description_id: Mapped[str] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True
    )
    readiness_score: Mapped[float] = mapped_column(Float)
    weights: Mapped[dict] = mapped_column(JSON, default=dict)
    breakdown: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )


class SkillGap(UUIDPrimaryKeyMixin, Base):
    """One skill gap comparison row (spec sections 6, 32) — belongs to
    EITHER a JobDescription (JD-specific gap) OR a TargetRole (role-level
    gap), never both; which one is set determines the gap's context, mirroring
    DatasetNote's nullable-scope-field precedent rather than a shared
    target_type/target_id column."""

    __tablename__ = "skill_gaps"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_description_id: Mapped[str | None] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_role_id: Mapped[str | None] = mapped_column(
        ForeignKey("target_roles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    skill_slug: Mapped[str] = mapped_column(String(150), index=True)
    required: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[JDRequirementPriority | None] = mapped_column(
        Enum(JDRequirementPriority, native_enum=False, length=30), nullable=True
    )
    current_mastery_score: Mapped[float] = mapped_column(Float, default=0.0)
    gap_size: Mapped[float] = mapped_column(Float, default=0.0)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A resume the user maintains — a container for ResumeVersion rows
    (spec section 30's versioning requirement); the resume itself carries no
    content, only identity."""

    __tablename__ = "resumes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeVersion.version_number"
    )


class ResumeVersion(UUIDPrimaryKeyMixin, Base):
    """One immutable snapshot of a Resume's text (spec section 30) — pasted
    or uploaded; `is_current` marks the one shown by default, editing always
    creates a new version rather than mutating an old one."""

    __tablename__ = "resume_versions"

    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    version_number: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[ResumeSource] = mapped_column(Enum(ResumeSource, native_enum=False, length=20))
    raw_text: Mapped[str] = mapped_column(Text)
    file_name: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )

    resume: Mapped["Resume"] = relationship(back_populates="versions")
    evidence: Mapped[list["ResumeEvidence"]] = relationship(
        back_populates="resume_version", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ResumeReview"]] = relationship(
        back_populates="resume_version", cascade="all, delete-orphan", order_by="ResumeReview.created_at"
    )


class ResumeEvidence(UUIDPrimaryKeyMixin, Base):
    """One evidence→skill mapping extracted from a resume (spec section 11)
    — `evidence_text` is a direct excerpt/paraphrase of what the resume
    already says, never a fabricated claim; `project_id` links it to a real
    platform Project when the resume line matches one."""

    __tablename__ = "resume_evidence"

    resume_version_id: Mapped[str] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="CASCADE"), index=True
    )
    skill_slug: Mapped[str] = mapped_column(String(150), index=True)
    evidence_text: Mapped[str] = mapped_column(Text)
    project_id: Mapped[str | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    resume_version: Mapped["ResumeVersion"] = relationship(back_populates="evidence")


class ResumeReview(UUIDPrimaryKeyMixin, Base):
    """An AI-assisted resume quality review (spec section 12) — reuses the
    same summary/issues/suggestions shape as the Phase 10 AIReviewResult
    schema so this isn't a bespoke output format."""

    __tablename__ = "resume_reviews"

    resume_version_id: Mapped[str] = mapped_column(
        ForeignKey("resume_versions.id", ondelete="CASCADE"), index=True
    )
    quality_score: Mapped[float] = mapped_column(Float)
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    impact_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    issues: Mapped[list] = mapped_column(JSON, default=list)
    suggestions: Mapped[list] = mapped_column(JSON, default=list)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )

    resume_version: Mapped["ResumeVersion"] = relationship(back_populates="reviews")


class Portfolio(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One per user — the container for PortfolioItem rows (spec section 19).
    `is_public_ready` is a user-set summary flag; the real per-item privacy
    control is PortfolioItem.privacy, always defaulting to PRIVATE."""

    __tablename__ = "portfolios"
    __table_args__ = (UniqueConstraint("user_id", name="uq_portfolios_user_id"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    headline: Mapped[str | None] = mapped_column(String(200), nullable=True)
    about: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public_ready: Mapped[bool] = mapped_column(Boolean, default=False)

    items: Mapped[list["PortfolioItem"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", order_by="PortfolioItem.display_order"
    )


class PortfolioItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One portfolio entry (spec sections 19-21) — for PROJECT/CASE_STUDY
    items, `ref_id` points at the real Project/CaseAttempt row (using only
    its actual facts); CERTIFICATION/ACHIEVEMENT/SKILL_HIGHLIGHT carry their
    content directly since there's no other row to link to. `privacy`
    defaults to PRIVATE — never exposed as PORTFOLIO or PUBLIC_READY without
    an explicit user action."""

    __tablename__ = "portfolio_items"

    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    item_type: Mapped[PortfolioItemType] = mapped_column(
        Enum(PortfolioItemType, native_enum=False, length=30)
    )
    ref_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    privacy: Mapped[PrivacyLevel] = mapped_column(
        Enum(PrivacyLevel, native_enum=False, length=20), default=PrivacyLevel.PRIVATE
    )
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    portfolio: Mapped["Portfolio"] = relationship(back_populates="items")


class CareerGoal(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A user-set career goal (spec section 26) — several goal types so this
    isn't hard-coded to only "reach readiness X"."""

    __tablename__ = "career_goals"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    goal_type: Mapped[CareerGoalType] = mapped_column(Enum(CareerGoalType, native_enum=False, length=30))
    title: Mapped[str] = mapped_column(String(300))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    current_value: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[CareerGoalStatus] = mapped_column(
        Enum(CareerGoalStatus, native_enum=False, length=20), default=CareerGoalStatus.ACTIVE
    )


class CareerMilestone(UUIDPrimaryKeyMixin, Base):
    """One Career Progress Timeline entry (spec section 25) — always written
    from a real deterministic event elsewhere (skill level-up, project/case/
    interview completion, goal completion, readiness level-up, achievement
    earned), never a freeform user-authored entry."""

    __tablename__ = "career_milestones"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    milestone_type: Mapped[CareerMilestoneType] = mapped_column(
        Enum(CareerMilestoneType, native_enum=False, length=30)
    )
    title: Mapped[str] = mapped_column(String(300))
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    related_goal_id: Mapped[str | None] = mapped_column(
        ForeignKey("career_goals.id", ondelete="SET NULL"), nullable=True
    )
    achieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )


class CareerAssessment(UUIDPrimaryKeyMixin, Base):
    """One point-in-time Career Readiness Rubric computation (spec sections
    23-24) — kept as history (mirrors ReadinessSnapshot) so the Career
    Progress Timeline can chart readiness trend. `explanation` answers "why"
    per dimension (spec section 35's explainability requirement).
    `overall_readiness_level` never implies a correspondence to an actual
    hiring decision."""

    __tablename__ = "career_assessments"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    target_role_id: Mapped[str | None] = mapped_column(
        ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    rubric_scores: Mapped[dict] = mapped_column(JSON, default=dict)  # {CareerRubricDimension: score}
    overall_score: Mapped[float] = mapped_column(Float)
    overall_readiness_level: Mapped[CareerReadinessLevel] = mapped_column(
        Enum(CareerReadinessLevel, native_enum=False, length=30)
    )
    gating_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    explanation: Mapped[dict] = mapped_column(JSON, default=dict)  # {CareerRubricDimension: [reasons]}
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )


class BehavioralStory(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One STAR-method story in the user's Behavioral Story Bank (spec
    section 38) — `category` matches the real tag taxonomy already used by
    Phase 9's behavioral exercises, so Interview Story Coverage can compare
    against the same category list. `related_question_ids` links to
    InterviewQuestion rows this story was practiced against."""

    __tablename__ = "behavioral_stories"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category: Mapped[BehavioralStoryCategory] = mapped_column(
        Enum(BehavioralStoryCategory, native_enum=False, length=40)
    )
    title: Mapped[str] = mapped_column(String(300))
    situation: Mapped[str] = mapped_column(Text)
    task: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(Text)
    result: Mapped[str] = mapped_column(Text)
    related_question_ids: Mapped[list] = mapped_column(JSON, default=list)
    last_practiced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JobPreparationWorkspace(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The per-JD "Prepare for This Job" workspace (spec sections 15, 31) —
    ties together a saved JobDescription with prep notes/checklist/status.
    Skill gaps, the prep plan, relevant projects, the interview plan, and
    resume alignment are all computed on demand from the JD/user's real data
    rather than duplicated into this row. Explicitly NOT job-application
    automation — this only tracks the user's own preparation."""

    __tablename__ = "job_preparation_workspaces"
    __table_args__ = (
        UniqueConstraint("job_description_id", name="uq_job_prep_workspace_jd_id"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    job_description_id: Mapped[str] = mapped_column(
        ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    checklist: Mapped[list] = mapped_column(JSON, default=list)  # [{label, is_done}]
    status: Mapped[JobPrepStatus] = mapped_column(
        Enum(JobPrepStatus, native_enum=False, length=20), default=JobPrepStatus.SAVED
    )


class Achievement(UUIDPrimaryKeyMixin, Base):
    """A badge definition (spec section 27's non-excessive Achievement
    System) — content-authored and synced from
    `content/career/achievements.yaml`, exactly like RoleTemplate.
    `criteria` is descriptive metadata for display only; actual earning is
    decided by app/services/achievement_service.py reading real platform
    events, never by re-interpreting this JSON as a rules engine."""

    __tablename__ = "achievements"

    slug: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    criteria: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserAchievement(UUIDPrimaryKeyMixin, Base):
    """One earned Achievement (append-only, never revoked)."""

    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    achievement_id: Mapped[str] = mapped_column(ForeignKey("achievements.id", ondelete="CASCADE"), index=True)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), default=_utcnow
    )

    achievement: Mapped["Achievement"] = relationship()


class CareerNote(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """One entry in the Career Knowledge Base (spec section 39) — a small,
    feature-scoped note model of its own rather than reusing InterviewNote's
    target_type/target_id shape, following this codebase's established
    one-note-model-per-feature-domain convention (Dataset Notes, Interview
    Notes)."""

    __tablename__ = "career_notes"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    body: Mapped[str] = mapped_column(Text)
