from sqlalchemy import select

from app.models.enums import LessonProgressStatus
from app.models.lesson_progress import LessonProgress
from app.repositories.base import BaseRepository


class LessonProgressRepository(BaseRepository[LessonProgress]):
    model = LessonProgress

    def list_for_user(self, user_id: str) -> list[LessonProgress]:
        stmt = select(LessonProgress).where(LessonProgress.user_id == user_id)
        return list(self.db.execute(stmt).scalars().all())

    def get(self, user_id: str, lesson_id: str) -> LessonProgress | None:
        stmt = select(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_in_progress(self, user_id: str, limit: int = 5) -> list[LessonProgress]:
        stmt = (
            select(LessonProgress)
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.IN_PROGRESS,
            )
            .order_by(LessonProgress.last_accessed_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
