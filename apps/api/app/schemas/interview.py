from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DifficultyLevel, InterviewMode, InterviewStatus, InterviewTargetType
from app.schemas.common import ORMSchema
from app.schemas.excel import ExcelSheetSchema
from app.schemas.exercise import RubricCriterionSchema


# --- Question catalog -------------------------------------------------------


class InterviewQuestionListItem(ORMSchema):
    id: str
    slug: str
    interview_type: str
    difficulty: DifficultyLevel
    title: str
    points: int
    time_limit_seconds: int | None
    company_archetypes: list[str]
    tags: list[str] = []
    is_bookmarked: bool = False
    best_score: float | None = None
    attempt_count: int = 0


class InterviewQuestionDetail(InterviewQuestionListItem):
    """Everything needed to actually attempt the question — the underlying
    exercise's public content (prompt/choices/business_context/rubric/
    hint_count), never its solution."""

    exercise_slug: str
    exercise_type: str
    prompt: str
    business_context: str | None = None
    stakeholder: str | None = None
    constraints: list[str] = []
    expected_deliverables: list[str] = []
    rubric: list[RubricCriterionSchema] = []
    choices: list[str] | None = None
    hint_count: int = 0
    follow_up_question_ids: list[str] = []
    # SQL/Python/Excel-specific starter content, populated only for the
    # matching exercise_type (mirrors ExerciseContent's own optional fields).
    dataset: str | None = None
    sql_starter_query: str | None = None
    python_starter_code: str | None = None
    excel_starter_sheets: list[ExcelSheetSchema] = []
    excel_check_cells: list[str] = []


# --- Content Admin (spec section 61) --------------------------------------------


class InterviewQuestionAdminListItemSchema(ORMSchema):
    """The admin-facing row (Content Admin) — interview questions are
    content-authored (content/interview/questions/*.yaml), so admin only
    lists/activates/deactivates, matching the existing Lesson/Exercise/Case
    admin panel convention."""

    id: str
    slug: str
    interview_type: str
    exercise_slug: str
    time_limit_seconds: int | None
    is_active: bool
    version: int


class UpdateInterviewQuestionAdminRequest(BaseModel):
    is_active: bool


class InterviewTemplateAdminListItemSchema(ORMSchema):
    id: str
    slug: str
    title: str
    target_profile: str
    section_count: int
    is_active: bool
    version: int


class UpdateInterviewTemplateAdminRequest(BaseModel):
    is_active: bool


# --- Interview templates ("company-style assessments") ----------------------


class InterviewSectionSpecSchema(BaseModel):
    interview_type: str
    title: str
    duration_minutes: int
    question_count: int
    difficulty: DifficultyLevel | None = None


class InterviewTemplateSchema(ORMSchema):
    id: str
    slug: str
    title: str
    target_profile: str
    description: str | None
    sections: list[InterviewSectionSpecSchema]
    rubric_weights: dict[str, float]
    tags: list[str]
    version: int


# --- Live interview session --------------------------------------------------


class InterviewDimensionScoreSchema(BaseModel):
    dimension: str
    score: float
    question_count: int


class InterviewScoreSchema(BaseModel):
    overall: float
    dimensions: list[InterviewDimensionScoreSchema]


class InterviewSectionSchema(ORMSchema):
    id: str
    interview_type: str
    title: str
    time_limit_seconds: int | None
    display_order: int
    started_at: datetime | None
    completed_at: datetime | None
    time_spent_seconds: int


class InterviewQuestionAttemptSchema(ORMSchema):
    id: str
    section_id: str | None
    interview_question_id: str | None
    case_attempt_id: str | None
    exercise_attempt_id: str | None
    parent_attempt_id: str | None
    is_follow_up: bool
    display_order: int
    started_at: datetime | None
    time_spent_seconds: int
    # Denormalized for the frontend's convenience — avoids a second round trip.
    question: InterviewQuestionDetail | None = None
    exercise_attempt_score: float | None = None
    case_attempt_status: str | None = None


class InterviewSchema(ORMSchema):
    id: str
    template_id: str | None
    mode: InterviewMode
    status: InterviewStatus
    title: str
    total_time_limit_seconds: int | None
    time_spent_seconds: int
    current_section_index: int
    started_at: datetime | None
    paused_at: datetime | None
    completed_at: datetime | None
    score: InterviewScoreSchema | None
    feedback: dict | None
    created_at: datetime
    sections: list[InterviewSectionSchema] = []
    question_attempts: list[InterviewQuestionAttemptSchema] = []
    current_question: InterviewQuestionAttemptSchema | None = None


