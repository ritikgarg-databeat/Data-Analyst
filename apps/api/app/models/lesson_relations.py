from sqlalchemy import Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LessonSkill(Base):
    """Which Skills a Lesson develops — drives skill-based filtering and mastery attribution."""

    __tablename__ = "lesson_skills"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)


class LessonDataset(Base):
    """Which Datasets a Lesson references."""

    __tablename__ = "lesson_datasets"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True)


class LessonPrerequisite(Base):
    """A prerequisite relationship between two Lessons.

    `is_hard_blocker=True` locks the lesson in the UI until the prerequisite
    is COMPLETED; `False` surfaces it as a "recommended first" suggestion
    without blocking access. See app.services.prerequisites.
    """

    __tablename__ = "lesson_prerequisites"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    prerequisite_lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    is_hard_blocker: Mapped[bool] = mapped_column(Boolean, default=True)


class ModulePrerequisite(Base):
    """A prerequisite relationship between two Modules (always a hard blocker)."""

    __tablename__ = "module_prerequisites"

    module_id: Mapped[str] = mapped_column(ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True)
    prerequisite_module_id: Mapped[str] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"), primary_key=True
    )


class RelatedLesson(Base):
    """A "see also" relationship between two Lessons. Directional in storage,
    queried symmetrically by app.services.related_content."""

    __tablename__ = "related_lessons"

    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    related_lesson_id: Mapped[str] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
