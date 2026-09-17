from pydantic import BaseModel

from app.content.schema import ContentBlock, InterviewQuestionRef, ResourceRef
from app.schemas.dataset import Dataset
from app.schemas.exercise import Exercise
from app.schemas.lesson import Lesson
from app.schemas.progress import LessonProgress


class LessonPrerequisiteRef(BaseModel):
    lesson: Lesson
    is_hard_blocker: bool
    is_completed: bool


class CompletionCriteriaOut(BaseModel):
    type: str
    threshold: float


class LessonContentResponse(BaseModel):
    lesson: Lesson
    progress: LessonProgress
    is_locked: bool
    prerequisites: list[LessonPrerequisiteRef]
    objectives: list[str]
    key_takeaways: list[str]
    common_mistakes: list[str]
    practical_applications: list[str]
    interview_questions: list[InterviewQuestionRef]
    resources: list[ResourceRef]
    blocks: list[ContentBlock]
    exercises: list[Exercise]
    datasets: list[Dataset]
    related_lessons: list[Lesson]
    completion_criteria: CompletionCriteriaOut
    previous_lesson: Lesson | None = None
    next_lesson: Lesson | None = None
