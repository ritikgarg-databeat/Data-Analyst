from datetime import datetime

from app.models.enums import DifficultyLevel, LessonContentType, LessonProgressStatus
from app.schemas.common import ORMSchema
from app.schemas.skill import Skill
from app.schemas.tag import Tag


class Lesson(ORMSchema):
    id: str
    module_id: str
    module_slug: str
    domain_slug: str
    slug: str
    title: str
    description: str | None = None
    content_type: LessonContentType
    difficulty: DifficultyLevel
    estimated_minutes: int
    display_order: int
    content_reference: str | None = None
    is_active: bool
    tags: list[Tag] = []
    skills: list[Skill] = []
    created_at: datetime
    updated_at: datetime


class LessonWithProgress(Lesson):
    status: LessonProgressStatus
    progress_percent: float
    is_locked: bool


class UpdateLessonAdminRequest(ORMSchema):
    """Lessons are content-file-owned — admin can only reorder/activate, not edit body content."""

    is_active: bool | None = None
    display_order: int | None = None
