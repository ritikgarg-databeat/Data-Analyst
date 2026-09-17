from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.assessment import Assessment
from app.models.enums import LessonProgressStatus
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.module import Module
from app.repositories.domain import DomainRepository
from app.repositories.module import ModuleRepository
from app.schemas.module import CreateModuleRequest, UpdateModuleRequest
from app.schemas.module import Module as ModuleSchema


class ModuleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ModuleRepository(db)
        self.domain_repo = DomainRepository(db)

    def _progress_percent(self, module_id: str, user_id: str) -> float:
        total = self.db.execute(
            select(func.count())
            .select_from(Lesson)
            .where(Lesson.module_id == module_id, Lesson.is_active.is_(True))
        ).scalar_one()
        if total == 0:
            return 0.0
        completed = self.db.execute(
            select(func.count())
            .select_from(LessonProgress)
            .join(Lesson, Lesson.id == LessonProgress.lesson_id)
            .where(
                Lesson.module_id == module_id,
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.COMPLETED,
            )
        ).scalar_one()
        return round(100 * completed / total, 1)

    def _has_assessment(self, module_id: str) -> bool:
        return (
            self.db.execute(
                select(func.count())
                .select_from(Assessment)
                .where(Assessment.module_id == module_id, Assessment.is_active.is_(True))
            ).scalar_one()
            > 0
        )

    def _to_schema(self, module: Module, user_id: str | None = None) -> ModuleSchema:
        return ModuleSchema(
            id=module.id,
            domain_id=module.domain_id,
            domain_slug=module.domain.slug,
            slug=module.slug,
            title=module.title,
            description=module.description,
            difficulty=module.difficulty,
            estimated_minutes=module.estimated_minutes,
            display_order=module.display_order,
            is_active=module.is_active,
            lesson_count=self.repo.lesson_count(module.id),
            progress_percent=self._progress_percent(module.id, user_id) if user_id else 0.0,
            has_assessment=self._has_assessment(module.id),
            created_at=module.created_at,
            updated_at=module.updated_at,
        )

    def list_by_domain_slug(self, domain_slug: str, user_id: str | None = None) -> list[ModuleSchema]:
        domain = self.domain_repo.get_by_slug(domain_slug)
        if domain is None:
            raise NotFoundError(f"Domain '{domain_slug}' was not found.", details={"slug": domain_slug})
        return [self._to_schema(m, user_id) for m in self.repo.list_by_domain(domain.id)]

    def get_by_slug(self, slug: str, user_id: str | None = None) -> ModuleSchema:
        return self._to_schema(self.get_model_by_slug(slug), user_id)

    def get_model_by_slug(self, slug: str) -> Module:
        module = self.repo.get_by_slug(slug)
        if module is None:
            raise NotFoundError(f"Module '{slug}' was not found.", details={"slug": slug})
        return module

    def create(self, payload: CreateModuleRequest) -> ModuleSchema:
        if self.repo.get_by_slug(payload.slug) is not None:
            raise ConflictError(f"Module '{payload.slug}' already exists.")
        if self.domain_repo.get_by_id(payload.domain_id) is None:
            raise NotFoundError(f"Domain '{payload.domain_id}' was not found.")
        module = Module(
            domain_id=payload.domain_id,
            slug=payload.slug,
            title=payload.title,
            description=payload.description,
            difficulty=payload.difficulty,
            estimated_minutes=payload.estimated_minutes,
            display_order=payload.display_order,
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)
        return self._to_schema(module)

    def update(self, module_id: str, payload: UpdateModuleRequest) -> ModuleSchema:
        module = self.repo.get_by_id(module_id)
        if module is None:
            raise NotFoundError(f"Module '{module_id}' was not found.")
        for field in (
            "domain_id",
            "slug",
            "title",
            "description",
            "difficulty",
            "estimated_minutes",
            "display_order",
            "is_active",
        ):
            value = getattr(payload, field)
            if value is not None:
                setattr(module, field, value)
        self.db.commit()
        self.db.refresh(module)
        return self._to_schema(module)
