from datetime import datetime

from pydantic import BaseModel

from app.models.enums import AssessmentAttemptStatus, AssessmentRetryPolicy
from app.schemas.common import ORMSchema
from app.schemas.exercise import ExerciseContent


class Assessment(ORMSchema):
    id: str
    module_id: str
    module_slug: str
    slug: str
    title: str
    description: str | None = None
    time_limit_minutes: int | None = None
    passing_score: float
    retry_policy: AssessmentRetryPolicy
    max_attempts: int | None = None
    question_count: int = 0
    is_active: bool


class AssessmentAttempt(ORMSchema):
    id: str
    user_id: str
    assessment_id: str
    status: AssessmentAttemptStatus
    score: float | None = None
    time_spent_seconds: int
    started_at: datetime
    completed_at: datetime | None = None


class StartAssessmentResponse(BaseModel):
    attempt: AssessmentAttempt
    questions: list[ExerciseContent]


class AssessmentAnswerSubmission(BaseModel):
    exercise_id: str
    submitted_answer: str


class SubmitAssessmentRequest(BaseModel):
    answers: list[AssessmentAnswerSubmission]
    time_spent_seconds: int = 0


class AssessmentAnswerResult(BaseModel):
    exercise_id: str
    is_correct: bool | None
    score: float | None
    correct_answer: str | None
    explanation: str


class SubmitAssessmentResponse(BaseModel):
    attempt: AssessmentAttempt
    passed: bool
    answers: list[AssessmentAnswerResult]
