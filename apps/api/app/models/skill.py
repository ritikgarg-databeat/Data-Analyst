from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DifficultyLevel, SkillCategory


class Skill(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A discrete, measurable skill (e.g. "Advanced SQL") tracked per user via UserSkill."""

    __tablename__ = "skills"

    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[SkillCategory] = mapped_column(Enum(SkillCategory, native_enum=False, length=30))
    target_level: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=20), default=DifficultyLevel.INTERMEDIATE
    )
