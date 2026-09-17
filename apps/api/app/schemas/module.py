from datetime import datetime

from app.models.enums import DifficultyLevel
from app.schemas.common import ORMSchema


class Module(ORMSchema):
    id: str
    domain_id: str
    domain_slug: str
    slug: str
    title: str
    description: str | None = None
    difficulty: DifficultyLevel
    estimated_minutes: int
    display_order: int
    is_active: bool
    lesson_count: int = 0
    progress_percent: float = 0.0
    has_assessment: bool = False
    created_at: datetime
    updated_at: datetime


class CreateModuleRequest(ORMSchema):
    domain_id: str
    slug: str
    title: str
    description: str | None = None
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_minutes: int = 15
    display_order: int = 0


class UpdateModuleRequest(ORMSchema):
    domain_id: str | None = None
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    difficulty: DifficultyLevel | None = None
    estimated_minutes: int | None = None
    display_order: int | None = None
    is_active: bool | None = None
