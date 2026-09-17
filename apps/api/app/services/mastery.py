"""Skill mastery scoring.

A basic-but-real model (Phase 2): every scored ExerciseAttempt and
AssessmentAnswer for a skill contributes to a weighted average, where the
weight favors harder exercises and more recent attempts, and the
contributed score itself is penalized for hints used / solutions revealed.
This is deliberately simple — it is NOT claiming a single completed lesson
equals mastery; mastery only moves via graded practice.
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAnswer, AssessmentAttempt
from app.models.enums import DifficultyLevel, mastery_level_for_score
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.user_skill import UserSkill

DIFFICULTY_WEIGHT: dict[DifficultyLevel, float] = {
    DifficultyLevel.BEGINNER: 1.0,
    DifficultyLevel.INTERMEDIATE: 1.5,
    DifficultyLevel.ADVANCED: 2.0,
}
RECENCY_HALF_LIFE_DAYS = 30.0
CORRECT_THRESHOLD = 70.0


def _ensure_aware(occurred_at: datetime) -> datetime:
    """SQLite round-trips DateTime(timezone=True) values as naive, but an
    object still pending flush in the current session keeps the aware value
    it was assigned in Python — normalize both to UTC-aware so events from
    either source can be compared/maxed safely."""
    return occurred_at if occurred_at.tzinfo is not None else occurred_at.replace(tzinfo=UTC)


@dataclass
class ScoredEvent:
    score: float  # 0-100, already hint/solution-penalized
    difficulty: DifficultyLevel
    occurred_at: datetime

    def __post_init__(self) -> None:
        self.occurred_at = _ensure_aware(self.occurred_at)


class MasteryService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _exercise_events(self, user_id: str, skill_id: str) -> list[ScoredEvent]:
        stmt = (
            select(ExerciseAttempt, Exercise)
            .join(Exercise, Exercise.id == ExerciseAttempt.exercise_id)
            .where(Exercise.skill_id == skill_id, ExerciseAttempt.user_id == user_id)
            .where(ExerciseAttempt.score.is_not(None))
        )
        events: list[ScoredEvent] = []
        for attempt, exercise in self.db.execute(stmt).all():
            penalty = 1.0 - min(0.6, 0.1 * attempt.hints_used + (0.3 if attempt.solution_revealed else 0.0))
            events.append(
                ScoredEvent(
                    score=max(0.0, attempt.score * penalty),
                    difficulty=exercise.difficulty,
                    occurred_at=attempt.attempted_at,
                )
            )
        return events

    def _assessment_events(self, user_id: str, skill_id: str) -> list[ScoredEvent]:
        stmt = (
            select(AssessmentAnswer, Exercise, AssessmentAttempt)
            .join(Exercise, Exercise.id == AssessmentAnswer.exercise_id)
            .join(AssessmentAttempt, AssessmentAttempt.id == AssessmentAnswer.attempt_id)
            .where(Exercise.skill_id == skill_id, AssessmentAttempt.user_id == user_id)
            .where(AssessmentAnswer.score.is_not(None))
        )
        events: list[ScoredEvent] = []
        for answer, exercise, attempt in self.db.execute(stmt).all():
            events.append(
                ScoredEvent(
                    score=answer.score,
                    difficulty=exercise.difficulty,
                    occurred_at=attempt.completed_at or attempt.started_at,
                )
            )
        return events

    def _weighted_score(self, events: list[ScoredEvent]) -> tuple[float, int, int]:
        if not events:
            return 0.0, 0, 0

        now = datetime.now(UTC)
        total_weight = 0.0
        total_weighted_score = 0.0
        correct = 0
        for event in events:
            days_ago = max(0.0, (now - event.occurred_at).total_seconds() / 86400)
            recency_weight = 0.5 ** (days_ago / RECENCY_HALF_LIFE_DAYS)
            weight = DIFFICULTY_WEIGHT[event.difficulty] * recency_weight
            total_weight += weight
            total_weighted_score += event.score * weight
            if event.score >= CORRECT_THRESHOLD:
                correct += 1

        average = total_weighted_score / total_weight if total_weight else 0.0
        return round(average, 1), len(events), correct

    def recalculate(self, user_id: str, skill_id: str) -> UserSkill:
        events = self._exercise_events(user_id, skill_id) + self._assessment_events(user_id, skill_id)
        mastery_score, attempted, correct = self._weighted_score(events)
        confidence_score = round(min(100.0, 20.0 + attempted * 8.0), 1) if attempted else 0.0

        user_skill = (
            self.db.query(UserSkill)
            .filter(UserSkill.user_id == user_id, UserSkill.skill_id == skill_id)
            .one_or_none()
        )
        if user_skill is None:
            user_skill = UserSkill(user_id=user_id, skill_id=skill_id)
            self.db.add(user_skill)

        user_skill.mastery_score = mastery_score
        user_skill.confidence_score = confidence_score
        user_skill.questions_attempted = attempted
        user_skill.questions_correct = correct
        user_skill.last_practiced_at = max((e.occurred_at for e in events), default=None)
        self.db.flush()
        return user_skill

    def recalculate_for_exercise(self, user_id: str, exercise_id: str) -> UserSkill | None:
        """Convenience: look up the exercise's skill and recalculate that skill only."""
        exercise = self.db.get(Exercise, exercise_id)
        if exercise is None or exercise.skill_id is None:
            return None
        return self.recalculate(user_id, exercise.skill_id)


def mastery_level(score: float) -> str:
    return mastery_level_for_score(score).value
