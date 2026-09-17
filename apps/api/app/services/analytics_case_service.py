"""Business/Product Analytics Cases (Phase 6, spec sections 33 & 44) — a
thin, richer read view over Exercises tagged `case-study`. Deliberately NOT
a parallel model/table: submission, scoring, and progress tracking all
reuse the existing Exercise/ExerciseAttempt pipeline untouched (see
app.services.exercise_service and the rubric-scoring addition in
app.services.grading) — "enough infrastructure for Business/Product cases"
per the spec, with the full case-study engine deferred to Phase 8."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content.loader import load_exercise_file
from app.core.errors import NotFoundError
from app.models.exercise import Exercise
from app.models.tag import ExerciseTag, Tag
from app.schemas.analytics_cases import AnalyticsCaseSchema
from app.schemas.exercise import RubricCriterionSchema
from app.services.exercise_service import ExerciseService

CASE_STUDY_TAG_SLUG = "case-study"


class AnalyticsCaseService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.exercise_service = ExerciseService(db)

    def _to_case_schema(self, exercise: Exercise) -> AnalyticsCaseSchema:
        content = load_exercise_file(exercise.content_reference) if exercise.content_reference else None
        base = self.exercise_service.to_schema(exercise)
        return AnalyticsCaseSchema(
            **base.model_dump(),
            prompt=content.prompt if content else "",
            business_context=content.business_context if content else None,
            stakeholder=content.stakeholder if content else None,
            constraints=content.constraints if content else [],
            expected_deliverables=content.expected_deliverables if content else [],
            rubric=[RubricCriterionSchema(criterion=c.criterion, points=c.points) for c in content.rubric]
            if content
            else [],
        )

    def list_cases(self, *, domain: str | None = None) -> list[AnalyticsCaseSchema]:
        stmt = (
            select(Exercise)
            .join(ExerciseTag, ExerciseTag.exercise_id == Exercise.id)
            .join(Tag, Tag.id == ExerciseTag.tag_id)
            .where(Tag.slug == CASE_STUDY_TAG_SLUG, Exercise.is_active.is_(True))
            .order_by(Exercise.display_order, Exercise.title)
        )
        exercises = list(self.db.execute(stmt).scalars().all())
        cases = [self._to_case_schema(e) for e in exercises]
        if domain:
            needle = domain.strip().lower()
            cases = [c for c in cases if any(needle in t.slug.lower() for t in c.tags)]
        return cases

    def get_case(self, slug: str) -> AnalyticsCaseSchema:
        exercise = self.db.execute(select(Exercise).where(Exercise.slug == slug)).scalar_one_or_none()
        if exercise is None:
            raise NotFoundError(f"Case '{slug}' was not found.", details={"slug": slug})
        return self._to_case_schema(exercise)
