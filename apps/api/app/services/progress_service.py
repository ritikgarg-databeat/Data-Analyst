from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.assessment import Assessment, AssessmentAttempt
from app.models.enums import SKILL_CATEGORY_LABELS, DifficultyLevel, LessonProgressStatus, SkillCategory
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.repositories.lesson import LessonRepository
from app.repositories.progress import LessonProgressRepository
from app.repositories.skill import SkillRepository, UserSkillRepository
from app.schemas.lesson import Lesson as LessonSchema
from app.schemas.progress import (
    ActivityDay,
    ContinueLearningItem,
    ProgressSummary,
    RecentlyCompletedItem,
    SkillCategoryOverview,
    UpdateLessonPositionRequest,
    UpsertLessonProgressRequest,
    WeakArea,
)
from app.schemas.progress import LessonProgress as LessonProgressSchema
from app.schemas.skill import Skill as SkillSchema
from app.services.completion_rules import CompletionContext, evaluate_completion

MASTERY_THRESHOLD = 80.0
WEAK_AREA_THRESHOLD = 55.0
ACTIVITY_WINDOW_DAYS = 14


class ProgressService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.progress_repo = LessonProgressRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.skill_repo = SkillRepository(db)
        self.user_skill_repo = UserSkillRepository(db)

    def list_lesson_progress(self, user_id: str) -> list[LessonProgressSchema]:
        return [LessonProgressSchema.model_validate(p) for p in self.progress_repo.list_for_user(user_id)]

    def _best_exercise_score_percent(self, user_id: str, lesson_id: str) -> float | None:
        stmt = (
            select(func.max(ExerciseAttempt.score))
            .select_from(ExerciseAttempt)
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .where(Exercise.lesson_id == lesson_id, ExerciseAttempt.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def _best_assessment_score_percent(self, user_id: str, module_id: str) -> float | None:
        stmt = (
            select(func.max(AssessmentAttempt.score))
            .select_from(AssessmentAttempt)
            .join(Assessment, Assessment.id == AssessmentAttempt.assessment_id)
            .where(Assessment.module_id == module_id, AssessmentAttempt.user_id == user_id)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def upsert_lesson_progress(
        self, user_id: str, lesson_id: str, payload: UpsertLessonProgressRequest
    ) -> LessonProgressSchema:
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_id}' was not found.", details={"lesson_id": lesson_id})

        progress = self.progress_repo.get(user_id, lesson_id)
        now = datetime.now(UTC)
        if progress is None:
            progress = LessonProgress(user_id=user_id, lesson_id=lesson_id)
            self.db.add(progress)

        progress.progress_percent = payload.progress_percent
        progress.last_accessed_at = now
        if progress.started_at is None:
            progress.started_at = now

        if payload.status == LessonProgressStatus.COMPLETED:
            ctx = CompletionContext(
                lesson=lesson,
                progress=progress,
                best_exercise_score_percent=self._best_exercise_score_percent(user_id, lesson_id),
                best_assessment_score_percent=self._best_assessment_score_percent(user_id, lesson.module_id),
            )
            if evaluate_completion(ctx):
                progress.status = LessonProgressStatus.COMPLETED
                if progress.completed_at is None:
                    progress.completed_at = now
            else:
                # Completion criteria not yet met — a lesson is never marked
                # complete merely because the client asked (see completion_rules).
                progress.status = LessonProgressStatus.IN_PROGRESS
        else:
            progress.status = payload.status

        self.db.commit()
        self.db.refresh(progress)
        return LessonProgressSchema.model_validate(progress)

    def update_position(
        self, user_id: str, lesson_id: str, payload: UpdateLessonPositionRequest
    ) -> LessonProgressSchema:
        lesson = self.lesson_repo.get_by_id(lesson_id)
        if lesson is None:
            raise NotFoundError(f"Lesson '{lesson_id}' was not found.", details={"lesson_id": lesson_id})

        progress = self.progress_repo.get(user_id, lesson_id)
        now = datetime.now(UTC)
        if progress is None:
            # Explicit defaults: Python-side column defaults only apply on
            # flush, so status/time_spent_seconds would otherwise still read
            # as None here — status wouldn't compare equal to NOT_STARTED
            # below, and the += would break on time_spent_seconds.
            progress = LessonProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                started_at=now,
                time_spent_seconds=0,
                status=LessonProgressStatus.NOT_STARTED,
            )
            self.db.add(progress)

        if payload.last_position is not None:
            progress.last_position = payload.last_position
        progress.time_spent_seconds = (progress.time_spent_seconds or 0) + payload.time_spent_delta_seconds
        progress.last_accessed_at = now
        if progress.status == LessonProgressStatus.NOT_STARTED:
            progress.status = LessonProgressStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(progress)
        return LessonProgressSchema.model_validate(progress)

    # ------------------------------------------------------------------
    # Dashboard summary
    # ------------------------------------------------------------------

    def _overall_progress_percent(self, user_id: str) -> float:
        total_lessons = self.db.execute(
            select(func.count()).select_from(Lesson).where(Lesson.is_active.is_(True))
        ).scalar_one()
        if total_lessons == 0:
            return 0.0
        completed_or_partial = self.db.execute(
            select(func.coalesce(func.sum(LessonProgress.progress_percent), 0.0)).where(
                LessonProgress.user_id == user_id
            )
        ).scalar_one()
        return round(min(completed_or_partial, total_lessons * 100) / total_lessons, 1)

    def _learning_streak_days(self, user_id: str) -> int:
        rows = (
            self.db.execute(
                select(LessonProgress.last_accessed_at).where(
                    LessonProgress.user_id == user_id, LessonProgress.last_accessed_at.is_not(None)
                )
            )
            .scalars()
            .all()
        )
        if not rows:
            return 0

        active_dates = {ts.date() for ts in rows}
        streak = 0
        cursor = datetime.now(UTC).date()
        while cursor in active_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def _skills_mastered_counts(self, user_id: str) -> tuple[int, int]:
        total_skills = self.db.execute(select(func.count()).select_from(Skill)).scalar_one()
        mastered = self.db.execute(
            select(func.count())
            .select_from(UserSkill)
            .where(UserSkill.user_id == user_id, UserSkill.mastery_score >= MASTERY_THRESHOLD)
        ).scalar_one()
        return mastered, total_skills

    def _current_level(self, average_mastery: float) -> DifficultyLevel:
        if average_mastery >= 70:
            return DifficultyLevel.ADVANCED
        if average_mastery >= 35:
            return DifficultyLevel.INTERMEDIATE
        return DifficultyLevel.BEGINNER

    def _lesson_schema(self, lesson: Lesson) -> LessonSchema:
        # Local import avoids a circular import with lesson_service at module load time.
        from app.services.lesson_service import LessonService

        return LessonService(self.db).to_schema(lesson)

    def _continue_learning(self, user_id: str, limit: int = 5) -> list[ContinueLearningItem]:
        items: list[ContinueLearningItem] = []
        for progress in self.progress_repo.list_in_progress(user_id, limit=limit):
            lesson = self.lesson_repo.get_by_id(progress.lesson_id)
            if lesson is None:
                continue
            items.append(
                ContinueLearningItem(
                    lesson=self._lesson_schema(lesson),
                    module_title=lesson.module.title,
                    domain_slug=lesson.module.domain.slug,
                    domain_name=lesson.module.domain.name,
                    progress_percent=progress.progress_percent,
                )
            )
        return items

    def _recently_completed(self, user_id: str, limit: int = 5) -> list[RecentlyCompletedItem]:
        stmt = (
            select(LessonProgress)
            .where(
                LessonProgress.user_id == user_id,
                LessonProgress.status == LessonProgressStatus.COMPLETED,
                LessonProgress.completed_at.is_not(None),
            )
            .order_by(LessonProgress.completed_at.desc())
            .limit(limit)
        )
        items: list[RecentlyCompletedItem] = []
        for progress in self.db.execute(stmt).scalars().all():
            lesson = self.lesson_repo.get_by_id(progress.lesson_id)
            if lesson is None or progress.completed_at is None:
                continue
            items.append(
                RecentlyCompletedItem(lesson=self._lesson_schema(lesson), completed_at=progress.completed_at)
            )
        return items

    def _weak_areas(self, user_id: str, limit: int = 5) -> list[WeakArea]:
        stmt = (
            select(UserSkill)
            .where(UserSkill.user_id == user_id, UserSkill.questions_attempted > 0)
            .order_by(UserSkill.mastery_score)
            .limit(limit)
        )
        weak: list[WeakArea] = []
        for user_skill in self.db.execute(stmt).scalars().all():
            if user_skill.mastery_score >= WEAK_AREA_THRESHOLD:
                continue
            skill = self.db.get(Skill, user_skill.skill_id)
            if skill is None:
                continue
            if user_skill.questions_correct < user_skill.questions_attempted / 2:
                reason = (
                    f"Only {user_skill.questions_correct}/{user_skill.questions_attempted} "
                    "recent answers correct."
                )
            else:
                reason = "Mastery score is still below a comfortable threshold."
            weak.append(
                WeakArea(
                    skill=SkillSchema.model_validate(skill),
                    mastery_score=user_skill.mastery_score,
                    reason=reason,
                )
            )
        return weak

    def _activity(self, user_id: str, days: int = ACTIVITY_WINDOW_DAYS) -> list[ActivityDay]:
        since = datetime.now(UTC) - timedelta(days=days)

        lesson_rows = (
            self.db.execute(
                select(LessonProgress.last_accessed_at).where(
                    LessonProgress.user_id == user_id, LessonProgress.last_accessed_at >= since
                )
            )
            .scalars()
            .all()
        )
        exercise_rows = (
            self.db.execute(
                select(ExerciseAttempt.attempted_at).where(
                    ExerciseAttempt.user_id == user_id, ExerciseAttempt.attempted_at >= since
                )
            )
            .scalars()
            .all()
        )

        lessons_by_day: dict[date, int] = {}
        for ts in lesson_rows:
            d = ts.date()
            lessons_by_day[d] = lessons_by_day.get(d, 0) + 1
        exercises_by_day: dict[date, int] = {}
        for ts in exercise_rows:
            d = ts.date()
            exercises_by_day[d] = exercises_by_day.get(d, 0) + 1

        today = datetime.now(UTC).date()
        return [
            ActivityDay(
                date=today - timedelta(days=offset),
                lessons_progressed=lessons_by_day.get(today - timedelta(days=offset), 0),
                exercises_attempted=exercises_by_day.get(today - timedelta(days=offset), 0),
            )
            for offset in range(days - 1, -1, -1)
        ]

    def _skill_overview(self, user_id: str) -> list[SkillCategoryOverview]:
        user_skills = {us.skill_id: us for us in self.user_skill_repo.list_for_user(user_id)}
        overview: list[SkillCategoryOverview] = []
        for category in SkillCategory:
            skills_in_category = [s for s in self.skill_repo.list_all() if s.category == category]
            if not skills_in_category:
                continue
            scores = [user_skills[s.id].mastery_score for s in skills_in_category if s.id in user_skills]
            average = round(sum(scores) / len(skills_in_category), 1) if skills_in_category else 0.0
            overview.append(
                SkillCategoryOverview(
                    category=category,
                    label=SKILL_CATEGORY_LABELS[category],
                    skill_count=len(skills_in_category),
                    average_mastery=average,
                )
            )
        return overview

    def get_summary(self, user_id: str) -> ProgressSummary:
        skills_mastered, total_skills = self._skills_mastered_counts(user_id)
        skill_overview = self._skill_overview(user_id)
        overall_avg_mastery = (
            round(sum(o.average_mastery for o in skill_overview) / len(skill_overview), 1)
            if skill_overview
            else 0.0
        )
        return ProgressSummary(
            overall_progress_percent=self._overall_progress_percent(user_id),
            current_level=self._current_level(overall_avg_mastery),
            learning_streak_days=self._learning_streak_days(user_id),
            skills_mastered=skills_mastered,
            total_skills=total_skills,
            continue_learning=self._continue_learning(user_id),
            recently_completed=self._recently_completed(user_id),
            weak_areas=self._weak_areas(user_id),
            activity=self._activity(user_id),
            skill_overview=skill_overview,
        )
