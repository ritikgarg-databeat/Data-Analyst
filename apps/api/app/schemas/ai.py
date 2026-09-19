"""Pydantic schemas for the AI Layer (Phase 10) — both the internal
structured-output shapes an AI response is validated against (spec section
44, "never trust model output blindly") and the external request/response
API contract. Structured-output models are intentionally small and reusable
across features rather than one bespoke shape per feature (mirrors how
`TestResultResponse` is one shape shared by every hypothesis test in
app/schemas/statistics.py)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMSchema

ClaimType = Literal["OBSERVED", "INFERRED", "HYPOTHESIS", "UNKNOWN"]


# --- Structured AI output (validated, never trusted blindly) ---------------


class AIClaim(BaseModel):
    """One data-specific claim inside an AI response, tagged per spec section
    17. Every AIReviewResult claim must carry one of these — a response with
    an untagged data-specific claim is a validation failure, not something
    the Gateway silently accepts."""

    claim: str
    claim_type: ClaimType
    evidence: str | None = None


class AIReviewResult(BaseModel):
    """The general-purpose structured shape (spec section 44's own example)
    — used by SQL/Python code review, analysis review, project review,
    domain coaching, communication/storytelling coaching, insight review,
    and (Phase 11) resume/portfolio review. Not every feature populates
    every field."""

    summary: str
    strengths: list[str] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    claims: list[AIClaim] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class AIInsightReviewResult(BaseModel):
    """Insight Reviewer (spec section 16) — evaluates the 4-part
    Observation/Evidence/Impact/Recommendation structure explicitly, one
    verdict per part, rather than the generic review shape."""

    observation_supported: bool
    observation_note: str
    evidence_sufficient: bool
    evidence_note: str
    impact_reasonable: bool
    impact_note: str
    recommendation_follows: bool
    recommendation_note: str
    overall_assessment: str


class AIDebugResult(BaseModel):
    """SQL/Python debugging (spec section 11) — the fixed 5-part structure.
    `what_happened`/`why_it_likely_happened` must be grounded in the actual
    error text passed into context; the Gateway never fabricates one when no
    error was supplied (the caller simply shouldn't invoke SQL_DEBUG then)."""

    what_happened: str
    why_it_likely_happened: str
    where: str
    how_to_investigate: str
    suggested_fix: str


class AINlToSqlResult(BaseModel):
    sql: str
    explanation_steps: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)


class AINlToPythonResult(BaseModel):
    plan: list[str] = Field(default_factory=list)
    code: str


class AIEdaResult(BaseModel):
    """AI EDA Assistant (spec section 23) — `observed_issues` must be
    grounded in the real DatasetProfile/EdaOverview passed into context;
    `suggested_investigations` are explicitly framed as unverified next
    steps, kept in a separate field so the UI can label them differently."""

    what_to_inspect: list[str] = Field(default_factory=list)
    observed_issues: list[str] = Field(default_factory=list)
    suggested_investigations: list[str] = Field(default_factory=list)
    important_variables: list[str] = Field(default_factory=list)
    suggested_visualizations: list[str] = Field(default_factory=list)
    suggested_questions: list[str] = Field(default_factory=list)
    potential_hypotheses: list[str] = Field(default_factory=list)


class AIInterviewerTurnResult(BaseModel):
    """One turn of the AI Case/Behavioral Interviewer (spec sections 26-30).
    `revealed_info_keys` names which gated pieces of the case's fixed
    specification (e.g. "segment_breakdown") this turn disclosed, so the
    service layer can update what's been revealed so far without the model
    itself being trusted to track that state."""

    interviewer_message: str
    revealed_info_keys: list[str] = Field(default_factory=list)
    follow_up_asked: bool = False


class AIDebriefResult(BaseModel):
    """AI Interview/Case/Behavioral Debrief (spec sections 29, 60)."""

    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    missed_opportunities: list[str] = Field(default_factory=list)
    suggested_practice: list[str] = Field(default_factory=list)


class AIExecSummaryResult(BaseModel):
    """Executive Communication Coach (spec section 58) — the fixed 5-line
    structure."""

    what_happened: str
    why: str
    impact: str
    recommendation: str
    next_step: str


class AIPlanDayExplanation(BaseModel):
    day_number: int
    why: str


class AIPlanExplanationResult(BaseModel):
    """AI Learning Planner (spec section 37) — explains WHY each day of the
    already-generated, deterministic `InterviewPlan` was selected. Does not
    generate the plan itself (`app/interview_engine/plan.py` already did) —
    see section 38, "Do not let AI arbitrarily rewrite the curriculum"."""

    day_explanations: list[AIPlanDayExplanation] = Field(default_factory=list)


class AISkillObservation(BaseModel):
    skill: str
    assessment: str


class AISkillDiagnosisResult(BaseModel):
    """AI Skill Diagnosis (spec section 39) — kept separate from
    UserSkill.mastery_score; see AISkillDiagnosis model docstring."""

    diagnosis_summary: str
    skill_observations: list[AISkillObservation] = Field(default_factory=list)
    recommended_practice: list[str] = Field(default_factory=list)


class AIProjectReviewResult(BaseModel):
    """AI Project Review (spec section 59)."""

    strong: list[str] = Field(default_factory=list)
    needs_improvement: list[str] = Field(default_factory=list)
    technical: list[str] = Field(default_factory=list)
    business: list[str] = Field(default_factory=list)
    communication: list[str] = Field(default_factory=list)
    top_3_improvements: list[str] = Field(default_factory=list)


class AIJDRequirementExtraction(BaseModel):
    """One requirement extracted from a job description (Phase 11, spec
    sections 6-8). `matched_skill_slug` must be one of the known platform
    skill slugs given in context, or None — the model is never allowed to
    invent a new skill slug; the service layer re-validates this regardless
    of what the model returns (spec section 7's "never inventing new skills
    silently")."""

    raw_text: str
    kind: str  # JDRequirementKind value
    priority: str  # JDRequirementPriority value
    matched_skill_slug: str | None = None


class AIJDExtractionResult(BaseModel):
    """AI JD Extraction (Phase 11, spec section 6) — structured requirements
    parsed from a pasted/uploaded job description's raw text."""

    requirements: list[AIJDRequirementExtraction] = Field(default_factory=list)
    company_context: str | None = None
    summary: str | None = None


class AIKnowledgeSource(BaseModel):
    title: str
    lesson_slug: str | None = None
    module_slug: str | None = None
    domain_slug: str | None = None
    kind: str = "lesson"  # lesson | metric | exercise


class AIKnowledgeAnswerResult(BaseModel):
    """Ask the Knowledge Base (spec sections 61-64) — retrieval-grounded
    answer. `insufficient_knowledge` is set when the retriever found nothing
    relevant enough to answer from (spec section 64: "say so")."""

    answer: str
    sources: list[AIKnowledgeSource] = Field(default_factory=list)
    insufficient_knowledge: bool = False


# --- API request/response schemas -------------------------------------------


class AISettingsSchema(ORMSchema):
    id: str
    created_at: datetime
    updated_at: datetime
    enabled: bool
    provider_override: str | None
    model_override: str | None
    response_style: str
    learning_mode: str
    privacy_preference: str
    max_context_chars: int | None
    daily_request_limit: int | None
    admin_access_enabled: bool
    effective_access_enabled: bool
    effective_provider: str
    ai_configured: bool


class UpdateAISettingsRequest(BaseModel):
    enabled: bool | None = None
    provider_override: str | None = None
    model_override: str | None = None
    response_style: str | None = None
    learning_mode: str | None = None
    privacy_preference: str | None = None
    max_context_chars: int | None = None


class AIUsageResponse(BaseModel):
    date: date
    request_count: int
    input_tokens: int
    output_tokens: int
    daily_request_limit: int
    requests_remaining: int
    privacy_notice: str


class AIMessageSchema(BaseModel):
    id: str
    role: str
    content: str
    structured_output: dict | None
    hint_level: int | None
    created_at: datetime


class AIConversationSchema(ORMSchema):
    id: str
    created_at: datetime
    updated_at: datetime
    feature: str
    title: str | None
    context_type: str | None
    context_id: str | None
    is_archived: bool
    last_message_at: datetime
    messages: list[AIMessageSchema] = Field(default_factory=list)


class AIConversationListItemSchema(ORMSchema):
    id: str
    created_at: datetime
    updated_at: datetime
    feature: str
    title: str | None
    context_type: str | None
    context_id: str | None
    is_archived: bool
    last_message_at: datetime


class AskMentorRequest(BaseModel):
    message: str
    context_type: Literal["sql", "python", "lesson", "case", "interview", "general"] = "general"
    context_id: str | None = None
    conversation_id: str | None = None
    mode: Literal["TUTOR", "COACH", "REVIEWER", "INTERVIEWER", "ANALYST", "EXPLAINER"] = "TUTOR"


class HintLevelRequest(BaseModel):
    context_type: Literal["sql", "python", "lesson"] = "sql"
    context_id: str
    hint_level: int = Field(ge=1, le=4)  # 1,2,3 = hints; 4 = full solution
    conversation_id: str | None = None


class AIChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    reply: str
    structured: dict | None = None
    hint_level: int | None = None
    provider: str
    model: str
    ai_configured: bool


class ReviewSqlRequest(BaseModel):
    query: str
    question: str | None = None
    engine: str = "duckdb"
    database: str | None = None


class DebugSqlRequest(BaseModel):
    query: str
    error_message: str
    engine: str = "duckdb"
    database: str | None = None


class OptimizeSqlRequest(BaseModel):
    query: str
    engine: str = "duckdb"
    database: str | None = None
    execution_time_ms: int | None = None


class NlToSqlRequest(BaseModel):
    request: str
    database: str
    engine: str = "duckdb"


class ReviewPythonRequest(BaseModel):
    code: str
    question: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    traceback_text: str | None = None


class NlToPythonRequest(BaseModel):
    request: str
    dataset_slugs: list[str] = Field(default_factory=list)


class ReviewAnalysisRequest(BaseModel):
    business_question: str
    dataset_slug: str | None = None
    code: str | None = None
    findings: str | None = None


class ReviewInsightRequest(BaseModel):
    observation: str
    evidence: str
    impact: str
    recommendation: str
    case_attempt_id: str | None = None


class EdaAssistRequest(BaseModel):
    dataset_id: str
    table_name: str | None = None
    # Only meaningful for /eda/explore (Explore with AI) — DATA_EXPLORATION's
    # own prompt documents an optional user_goal input; /eda/assist ignores it
    # since EDA_ASSISTANT's prompt is grounded in the profile alone.
    user_goal: str | None = None


class DomainCoachRequest(BaseModel):
    domain: Literal[
        "STATISTICS", "EXPERIMENTATION", "PRODUCT_ANALYTICS", "BUSINESS_ANALYTICS", "DATA_MODELING", "DBT"
    ]
    question: str | None = None
    result_ref: dict = Field(default_factory=dict)


class AIStructuredResponse(BaseModel):
    """Generic wrapper returned by review/coach/debug-style endpoints —
    `structured` holds the validated result (shape depends on the endpoint;
    documented per-endpoint in app/routers/ai.py), `structured_valid` is
    false when the provider's output couldn't be validated (never silently
    dropped — `raw_text` still carries whatever the provider said)."""

    raw_text: str
    structured: dict | None
    structured_valid: bool
    provider: str
    model: str
    ai_configured: bool
    audit_id: str | None = None


class CaseCoachRequest(BaseModel):
    message: str
    coaching_mode: Literal["GUIDED", "STANDARD", "INTERVIEW", "STRICT"] = "STANDARD"
    conversation_id: str | None = None


class CaseInterviewerTurnRequest(BaseModel):
    message: str
    conversation_id: str | None = None


class BehavioralInterviewerTurnRequest(BaseModel):
    message: str
    interview_question_attempt_id: str
    conversation_id: str | None = None


class CommunicationReviewRequest(BaseModel):
    text: str
    audience: str | None = None


class StorytellingReviewRequest(BaseModel):
    findings_text: str
    chart_description: str | None = None


class ExecSummaryRequest(BaseModel):
    analysis_text: str


class PlanExplanationRequest(BaseModel):
    plan_id: str


class SkillDiagnosisRequest(BaseModel):
    exercise_attempt_id: str


class AIMistakeMemorySchema(ORMSchema):
    id: str
    created_at: datetime
    updated_at: datetime
    skill_slug: str | None
    category: str | None
    mistake_summary: str
    first_observed_at: datetime
    last_observed_at: datetime
    occurrences: int
    recommended_review: str | None


class AISkillDiagnosisSchema(BaseModel):
    id: str
    skill_slug: str | None
    exercise_attempt_id: str | None
    diagnosis: str
    strength_areas: list[str]
    improvement_areas: list[str]
    recommended_exercise_slugs: list[str]
    created_at: datetime


class ProjectReviewRequest(BaseModel):
    project_id: str


class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class JDExtractionRequest(BaseModel):
    job_description_id: str


class ResumeReviewRequest(BaseModel):
    resume_version_id: str


class CareerCoachRequest(BaseModel):
    message: str
    topic: Literal["goal", "readiness", "weekly_review", "jd_prep", "general"] = "general"
    conversation_id: str | None = None


class PortfolioReviewRequest(BaseModel):
    portfolio_id: str
