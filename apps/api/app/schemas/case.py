from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CaseAttemptStatus, CaseCategory, CaseDifficulty, CaseStage
from app.schemas.common import ORMSchema


class RubricCriterionSchema(BaseModel):
    criterion: str
    points: int


class RubricCategorySchema(BaseModel):
    category: str
    weight: float
    criteria: list[RubricCriterionSchema]
    is_technical: bool = False


class CaseSchema(ORMSchema):
    """The public case shape — shown on the detail page and throughout the
    workspace. Deliberately excludes `clarification_guidance`, `hints` (only
    a count is exposed; text is revealed progressively — see
    POST /cases/attempts/{id}/hint), and `reference_solution` (see
    POST /cases/attempts/{id}/reveal-solution, gated on completion)."""

    id: str
    slug: str
    title: str
    category: CaseCategory
    difficulty: CaseDifficulty
    estimated_minutes: int
    company_context: str | None
    stakeholder_name: str
    stakeholder_role: str
    problem_statement: str
    business_context: str | None
    objective: str
    initial_information: str | None
    constraints: list[str]
    available_datasets: list[str]
    expected_deliverables: list[str]
    learning_objectives: list[str]
    stages: list[str]
    tags: list[str]
    skills: list[str]
    rubric: list[RubricCategorySchema]
    hint_count: int
    version: int


class CaseAdminListItemSchema(ORMSchema):
    """The admin-facing case row (Content Admin, spec section 61) — cases are
    content-authored in `content/cases/*.yaml` (see app/content/sync.py), so
    admin only lists/activates/deactivates rather than editing the content
    itself, matching the existing Lesson/Exercise admin panel convention."""

    id: str
    slug: str
    title: str
    category: CaseCategory
    difficulty: CaseDifficulty
    is_active: bool
    version: int


class UpdateCaseAdminRequest(BaseModel):
    is_active: bool


class CaseListItemSchema(BaseModel):
    case: CaseSchema
    attempt_id: str | None = None
    attempt_status: CaseAttemptStatus | None = None
    attempt_score: float | None = None


class CaseAttemptSchema(ORMSchema):
    id: str
    case_id: str
    case_version_snapshot: int
    attempt_number: int
    status: CaseAttemptStatus
    current_stage: CaseStage | None
    clarification_questions: str | None
    problem_framing: dict | None
    selected_dataset_slugs: list[str]
    recommendation: dict | None
    executive_summary: dict | None
    reflection: dict | None
    hints_used: int
    solution_revealed: bool
    rubric_selections: dict
    score: dict | None
    feedback: dict | None
    time_per_stage_seconds: dict
    started_at: datetime | None
    submitted_at: datetime | None
    completed_at: datetime | None
    last_activity_at: datetime | None
    submission_readiness: dict[str, bool] = {}


class UpdateStageRequest(BaseModel):
    stage: CaseStage


class SaveClarificationRequest(BaseModel):
    questions: str


class ProblemFramingPayload(BaseModel):
    problem: str
    objective: str
    primary_metric: str
    scope: str
    hypotheses: str


class SaveFramingRequest(BaseModel):
    framing: ProblemFramingPayload


class SaveDatasetSelectionRequest(BaseModel):
    dataset_slugs: list[str]


class RecommendationPayload(BaseModel):
    recommendation: str
    why: str
    expected_impact: str
    risks: str
    implementation_considerations: str
    next_steps: str


class SaveRecommendationRequest(BaseModel):
    recommendation: RecommendationPayload


class ExecutiveSummaryPayload(BaseModel):
    problem: str
    key_findings: str
    business_impact: str
    recommendation: str
    next_steps: str


class SaveExecutiveSummaryRequest(BaseModel):
    executive_summary: ExecutiveSummaryPayload


class RecordStageTimeRequest(BaseModel):
    stage: CaseStage
    seconds: float


class RevealHintResponse(BaseModel):
    hint: str
    hints_used: int


class SubmitCaseAttemptRequest(BaseModel):
    rubric_selections: dict[str, list[str]]  # {category: [criterion, ...]}


class ReflectionPayload(BaseModel):
    what_learned: str
    what_difficult: str
    what_differently: str
    skill_improved: str
    what_review: str


class SaveReflectionRequest(BaseModel):
    reflection: ReflectionPayload


class RevealCaseSolutionResponse(BaseModel):
    summary: str
    key_insights: list[str]
    recommendation: str | None
    acceptable_alternatives: list[str]
