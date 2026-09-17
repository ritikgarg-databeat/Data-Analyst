from sqlalchemy import func, select

from app.models.lesson import Lesson
from app.models.module import Module
from app.repositories.base import BaseRepository


class ModuleRepository(BaseRepository[Module]):
    model = Module

    def list_by_domain(self, domain_id: str) -> list[Module]:
        stmt = (
            select(Module)
            .where(Module.domain_id == domain_id, Module.is_active.is_(True))
            .order_by(Module.display_order)
        )
        return list(self.db.execute(stmt).scalars().all())

    def lesson_count(self, module_id: str) -> int:
        stmt = select(func.count()).select_from(Lesson).where(Lesson.module_id == module_id)
        return self.db.execute(stmt).scalar_one()
