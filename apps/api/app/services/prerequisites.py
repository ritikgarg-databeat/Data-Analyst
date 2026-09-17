from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import LessonProgressStatus
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.lesson_relations import LessonPrerequisite


@dataclass
class PrerequisiteStatus:
    prerequisite_lesson: Lesson
    is_hard_blocker: bool
    is_completed: bool


class PrerequisiteService:
    """Hard blockers lock a lesson in the UI until completed; soft ones are
    surfaced as "recommended first" without blocking access."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_prerequisite_statuses(self, user_id: str, lesson_id: str) -> list[PrerequisiteStatus]:
        stmt = (
            select(LessonPrerequisite, Lesson)
            .join(Lesson, Lesson.id == LessonPrerequisite.prerequisite_lesson_id)
            .where(LessonPrerequisite.lesson_id == lesson_id)
        )
        rows = self.db.execute(stmt).all()

        statuses: list[PrerequisiteStatus] = []
        for prereq, prereq_lesson in rows:
            progress = self.db.execute(
                select(LessonProgress).where(
                    LessonProgress.user_id == user_id, LessonProgress.lesson_id == prereq_lesson.id
                )
            ).scalar_one_or_none()
            is_completed = progress is not None and progress.status == LessonProgressStatus.COMPLETED
            statuses.append(
                PrerequisiteStatus(
                    prerequisite_lesson=prereq_lesson,
                    is_hard_blocker=prereq.is_hard_blocker,
                    is_completed=is_completed,
                )
            )
        return statuses

    def is_locked(self, user_id: str, lesson_id: str) -> bool:
        statuses = self.get_prerequisite_statuses(user_id, lesson_id)
        return any(s.is_hard_blocker and not s.is_completed for s in statuses)
