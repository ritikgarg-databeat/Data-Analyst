from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import JDRequirementKind, JDRequirementPriority, JDSource, JobPrepStatus
from app.schemas.common import ORMSchema

# --- Job descriptions + requirements -----------------------------------------


class JDRequirementSchema(ORMSchema):
    id: str
    kind: JDRequirementKind
    priority: JDRequirementPriority
    raw_text: str
    matched_skill_slug: str | None
    confidence: float | None


class JobDescriptionSchema(ORMSchema):
    id: str
    target_role_id: str | None
    company: str | None
    title: str
    source: JDSource
    raw_text: str
    location: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    requirements: list[JDRequirementSchema] = Field(default_factory=list)


class JobDescriptionListItemSchema(ORMSchema):
    """Lighter row for list views — omits raw_text/requirements."""

    id: str
    target_role_id: str | None
    company: str | None
    title: str
    source: JDSource
    location: str | None
    created_at: datetime
    updated_at: datetime


class CreateJobDescriptionRequest(BaseModel):
    company: str | None = None
    title: str
    source: JDSource
    raw_text: str
    location: str | None = None
    notes: str | None = None
    target_role_id: str | None = None


class UpdateJobDescriptionRequest(BaseModel):
    company: str | None = None
    title: str | None = None
    notes: str | None = None
    target_role_id: str | None = None


# --- JD analysis / readiness --------------------------------------------------


class JDAnalysisSchema(ORMSchema):
    id: str
    readiness_score: float
    weights: dict[str, float]
    breakdown: dict
    summary: str | None
    ai_explanation: str | None
    computed_at: datetime


class AnalyzeJobDescriptionRequest(BaseModel):
    weights: dict[str, float] | None = None  # None -> service defaults


# --- Skill gaps ----------------------------------------------------------------


class SkillGapSchema(ORMSchema):
    id: str
    skill_slug: str
    required: bool
    priority: JDRequirementPriority | None
    current_mastery_score: float
    gap_size: float
    computed_at: datetime


class SkillGapTableResponse(BaseModel):
    gaps: list[SkillGapSchema]
    covered_skill_slugs: list[str] = Field(default_factory=list)


# --- Preparation plan / interview plan -----------------------------------------


class PreparationTaskSchema(BaseModel):
    """One task in the JD Preparation Plan (spec section 15) — deterministic
    relationships (skill -> recommended exercise/case/project slugs) with an
    optional AI-authored `why` explanation attached separately."""

    skill_slug: str
    priority: JDRequirementPriority | None
    recommended_exercise_slugs: list[str] = Field(default_factory=list)
    recommended_case_slugs: list[str] = Field(default_factory=list)
    recommended_project_slugs: list[str] = Field(default_factory=list)


class PreparationPlanResponse(BaseModel):
    job_description_id: str
    tasks: list[PreparationTaskSchema]


class JDInterviewPlanResponse(BaseModel):
    """A JD-specific interview prep aid (spec section 16) — estimated prep
    guidance derived from the JD's own requirement mix, never a claim about
    the actual employer's real interview process."""

    job_description_id: str
    focus_interview_types: list[str]
    suggested_question_slugs: list[str] = Field(default_factory=list)
    suggested_case_slugs: list[str] = Field(default_factory=list)
    note: str


# --- Job Preparation Workspace --------------------------------------------------


class ChecklistItemSchema(BaseModel):
    label: str
    is_done: bool = False


class JobPreparationWorkspaceSchema(ORMSchema):
    id: str
    job_description_id: str
    notes: str | None
    checklist: list[ChecklistItemSchema]
    status: JobPrepStatus
    created_at: datetime
    updated_at: datetime


class CreateJobPrepWorkspaceRequest(BaseModel):
    job_description_id: str


class UpdateJobPrepWorkspaceRequest(BaseModel):
    notes: str | None = None
    checklist: list[ChecklistItemSchema] | None = None
    status: JobPrepStatus | None = None


class JDComparisonEntrySchema(BaseModel):
    job_description_id: str
    title: str
    company: str | None
    readiness_score: float | None
    must_have_gap_count: int


class JDComparisonResponse(BaseModel):
    entries: list[JDComparisonEntrySchema]
    common_must_have_skill_slugs: list[str] = Field(default_factory=list)
