from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.loader import load_exercise_file
from app.content.schema import ExerciseContentFile
from app.core.errors import AppError, NotFoundError
from app.models.dataset import Dataset
from app.models.enums import ExerciseAttemptStatus
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.lesson_progress import LessonProgress
from app.models.skill import Skill
from app.models.tag import ExerciseTag, Tag
from app.repositories.exercise import ExerciseRepository
from app.schemas.exercise import (
    Exercise as ExerciseSchema,
)
from app.schemas.exercise import (
    ExerciseAttempt as ExerciseAttemptSchema,
)
from app.schemas.exercise import (
    ExerciseContent as ExerciseContentSchema,
)
from app.schemas.exercise import (
    RevealHintResponse,
    RevealSolutionResponse,
    RubricCriterionSchema,
    SubmitExerciseAttemptRequest,
    SubmitExerciseAttemptResponse,
    UpdateExerciseAdminRequest,
)
from app.schemas.tag import Tag as TagSchema
from app.services.grading import grade
from app.services.mastery import MasteryService


class ExerciseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExerciseRepository(db)
        self.mastery_service = MasteryService(db)

    def _tags(self, exercise_id: str) -> list[TagSchema]:
        stmt = (
            select(Tag)
            .join(ExerciseTag, ExerciseTag.tag_id == Tag.id)
            .where(ExerciseTag.exercise_id == exercise_id)
        )
        return [TagSchema.model_validate(t) for t in self.db.execute(stmt).scalars().all()]

    def to_schema(self, exercise: Exercise) -> ExerciseSchema:
        skill_slug = None
        if exercise.skill_id:
            skill = self.db.get(Skill, exercise.skill_id)
            skill_slug = skill.slug if skill else None
        dataset_slug = None
        if exercise.dataset_id:
            dataset = self.db.get(Dataset, exercise.dataset_id)
            dataset_slug = dataset.slug if dataset else None

        return ExerciseSchema(
            id=exercise.id,
            lesson_id=exercise.lesson_id,
            skill_id=exercise.skill_id,
            skill_slug=skill_slug,
            dataset_id=exercise.dataset_id,
            dataset_slug=dataset_slug,
            slug=exercise.slug,
            title=exercise.title,
            description=exercise.description,
            exercise_type=exercise.exercise_type,
            difficulty=exercise.difficulty,
            points=exercise.points,
            display_order=exercise.display_order,
            content_reference=exercise.content_reference,
            is_active=exercise.is_active,
            tags=self._tags(exercise.id),
        )

    def list_exercises(self) -> list[ExerciseSchema]:
        return [self.to_schema(e) for e in self.repo.list_all(active_only=False)]

    def get_model_by_slug(self, slug: str) -> Exercise:
        exercise = self.repo.get_by_slug(slug)
        if exercise is None:
            raise NotFoundError(f"Exercise '{slug}' was not found.", details={"slug": slug})
        return exercise

    def get_by_slug(self, slug: str) -> ExerciseSchema:
        return self.to_schema(self.get_model_by_slug(slug))

    def _load_content(self, exercise: Exercise) -> ExerciseContentFile:
        if not exercise.content_reference:
            raise NotFoundError(f"Exercise '{exercise.slug}' has no content file.")
        return load_exercise_file(exercise.content_reference)

    def _attempts_for(self, user_id: str, exercise_id: str) -> list[ExerciseAttempt]:
        stmt = (
            select(ExerciseAttempt)
            .where(ExerciseAttempt.user_id == user_id, ExerciseAttempt.exercise_id == exercise_id)
            .order_by(ExerciseAttempt.attempted_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def get_content(self, slug: str, user_id: str) -> ExerciseContentSchema:
        exercise = self.get_model_by_slug(slug)
        content = self._load_content(exercise)
        attempts = self._attempts_for(user_id, exercise.id)
        best = max(attempts, key=lambda a: a.score or 0, default=None)

        base = self.to_schema(exercise)
        return ExerciseContentSchema(
            **base.model_dump(),
            prompt=content.prompt,
            choices=content.choices,
            hint_count=len(content.hints),
            best_attempt=ExerciseAttemptSchema.model_validate(best) if best else None,
            attempt_count=len(attempts),
            business_context=content.business_context,
            stakeholder=content.stakeholder,
            constraints=content.constraints,
            expected_deliverables=content.expected_deliverables,
            rubric=[
                RubricCriterionSchema(criterion=c.criterion, points=c.points) for c in content.rubric
            ],
        )

    def submit_attempt(
        self, user_id: str, slug: str, payload: SubmitExerciseAttemptRequest
    ) -> SubmitExerciseAttemptResponse:
        exercise = self.get_model_by_slug(slug)
        content = self._load_content(exercise)
        had_passed_before = any(
            a.status == ExerciseAttemptStatus.PASSED for a in self._attempts_for(user_id, exercise.id)
        )

        result = grade(content, payload.submitted_answer, payload.rubric_selections)
        if result.is_auto_graded:
            status = ExerciseAttemptStatus.PASSED if result.is_correct else ExerciseAttemptStatus.FAILED
            score = result.score
        else:
            status = ExerciseAttemptStatus.SUBMITTED
            score = payload.self_reported_score

        # Reuse a PENDING attempt (created by reveal_hint/reveal_solution) so the
        # hints_used/solution_revealed already recorded on it carry through to
        # the graded attempt, rather than being lost on a fresh row.
        pending = self._latest_attempt(user_id, exercise.id)
        if pending is not None and pending.status == ExerciseAttemptStatus.PENDING:
            attempt = pending
            attempt.attempted_at = datetime.now(UTC)
        else:
            attempt = ExerciseAttempt(
                user_id=user_id, exercise_id=exercise.id, attempted_at=datetime.now(UTC)
            )
            self.db.add(attempt)

        attempt.status = status
        attempt.score = score
        attempt.submitted_answer = payload.submitted_answer
        self.db.flush()

        if exercise.skill_id and score is not None:
            self.mastery_service.recalculate(user_id, exercise.skill_id)

        if status == ExerciseAttemptStatus.PASSED and not had_passed_before and exercise.lesson_id:
            progress = self.db.execute(
                select(LessonProgress).where(
                    LessonProgress.user_id == user_id, LessonProgress.lesson_id == exercise.lesson_id
                )
            ).scalar_one_or_none()
            if progress is not None:
                progress.exercises_completed = (progress.exercises_completed or 0) + 1

        self.db.commit()
        self.db.refresh(attempt)

        show_answer = result.is_auto_graded or attempt.solution_revealed
        return SubmitExerciseAttemptResponse(
            attempt=ExerciseAttemptSchema.model_validate(attempt),
            is_auto_graded=result.is_auto_graded,
            explanation=content.explanation
            if (result.is_auto_graded or status != ExerciseAttemptStatus.SUBMITTED)
            else None,
            correct_answer=content.correct_answer if show_answer else None,
        )

    def _latest_attempt(self, user_id: str, exercise_id: str) -> ExerciseAttempt | None:
        attempts = self._attempts_for(user_id, exercise_id)
        return attempts[0] if attempts else None

    def reveal_hint(self, user_id: str, slug: str) -> RevealHintResponse:
        exercise = self.get_model_by_slug(slug)
        content = self._load_content(exercise)
        if not content.hints:
            raise AppError("This exercise has no hints.", details={"slug": slug})

        attempt = self._latest_attempt(user_id, exercise.id)
        if attempt is None or attempt.status != ExerciseAttemptStatus.PENDING:
            attempt = ExerciseAttempt(
                user_id=user_id, exercise_id=exercise.id, status=ExerciseAttemptStatus.PENDING
            )
            self.db.add(attempt)
            self.db.flush()

        if attempt.hints_used >= len(content.hints):
            hint_index = len(content.hints) - 1
        else:
            attempt.hints_used += 1
            hint_index = attempt.hints_used - 1

        self.db.commit()
        return RevealHintResponse(
            hint_index=hint_index,
            hint=content.hints[hint_index],
            hints_remaining=max(0, len(content.hints) - attempt.hints_used),
        )

    def reveal_solution(self, user_id: str, slug: str) -> RevealSolutionResponse:
        exercise = self.get_model_by_slug(slug)
        content = self._load_content(exercise)

        attempt = self._latest_attempt(user_id, exercise.id)
        if attempt is None or attempt.status != ExerciseAttemptStatus.PENDING:
            attempt = ExerciseAttempt(
                user_id=user_id, exercise_id=exercise.id, status=ExerciseAttemptStatus.PENDING
            )
            self.db.add(attempt)
            self.db.flush()
        attempt.solution_revealed = True
        self.db.commit()

        return RevealSolutionResponse(solution=content.solution, explanation=content.explanation)

    def update_admin(self, exercise_id: str, payload: UpdateExerciseAdminRequest) -> ExerciseSchema:
        exercise = self.repo.get_by_id(exercise_id)
        if exercise is None:
            raise NotFoundError(f"Exercise '{exercise_id}' was not found.")
        if payload.is_active is not None:
            exercise.is_active = payload.is_active
        if payload.display_order is not None:
            exercise.display_order = payload.display_order
        self.db.commit()
        self.db.refresh(exercise)
        return self.to_schema(exercise)
