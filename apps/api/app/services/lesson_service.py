from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.loader import load_lesson_file
from app.content.schema import LessonContentFile
from app.core.errors import NotFoundError
from app.models.dataset import Dataset
from app.models.enums import LessonProgressStatus
from app.models.exercise import Exercise
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.lesson_relations import LessonDataset, LessonSkill, RelatedLesson
from app.models.skill import Skill
from app.models.tag import LessonTag, Tag
from app.repositories.lesson import LessonRepository
from app.repositories.module import ModuleRepository
from app.schemas.content import CompletionCriteriaOut, LessonContentResponse, LessonPrerequisiteRef
from app.schemas.dataset import Dataset as DatasetSchema
from app.schemas.lesson import Lesson as LessonSchema
from app.schemas.lesson import UpdateLessonAdminRequest
from app.schemas.progress import LessonProgress as LessonProgressSchema
from app.schemas.skill import Skill as SkillSchema
from app.schemas.tag import Tag as TagSchema
from app.services.completion_rules import get_criteria
from app.services.prerequisites import PrerequisiteService


class LessonService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = LessonRepository(db)
        self.module_repo = ModuleRepository(db)
        self.prereq_service = PrerequisiteService(db)

    def _tags(self, lesson_id: str) -> list[TagSchema]:
        stmt = select(Tag).join(LessonTag, LessonTag.tag_id == Tag.id).where(LessonTag.lesson_id == lesson_id)
        return [TagSchema.model_validate(t) for t in self.db.execute(stmt).scalars().all()]

    def _skills(self, lesson_id: str) -> list[SkillSchema]:
        stmt = (
            select(Skill)
            .join(LessonSkill, LessonSkill.skill_id == Skill.id)
            .where(LessonSkill.lesson_id == lesson_id)
        )
        return [SkillSchema.model_validate(s) for s in self.db.execute(stmt).scalars().all()]

    def to_schema(self, lesson: Lesson) -> LessonSchema:
        return LessonSchema(
            id=lesson.id,
            module_id=lesson.module_id,
            module_slug=lesson.module.slug,
            domain_slug=lesson.module.domain.slug,
            slug=lesson.slug,
            title=lesson.title,
            description=lesson.description,
            content_type=lesson.content_type,
            difficulty=lesson.difficulty,
            estimated_minutes=lesson.estimated_minutes,
            display_order=lesson.display_order,
            content_reference=lesson.content_reference,
            is_active=lesson.is_active,
            tags=self._tags(lesson.id),
            skills=self._skills(lesson.id),
            created_at=lesson.created_at,
            updated_at=lesson.updated_at,
        )

    def list_by_module_slug(self, module_slug: str) -> list[LessonSchema]:
        module = self.module_repo.get_by_slug(module_slug)
        if module is None:
            raise NotFoundError(f"Module '{module_slug}' was not found.", details={"slug": module_slug})
        return [self.to_schema(lesson) for lesson in self.repo.list_by_module(module.id)]

    def get_by_slug(self, slug: str) -> LessonSchema:
        return self.to_schema(self.get_model_by_slug(slug))

    def get_model_by_slug(self, slug: str) -> Lesson:
        lesson = self.repo.get_by_slug(slug)
        if lesson is None:
            raise NotFoundError(f"Lesson '{slug}' was not found.", details={"slug": slug})
        return lesson

    def update_admin(self, lesson_id: str, payload: UpdateLessonAdminRequest) -> LessonSchema:
        lesson = self.repo.get_by_id(lesson_id)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_id}' was not found.")
        if payload.is_active is not None:
            lesson.is_active = payload.is_active
        if payload.display_order is not None:
            lesson.display_order = payload.display_order
        self.db.commit()
        self.db.refresh(lesson)
        return self.to_schema(lesson)

    def _load_content_file(self, lesson: Lesson) -> LessonContentFile:
        if not lesson.content_reference:
            raise NotFoundError(f"Lesson '{lesson.slug}' has no content file.")
        return load_lesson_file(lesson.content_reference)

    def _get_or_create_progress(self, user_id: str, lesson_id: str) -> LessonProgress:
        progress = self.db.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = LessonProgress(
                user_id=user_id, lesson_id=lesson_id, status=LessonProgressStatus.NOT_STARTED
            )
            self.db.add(progress)
            self.db.flush()
        return progress

    def get_content(self, slug: str, user_id: str) -> LessonContentResponse:
        lesson = self.get_model_by_slug(slug)
        content = self._load_content_file(lesson)
        progress = self._get_or_create_progress(user_id, lesson.id)
        is_locked = self.prereq_service.is_locked(user_id, lesson.id)

        prereq_statuses = self.prereq_service.get_prerequisite_statuses(user_id, lesson.id)
        prerequisites = [
            LessonPrerequisiteRef(
                lesson=self.to_schema(s.prerequisite_lesson),
                is_hard_blocker=s.is_hard_blocker,
                is_completed=s.is_completed,
            )
            for s in prereq_statuses
        ]

        exercises = (
            self.db.execute(
                select(Exercise).where(Exercise.lesson_id == lesson.id, Exercise.is_active.is_(True))
            )
            .scalars()
            .all()
        )
        from app.services.exercise_service import ExerciseService

        exercise_service = ExerciseService(self.db)
        exercise_schemas = [exercise_service.to_schema(e) for e in exercises]

        datasets = (
            self.db.execute(
                select(Dataset)
                .join(LessonDataset, LessonDataset.dataset_id == Dataset.id)
                .where(LessonDataset.lesson_id == lesson.id)
            )
            .scalars()
            .all()
        )

        related = (
            self.db.execute(
                select(Lesson)
                .join(RelatedLesson, RelatedLesson.related_lesson_id == Lesson.id)
                .where(RelatedLesson.lesson_id == lesson.id)
            )
            .scalars()
            .all()
        )

        siblings = self.repo.list_by_module(lesson.module_id)
        idx = next((i for i, sib in enumerate(siblings) if sib.id == lesson.id), None)
        previous_lesson = self.to_schema(siblings[idx - 1]) if idx is not None and idx > 0 else None
        next_lesson = (
            self.to_schema(siblings[idx + 1]) if idx is not None and idx + 1 < len(siblings) else None
        )

        criteria = get_criteria(lesson)

        return LessonContentResponse(
            lesson=self.to_schema(lesson),
            progress=LessonProgressSchema.model_validate(progress),
            is_locked=is_locked,
            prerequisites=prerequisites,
            objectives=content.objectives,
            key_takeaways=content.key_takeaways,
            common_mistakes=content.common_mistakes,
            practical_applications=content.practical_applications,
            interview_questions=content.interview_questions,
            resources=content.resources,
            blocks=content.blocks,
            exercises=exercise_schemas,
            datasets=[DatasetSchema.model_validate(d) for d in datasets],
            related_lessons=[self.to_schema(r) for r in related],
            completion_criteria=CompletionCriteriaOut(
                type=str(criteria["type"]), threshold=float(criteria["threshold"])
            ),  # type: ignore[arg-type]
            previous_lesson=previous_lesson,
            next_lesson=next_lesson,
        )
