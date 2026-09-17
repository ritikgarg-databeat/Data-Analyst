from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.domain import Domain
from app.models.enums import LessonProgressStatus
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.module import Module
from app.repositories.domain import DomainRepository
from app.schemas.domain import CreateDomainRequest, UpdateDomainRequest
from app.schemas.domain import Domain as DomainSchema


class DomainService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = DomainRepository(db)

    def _progress_percent(self, domain_id: str, user_id: str) -> float:
        total = self.db.execute(
            select(func.count())
            .select_from(Lesson)
            .join(Module, Module.id == Lesson.module_id)
            .where(Module.domain_id == domain_id, Lesson.is_active.is_(True))
        ).scalar_one()
        if total == 0:
            return 0.0
        completed = self.db.execute(
            select(func.count())
            .select_from(LessonProgress)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .join(Module, Module.id == Lesson.module_id)
            .where(
                Module.domain_id == domain_id,
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.COMPLETED,
            )
        ).scalar_one()
        return round(100 * completed / total, 1)

    def _to_schema(self, domain: Domain, user_id: str | None = None) -> DomainSchema:
        return DomainSchema(
            id=domain.id,
            slug=domain.slug,
            name=domain.name,
            description=domain.description,
            display_order=domain.display_order,
            icon=domain.icon,
            is_active=domain.is_active,
            module_count=self.repo.module_count(domain.id),
            progress_percent=self._progress_percent(domain.id, user_id) if user_id else 0.0,
            created_at=domain.created_at,
            updated_at=domain.updated_at,
        )

    def list_domains(self, user_id: str | None = None) -> list[DomainSchema]:
        return [self._to_schema(d, user_id) for d in self.repo.list_all()]

    def get_by_slug(self, slug: str, user_id: str | None = None) -> DomainSchema:
        return self._to_schema(self.get_model_by_slug(slug), user_id)

    def get_model_by_slug(self, slug: str) -> Domain:
        domain = self.repo.get_by_slug(slug)
        if domain is None:
            raise NotFoundError(f"Domain '{slug}' was not found.", details={"slug": slug})
        return domain

    def create(self, payload: CreateDomainRequest) -> DomainSchema:
        if self.repo.get_by_slug(payload.slug) is not None:
            raise ConflictError(f"Domain '{payload.slug}' already exists.")
        domain = Domain(
            slug=payload.slug,
            name=payload.name,
            description=payload.description,
            icon=payload.icon,
            display_order=payload.display_order,
        )
        self.db.add(domain)
        self.db.commit()
        self.db.refresh(domain)
        return self._to_schema(domain)

    def update(self, domain_id: str, payload: UpdateDomainRequest) -> DomainSchema:
        domain = self.repo.get_by_id(domain_id)
        if domain is None:
            raise NotFoundError(f"Domain '{domain_id}' was not found.")
        for field in ("slug", "name", "description", "icon", "display_order", "is_active"):
            value = getattr(payload, field)
            if value is not None:
                setattr(domain, field, value)
        self.db.commit()
        self.db.refresh(domain)
        return self._to_schema(domain)
