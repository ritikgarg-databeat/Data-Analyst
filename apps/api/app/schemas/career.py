from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import (
    BehavioralStoryCategory,
    CareerGoalStatus,
    CareerGoalType,
    CareerMilestoneType,
    CareerReadinessLevel,
    TargetRoleCategory,
)
from app.schemas.common import ORMSchema

# --- Role templates + target roles ------------------------------------------


class RoleTemplateSchema(ORMSchema):
    id: str
    slug: str
    title: str
    category: TargetRoleCategory
    description: str | None
    core_skills: list[str]
    preferred_skills: list[str]
    nice_to_have_skills: list[str]
    typical_responsibilities: list[str]
    version: int


class TargetRoleSchema(ORMSchema):
    id: str
    role_template_id: str | None
    custom_title: str | None
    notes: str | None
    is_primary: bool
    created_at: datetime
    role_template: RoleTemplateSchema | None = None


class CreateTargetRoleRequest(BaseModel):
    role_template_slug: str | None = None
    custom_title: str | None = None
    notes: str | None = None
    is_primary: bool = False


class UpdateTargetRoleRequest(BaseModel):
    notes: str | None = None
    is_primary: bool | None = None


# --- Career profile ----------------------------------------------------------


class CareerProfileSchema(ORMSchema):
    id: str
    headline: str | None
    summary: str | None
    primary_target_role_id: str | None
    created_at: datetime
    updated_at: datetime


class UpdateCareerProfileRequest(BaseModel):
    headline: str | None = None
    summary: str | None = None
    primary_target_role_id: str | None = None


# --- Goals + timeline ---------------------------------------------------------


class CareerGoalSchema(ORMSchema):
    id: str
    goal_type: CareerGoalType
    title: str
    description: str | None
    target_value: str | None
    current_value: str | None
    target_date: date | None
    status: CareerGoalStatus
    created_at: datetime
    updated_at: datetime


class CreateCareerGoalRequest(BaseModel):
    goal_type: CareerGoalType
    title: str
    description: str | None = None
    target_value: str | None = None
    target_date: date | None = None


class UpdateCareerGoalRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    target_value: str | None = None
    current_value: str | None = None
    target_date: date | None = None
    status: CareerGoalStatus | None = None


class CareerMilestoneSchema(ORMSchema):
    id: str
    milestone_type: CareerMilestoneType
    title: str
    detail: str | None
    related_goal_id: str | None
    achieved_at: datetime


# --- Readiness assessment ------------------------------------------------------


class CareerAssessmentSchema(ORMSchema):
    id: str
    target_role_id: str | None
    rubric_scores: dict[str, float]
    overall_score: float
    overall_readiness_level: CareerReadinessLevel
    gating_passed: bool
    explanation: dict[str, list[str]]
    computed_at: datetime


class ComputeCareerAssessmentRequest(BaseModel):
    target_role_id: str | None = None


class CareerSkillMatrixEntrySchema(BaseModel):
    """One row of the Career Skill Matrix / Interview Evidence Mapping (spec
    sections 22, 34) — every count is a REAL aggregation from
    ExerciseAttempt/CaseAttempt/Project/Interview rows, never estimated."""

    skill_slug: str
    name: str
    category: str
    mastery_score: float
    evidence_level: str  # CareerEvidenceLevel value
    exercises_passed: int
    assessment_pct: float | None
    projects_count: int
    cases_count: int
    mock_interview_score: float | None
    is_gap_for_primary_role: bool = False


class CareerDashboardSchema(BaseModel):
    """Aggregation backing the Career Command Center — everything here is
    read from already-computed rows (profile/goals/latest assessment/recent
    milestones/achievement count), never recomputed here."""

    profile: CareerProfileSchema
    primary_target_role: TargetRoleSchema | None
    target_role_count: int
    latest_assessment: CareerAssessmentSchema | None
    active_goal_count: int
    recent_milestones: list[CareerMilestoneSchema]
    achievement_count: int
    saved_job_count: int


# --- Behavioral Story Bank -----------------------------------------------------


class BehavioralStorySchema(ORMSchema):
    id: str
    category: BehavioralStoryCategory
    title: str
    situation: str
    task: str
    action: str
    result: str
    related_question_ids: list[str]
    last_practiced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CreateBehavioralStoryRequest(BaseModel):
    category: BehavioralStoryCategory
    title: str
    situation: str
    task: str
    action: str
    result: str


class UpdateBehavioralStoryRequest(BaseModel):
    title: str | None = None
    situation: str | None = None
    task: str | None = None
    action: str | None = None
    result: str | None = None


class StoryCoverageEntrySchema(BaseModel):
    category: BehavioralStoryCategory
    story_count: int
    has_coverage: bool


class StoryCoverageResponse(BaseModel):
    coverage: list[StoryCoverageEntrySchema]
    missing_categories: list[BehavioralStoryCategory]


# --- Career Knowledge Base -----------------------------------------------------


class CareerNoteSchema(ORMSchema):
    id: str
    topic: str | None
    body: str
    created_at: datetime
    updated_at: datetime


class CreateCareerNoteRequest(BaseModel):
    topic: str | None = None
    body: str


class UpdateCareerNoteRequest(BaseModel):
    topic: str | None = None
    body: str | None = None


# --- Achievements ---------------------------------------------------------------


class AchievementSchema(ORMSchema):
    id: str
    slug: str
    title: str
    description: str
    icon: str | None
    criteria: dict


class UserAchievementSchema(ORMSchema):
    id: str
    earned_at: datetime
    achievement: AchievementSchema


# --- Weekly review --------------------------------------------------------------


class CareerReportSchema(BaseModel):
    """The exportable Career Report (spec section 46) — a point-in-time
    snapshot assembled entirely from already-computed rows (profile/target
    roles/latest assessment/goals/milestones/achievements/skill matrix
    highlights), reusing the existing client-side CSV/text download pattern
    (no new PDF-generation backend) rather than inventing new export infra."""

    generated_at: datetime
    profile: CareerProfileSchema
    target_roles: list[TargetRoleSchema]
    latest_assessment: CareerAssessmentSchema | None
    top_skill_gaps: list[CareerSkillMatrixEntrySchema]
    active_goals: list[CareerGoalSchema]
    recent_milestones: list[CareerMilestoneSchema]
    achievement_count: int


class WeeklyReviewResponse(BaseModel):
    """A deterministic rollup of the last 7 days (spec section 28) — hours/
    exercises/cases/projects/interviews/score deltas — the AI Career Coach
    only narrates this, never computes it."""

    period_start: date
    period_end: date
    exercises_attempted: int
    exercises_passed: int
    cases_completed: int
    projects_completed: int
    interviews_completed: int
    new_milestones: list[CareerMilestoneSchema]
    weak_skill_slugs: list[str] = Field(default_factory=list)
