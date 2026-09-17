from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DifficultyLevel, ExerciseAttemptStatus, ExerciseType
from app.schemas.common import ORMSchema
from app.schemas.tag import Tag


class RubricCriterionSchema(BaseModel):
    """One self-assessed evaluation criterion (spec section 46 "Case
    Evaluation") — shown to the learner up front (it's guidance on what a
    strong answer covers, not the answer itself), checked off after they
    submit their own free-text answer to compute a real, non-self-reported
    score. See app.services.grading.grade()."""

    criterion: str
    points: int


class Exercise(ORMSchema):
    id: str
    lesson_id: str | None = None
    skill_id: str | None = None
    skill_slug: str | None = None
    dataset_id: str | None = None
    dataset_slug: str | None = None
    slug: str
    title: str
    description: str | None = None
    exercise_type: ExerciseType
    difficulty: DifficultyLevel
    points: int
    display_order: int
    content_reference: str | None = None
    is_active: bool
    tags: list[Tag] = []


class ExerciseAttempt(ORMSchema):
    id: str
    user_id: str
    exercise_id: str
    status: ExerciseAttemptStatus
    score: float | None = None
    submitted_answer: str | None = None
    hints_used: int
    solution_revealed: bool
    execution_time_ms: int | None = None
    attempted_at: datetime


class ExerciseContent(Exercise):
    """Exercise content for attempting — never includes correct_answer/solution."""

    prompt: str
    choices: list[str] | None = None
    hint_count: int
    best_attempt: ExerciseAttempt | None = None
    attempt_count: int = 0
    # Phase 6: case-framing + rubric fields, populated only for case-study
    # exercises (rubric is shown up front — it's evaluation guidance, not
    # the answer, so it's safe to surface before submission).
    business_context: str | None = None
    stakeholder: str | None = None
    constraints: list[str] = []
    expected_deliverables: list[str] = []
    rubric: list[RubricCriterionSchema] = []


class SubmitExerciseAttemptRequest(BaseModel):
    submitted_answer: str
    self_reported_score: float | None = None
    # Phase 6: which rubric criteria (by `criterion` string) the learner
    # self-assessed their own answer as satisfying — only meaningful for
    # exercises whose content file defines a `rubric`.
    rubric_selections: list[str] | None = None


class SubmitExerciseAttemptResponse(BaseModel):
    attempt: ExerciseAttempt
    is_auto_graded: bool
    explanation: str | None = None
    correct_answer: str | None = None


class RevealHintResponse(BaseModel):
    hint_index: int
    hint: str
    hints_remaining: int


class RevealSolutionResponse(BaseModel):
    solution: str | None = None
    explanation: str


class UpdateExerciseAdminRequest(BaseModel):
    """Exercises are content-file-owned — admin can only reorder/activate, not edit body content."""

    is_active: bool | None = None
    display_order: int | None = None
