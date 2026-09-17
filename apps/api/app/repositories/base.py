from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base


class BaseRepository[ModelType: Base]:
    """Thin data-access layer around a single SQLAlchemy model.

    Kept intentionally minimal for Phase 1 — just the operations the current
    services need. Extend per-repository rather than growing this god class.
    """

    model: type[ModelType]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, id_: str) -> ModelType | None:
        return self.db.get(self.model, id_)

    def get_by_slug(self, slug: str) -> ModelType | None:
        stmt = select(self.model).where(self.model.slug == slug)  # type: ignore[attr-defined]
        return self.db.execute(stmt).scalar_one_or_none()

    def list_all(self, *, active_only: bool = True) -> list[ModelType]:
        stmt = select(self.model)
        if active_only and hasattr(self.model, "is_active"):
            stmt = stmt.where(self.model.is_active.is_(True))  # type: ignore[attr-defined]
        if hasattr(self.model, "display_order"):
            stmt = stmt.order_by(self.model.display_order)  # type: ignore[attr-defined]
        return list(self.db.execute(stmt).scalars().all())

    def add(self, instance: ModelType) -> ModelType:
        self.db.add(instance)
        self.db.flush()
        return instance
