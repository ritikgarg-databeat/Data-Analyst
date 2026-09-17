"""Deterministic "what should I study next" recommendations (Phase 2 — no AI).

Priority order, per lesson prompt: incomplete prerequisite > next lesson in
the user's current module > weak skill > any unfinished lesson > review item.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import LessonProgressStatus
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.lesson_relations import LessonSkill
from app.models.module import Module
from app.models.user_skill import UserSkill
from app.services.prerequisites import PrerequisiteService

Reason = Literal["incomplete_prerequisite", "next_in_module", "weak_skill", "unfinished_lesson", "review"]

MASTERY_REVIEW_THRESHOLD = 60.0


@dataclass
class Recommendation:
    lesson: Lesson
    reason: Reason
    explanation: str


class RecommendationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.prereqs = PrerequisiteService(db)

    def _progress_for(self, user_id: str, lesson_id: str) -> LessonProgress | None:
        return self.db.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id
            )
        ).scalar_one_or_none()

    def _current_module(self, user_id: str) -> Module | None:
        stmt = (
            select(Module)
            .join(Lesson, Lesson.module_id == Module.id)
            .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.IN_PROGRESS,
            )
            .order_by(LessonProgress.last_accessed_at.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _next_in_module(self, user_id: str, module_id: str) -> Lesson | None:
        stmt = (
            select(Lesson)
            .outerjoin(
                LessonProgress,
                (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user_id),
            )
            .where(Lesson.module_id == module_id, Lesson.is_active.is_(True))
            .where(
                (LessonProgress.status.is_(None)) | (LessonProgress.status != LessonProgressStatus.COMPLETED)
            )
            .order_by(Lesson.display_order)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _weakest_skill_lesson(
        self, user_id: str, exclude_lesson_ids: set[str]
    ) -> tuple[Lesson, float] | None:
        weak_skill = self.db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id, UserSkill.questions_attempted > 0)
            .order_by(UserSkill.mastery_score)
            .limit(1)
        ).scalar_one_or_none()
        if weak_skill is None:
            return None

        stmt = (
            select(Lesson)
            .join(LessonSkill, LessonSkill.lesson_id == Lesson.id)
            .outerjoin(
                LessonProgress,
                (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user_id),
            )
            .where(LessonSkill.skill_id == weak_skill.skill_id, Lesson.is_active.is_(True))
            .where(
                (LessonProgress.status.is_(None)) | (LessonProgress.status != LessonProgressStatus.COMPLETED)
            )
            .where(~Lesson.id.in_(exclude_lesson_ids) if exclude_lesson_ids else True)
            .order_by(Lesson.display_order)
            .limit(1)
        )
        lesson = self.db.execute(stmt).scalar_one_or_none()
        return (lesson, weak_skill.mastery_score) if lesson else None

    def _any_unfinished_lesson(self, user_id: str, exclude_lesson_ids: set[str]) -> Lesson | None:
        stmt = (
            select(Lesson)
            .outerjoin(
                LessonProgress,
                (LessonProgress.lesson_id == Lesson.id) & (LessonProgress.user_id == user_id),
            )
            .where(Lesson.is_active.is_(True))
            .where(
                (LessonProgress.status.is_(None)) | (LessonProgress.status != LessonProgressStatus.COMPLETED)
            )
            .where(~Lesson.id.in_(exclude_lesson_ids) if exclude_lesson_ids else True)
            .order_by(Lesson.display_order)
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _review_lesson(self, user_id: str, exclude_lesson_ids: set[str]) -> tuple[Lesson, float] | None:
        weak_skill = self.db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id, UserSkill.mastery_score < MASTERY_REVIEW_THRESHOLD)
            .order_by(UserSkill.mastery_score)
            .limit(1)
        ).scalar_one_or_none()
        if weak_skill is None:
            return None

        stmt = (
            select(Lesson)
            .join(LessonSkill, LessonSkill.lesson_id == Lesson.id)
            .join(LessonProgress, LessonProgress.lesson_id == Lesson.id)
            .where(
                LessonSkill.skill_id == weak_skill.skill_id,
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.COMPLETED,
            )
            .where(~Lesson.id.in_(exclude_lesson_ids) if exclude_lesson_ids else True)
            .order_by(Lesson.display_order)
            .limit(1)
        )
        lesson = self.db.execute(stmt).scalar_one_or_none()
        return (lesson, weak_skill.mastery_score) if lesson else None

    def get_next(self, user_id: str, limit: int = 5) -> list[Recommendation]:
        recommendations: list[Recommendation] = []
        seen: set[str] = set()

        def add(lesson: Lesson | None, reason: Reason, explanation: str) -> None:
            if lesson is not None and lesson.id not in seen:
                recommendations.append(Recommendation(lesson=lesson, reason=reason, explanation=explanation))
                seen.add(lesson.id)

        current_module = self._current_module(user_id)
        if current_module is not None:
            next_lesson = self._next_in_module(user_id, current_module.id)
            if next_lesson is not None:
                if self.prereqs.is_locked(user_id, next_lesson.id):
                    unmet = [
                        s
                        for s in self.prereqs.get_prerequisite_statuses(user_id, next_lesson.id)
                        if s.is_hard_blocker and not s.is_completed
                    ]
                    for status in unmet:
                        add(
                            status.prerequisite_lesson,
                            "incomplete_prerequisite",
                            f'Required before you can continue "{next_lesson.title}".',
                        )
                else:
                    add(
                        next_lesson,
                        "next_in_module",
                        f"Continues where you left off in {current_module.title}.",
                    )

        while len(recommendations) < limit:
            weak = self._weakest_skill_lesson(user_id, seen)
            if weak is None:
                break
            lesson, score = weak
            add(lesson, "weak_skill", f"Your mastery here is {score:.0f}/100 — this lesson builds it.")

        while len(recommendations) < limit:
            lesson = self._any_unfinished_lesson(user_id, seen)
            if lesson is None:
                break
            add(lesson, "unfinished_lesson", "You haven't finished this lesson yet.")

        while len(recommendations) < limit:
            review = self._review_lesson(user_id, seen)
            if review is None:
                break
            lesson, score = review
            add(lesson, "review", f"Mastery has dipped to {score:.0f}/100 — worth a review.")

        return recommendations[:limit]
