"""Achievement System (Phase 11, spec section 27) — a deliberately short,
non-excessive badge list (database/seeds/achievements.yaml). Earning is
decided here, by checking REAL counts against each badge's slug — never by
interpreting Achievement.criteria as a generic rules engine (see that
model's docstring) and never a substitute for the real mastery/readiness
scores. `sync_for_user` is called opportunistically (from the Career
Dashboard) rather than hooked into every other phase's own commit path."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.career import (
    Achievement,
    BehavioralStory,
    CareerAssessment,
    Portfolio,
    PortfolioItem,
    Resume,
    ResumeVersion,
    UserAchievement,
)
from app.models.case import CaseAttempt
from app.models.enums import CareerReadinessLevel, CaseAttemptStatus, InterviewStatus, PrivacyLevel
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview
from app.models.project import Project
from app.models.user_skill import UserSkill
from app.schemas.career import AchievementSchema, UserAchievementSchema

READY_LEVELS = {
    CareerReadinessLevel.INTERVIEW_READY,
    CareerReadinessLevel.STRONG_CANDIDATE,
    CareerReadinessLevel.EXCEPTIONAL,
}


class AchievementService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_achievements(self) -> list[AchievementSchema]:
        rows = self.db.execute(select(Achievement).where(Achievement.is_active.is_(True))).scalars().all()
        return [AchievementSchema.model_validate(r) for r in rows]

    def _count(self, stmt) -> int:
        return self.db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    def _is_earned(self, user_id: str, slug: str) -> bool:
        if slug in ("first-exercise-passed", "ten-exercises-passed"):
            threshold = 1 if slug == "first-exercise-passed" else 10
            count = self._count(
                select(ExerciseAttempt).where(
                    ExerciseAttempt.user_id == user_id, ExerciseAttempt.score.is_not(None),
                    ExerciseAttempt.score >= 70,
                )
            )
            return count >= threshold
        if slug == "first-skill-mastered":
            return self._count(
                select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.mastery_score >= 90)
            ) >= 1
        if slug == "first-case-completed":
            return self._count(
                select(CaseAttempt).where(
                    CaseAttempt.user_id == user_id, CaseAttempt.status == CaseAttemptStatus.COMPLETED
                )
            ) >= 1
        if slug == "first-project-completed":
            return self._count(
                select(Project).where(
                    Project.user_id == user_id, Project.status == CaseAttemptStatus.COMPLETED
                )
            ) >= 1
        if slug == "first-interview-completed":
            return self._count(
                select(Interview).where(
                    Interview.user_id == user_id, Interview.status == InterviewStatus.COMPLETED
                )
            ) >= 1
        if slug == "resume-added":
            return self._count(
                select(ResumeVersion)
                .join(Resume, Resume.id == ResumeVersion.resume_id)
                .where(Resume.user_id == user_id)
            ) >= 1
        if slug == "portfolio-item-published":
            return self._count(
                select(PortfolioItem)
                .join(Portfolio, Portfolio.id == PortfolioItem.portfolio_id)
                .where(Portfolio.user_id == user_id, PortfolioItem.privacy != PrivacyLevel.PRIVATE)
            ) >= 1
        if slug == "behavioral-story-bank-started":
            return self._count(select(BehavioralStory).where(BehavioralStory.user_id == user_id)) >= 3
        if slug == "interview-ready-reached":
            rows = self.db.execute(
                select(CareerAssessment.overall_readiness_level).where(CareerAssessment.user_id == user_id)
            ).scalars().all()
            return any(level in READY_LEVELS for level in rows)
        return False

    def sync_for_user(self, user_id: str) -> list[UserAchievementSchema]:
        already_earned = set(
            self.db.execute(
                select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
            ).scalars().all()
        )
        achievements = (
            self.db.execute(select(Achievement).where(Achievement.is_active.is_(True))).scalars().all()
        )
        for achievement in achievements:
            if achievement.id in already_earned:
                continue
            if self._is_earned(user_id, achievement.slug):
                self.db.add(UserAchievement(user_id=user_id, achievement_id=achievement.id))
        self.db.commit()

        rows = self.db.execute(
            select(UserAchievement)
            .where(UserAchievement.user_id == user_id)
            .order_by(UserAchievement.earned_at.desc())
        ).scalars().all()
        return [UserAchievementSchema.model_validate(r) for r in rows]
