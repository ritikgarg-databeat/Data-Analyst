from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.enums import DifficultyLevel, LessonProgressStatus, SkillCategory
from app.schemas.common import ORMSchema
from app.schemas.lesson import Lesson
from app.schemas.skill import Skill


class LessonProgress(ORMSchema):
    user_id: str
    lesson_id: str
    status: LessonProgressStatus
    progress_percent: float
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_accessed_at: datetime | None = None
    time_spent_seconds: int = 0
    last_position: str | None = None
    exercises_completed: int = 0


class UpsertLessonProgressRequest(BaseModel):
    status: LessonProgressStatus
    progress_percent: float = Field(ge=0, le=100)


class UpdateLessonPositionRequest(BaseModel):
    last_position: str | None = None
    time_spent_delta_seconds: int = Field(default=0, ge=0)


class ContinueLearningItem(BaseModel):
    lesson: Lesson
    module_title: str
    domain_slug: str
    domain_name: str
    progress_percent: float


class RecentlyCompletedItem(BaseModel):
    lesson: Lesson
    completed_at: datetime


class WeakArea(BaseModel):
    skill: Skill
    mastery_score: float
    reason: str


class ActivityDay(BaseModel):
    date: date
    lessons_progressed: int
    exercises_attempted: int


class SkillCategoryOverview(BaseModel):
    category: SkillCategory
    label: str
    skill_count: int
    average_mastery: float


class ProgressSummary(BaseModel):
    overall_progress_percent: float
    current_level: DifficultyLevel
    learning_streak_days: int
    skills_mastered: int
    total_skills: int
    continue_learning: list[ContinueLearningItem]
    recently_completed: list[RecentlyCompletedItem]
    weak_areas: list[WeakArea]
    activity: list[ActivityDay]
    skill_overview: list[SkillCategoryOverview]
