from sqlalchemy import func, select

from app.models.domain import Domain
from app.models.module import Module
from app.repositories.base import BaseRepository


class DomainRepository(BaseRepository[Domain]):
    model = Domain

    def module_count(self, domain_id: str) -> int:
        stmt = select(func.count()).select_from(Module).where(Module.domain_id == domain_id)
        return self.db.execute(stmt).scalar_one()
