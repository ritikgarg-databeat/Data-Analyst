from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.tag import Tag
from app.repositories.tag import TagRepository
from app.schemas.tag import CreateTagRequest, UpdateTagRequest


class TagService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TagRepository(db)

    def list_tags(self) -> list[Tag]:
        return self.repo.list_all()

    def create(self, payload: CreateTagRequest) -> Tag:
        if self.repo.get_by_slug(payload.slug) is not None:
            raise ConflictError(f"Tag '{payload.slug}' already exists.")
        tag = Tag(slug=payload.slug, name=payload.name)
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def update(self, tag_id: str, payload: UpdateTagRequest) -> Tag:
        tag = self.repo.get_by_id(tag_id)
        if tag is None:
            raise NotFoundError(f"Tag '{tag_id}' was not found.")
        if payload.slug is not None:
            tag.slug = payload.slug
        if payload.name is not None:
            tag.name = payload.name
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def delete(self, tag_id: str) -> None:
        tag = self.repo.get_by_id(tag_id)
        if tag is None:
            raise NotFoundError(f"Tag '{tag_id}' was not found.")
        self.db.delete(tag)
        self.db.commit()
