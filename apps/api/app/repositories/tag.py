from sqlalchemy import select

from app.models.tag import Tag
from app.repositories.base import BaseRepository


class TagRepository(BaseRepository[Tag]):
    model = Tag

    def list_all(self, *, active_only: bool = True) -> list[Tag]:  # noqa: ARG002
        return list(self.db.execute(select(Tag).order_by(Tag.name)).scalars().all())
