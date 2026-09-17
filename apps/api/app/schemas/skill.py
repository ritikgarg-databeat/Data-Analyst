from datetime import datetime

from app.models.enums import DifficultyLevel, MasteryLevel, SkillCategory
from app.schemas.common import ORMSchema


class Skill(ORMSchema):
    id: str
    slug: str
    name: str
    description: str | None = None
    category: SkillCategory
    target_level: DifficultyLevel
    created_at: datetime
    updated_at: datetime


class UserSkill(ORMSchema):
    user_id: str
    skill_id: str
    skill: Skill
    mastery_score: float
    mastery_level: MasteryLevel
    confidence_score: float
    questions_attempted: int
    questions_correct: int
    last_practiced_at: datetime | None = None
    updated_at: datetime


class CreateSkillRequest(ORMSchema):
    slug: str
    name: str
    description: str | None = None
    category: SkillCategory
    target_level: DifficultyLevel = DifficultyLevel.INTERMEDIATE


class UpdateSkillRequest(ORMSchema):
    slug: str | None = None
    name: str | None = None
    description: str | None = None
    category: SkillCategory | None = None
    target_level: DifficultyLevel | None = None
