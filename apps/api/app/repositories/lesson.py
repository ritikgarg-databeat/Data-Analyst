from sqlalchemy import select

from app.models.lesson import Lesson
from app.repositories.base import BaseRepository


class LessonRepository(BaseRepository[Lesson]):
    model = Lesson

    def list_by_module(self, module_id: str) -> list[Lesson]:
        stmt = (
            select(Lesson)
            .where(Lesson.module_id == module_id, Lesson.is_active.is_(True))
            .order_by(Lesson.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())
