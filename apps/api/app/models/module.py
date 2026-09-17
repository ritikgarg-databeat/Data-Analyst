from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import DifficultyLevel


class Module(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A module groups related lessons within a Domain."""

    __tablename__ = "modules"

    domain_id: Mapped[str] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), index=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        Enum(DifficultyLevel, native_enum=False, length=20), default=DifficultyLevel.BEGINNER
    )
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    domain: Mapped["Domain"] = relationship(back_populates="modules")  # noqa: F821
    lessons: Mapped[list["Lesson"]] = relationship(  # noqa: F821
        back_populates="module", cascade="all, delete-orphan", order_by="Lesson.display_order"
    )