class CreateInterviewRequest(BaseModel):
    mode: InterviewMode
    template_slug: str | None = None
    # For ad-hoc (non-template) practice/timed/weakness-drill sessions:
    interview_type: str | None = None
    time_limit_seconds: int | None = None
    question_count: int = 5
    # Pins a single-question PRACTICE interview to this exact question (spec
    # section 52 — practicing a specific bookmarked/reviewed question)
    # instead of letting adaptive selection choose one — takes priority over
    # every other field above when set.
    question_id: str | None = None


class AnswerInterviewQuestionRequest(BaseModel):
    """Only the field matching the current question's exercise_type is used;
    the rest are ignored — the frontend just fills in whichever applies."""

    submitted_answer: str | None = None
    rubric_selections: list[str] | None = None
    self_reported_score: float | None = None
    submitted_query: str | None = None
    submitted_code: str | None = None
    submitted_sheets: list[ExcelSheetSchema] | None = None


class AnswerInterviewQuestionResponse(BaseModel):
    interview: InterviewSchema
    is_auto_graded: bool
    score: float | None = None
    explanation: str | None = None
    correct_answer: str | None = None


# --- Spaced review ---------------------------------------------------------------


class DueReviewSchema(BaseModel):
    question_id: str
    slug: str
    title: str
    interview_type: str
    last_score: float
    days_since_last_attempt: float
    interval_days: float
    days_overdue: float
    priority: float
    reason: str


# --- Post-interview review & retry ---------------------------------------------


class InterviewTestOutcomeSchema(BaseModel):
    """One real execution check from the underlying grading engine — the SQL
    correctness/hidden-test results, the Python hidden tests, or the Excel
    check cells. Hidden tests stay hidden while an interview is live; review
    is where they're finally shown."""

    name: str
    passed: bool
    is_hidden: bool
    message: str


class InterviewQuestionReviewSchema(BaseModel):
    attempt_id: str
    display_order: int
    interview_type: str
    is_follow_up: bool
    question_slug: str | None = None
    title: str
    prompt: str | None = None
    time_limit_seconds: int | None = None
    time_spent_seconds: int = 0
    over_time: bool = False
    score: float | None = None
    passed: bool | None = None
    submitted_answer: str | None = None
    # Revealed only after the interview is finished — never mid-interview.
    correct_answer: str | None = None
    explanation: str | None = None
    solution: str | None = None
    test_outcomes: list[InterviewTestOutcomeSchema] = []
    skill_slug: str | None = None
    skill_name: str | None = None
    recommended_lesson_slug: str | None = None
    recommended_lesson_title: str | None = None
    case_attempt_id: str | None = None
    case_slug: str | None = None


class InterviewReviewResponse(BaseModel):
    interview: InterviewSchema
    questions: list[InterviewQuestionReviewSchema]


class RetryInterviewRequest(BaseModel):
    """Retries never mutate the original interview — they always create a new
    one, so every historical attempt is preserved (spec section 47)."""

    scope: str = "FULL"  # "FULL" | "SECTION" | "QUESTION"
    section_id: str | None = None
    interview_question_id: str | None = None


# --- Readiness / weaknesses / plan / history ---------------------------------


class ReadinessResponse(BaseModel):
    overall_score: float
    mastery_component: float
    recent_performance_component: float
    consistency_component: float
    breakdown: dict[str, float]
    strongest: list[str] = []
    weakest: list[str] = []


class WeaknessFindingSchema(BaseModel):
    gap_type: str
    interview_type: str
    occurrences: int
    average_score: float
    detail: str


class PlanDaySchema(BaseModel):
    day_number: int
    focus_area: str
    title: str
    task_type: str
    task_ref: str | None
    description: str


class InterviewPlanSchema(ORMSchema):
    id: str
    generated_at: datetime
    days: list[PlanDaySchema]


class ReadinessSnapshotSchema(ORMSchema):
    id: str
    computed_at: datetime
    overall_score: float
    breakdown: dict[str, float]


# --- Bookmarks / notes -------------------------------------------------------


class InterviewBookmarkSchema(ORMSchema):
    id: str
    target_type: InterviewTargetType
    target_id: str
    created_at: datetime


class CreateBookmarkRequest(BaseModel):
    target_type: InterviewTargetType
    target_id: str


class InterviewNoteSchema(ORMSchema):
    id: str
    target_type: InterviewTargetType
    target_id: str
    note: str
    created_at: datetime
    updated_at: datetime


class CreateNoteRequest(BaseModel):
    target_type: InterviewTargetType
    target_id: str
    note: str


class UpdateNoteRequest(BaseModel):
    note: str
