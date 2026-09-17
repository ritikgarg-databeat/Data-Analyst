"""Spaced-review foundation (spec section 53) — pure, DB-free, deterministic.

Deliberately NOT a full SM-2/Anki-style scheduler: the spec asks for a
*foundation*, and a real spacing algorithm needs review-quality grades and a
per-item ease factor that this phase doesn't collect yet. What this does
instead is the honest, inspectable version of the same idea: how long a
question should rest before it's worth seeing again is a function of how well
it went last time, and anything past that rest interval is "due".

    score < 60          -> revisit after 1 day    (you didn't get it)
    60 <= score < 85    -> revisit after 3 days   (shaky)
    85 <= score < 100   -> revisit after 10 days  (solid)
    score == 100        -> revisit after 30 days  (mastered — but not never)

Repeated success stretches the interval (a question answered well three times
running rests ~2x longer than one answered well once); a failure resets that
stretch, so a question you keep missing keeps coming back quickly. Priority
orders the queue: how badly it went, then how overdue it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

BASE_INTERVAL_DAYS: list[tuple[float, float]] = [
    (60.0, 1.0),
    (85.0, 3.0),
    (100.0, 10.0),
]
MASTERED_INTERVAL_DAYS = 30.0
# How much each consecutive good answer stretches the rest interval, and the
# ceiling on that stretch (so an interval can never run away entirely).
STREAK_STRETCH = 0.5
MAX_STREAK_MULTIPLIER = 2.0
GOOD_SCORE = 85.0


@dataclass
class ReviewItem:
    """One question's history, as far as spacing cares about it."""

    question_id: str
    interview_type: str
    last_score: float
    last_attempted_at: datetime
    attempt_count: int = 1
    consecutive_good: int = 0


@dataclass
class DueReview:
    question_id: str
    interview_type: str
    last_score: float
    days_since_last_attempt: float
    interval_days: float
    days_overdue: float
    priority: float  # higher = review sooner
    reason: str


def _ensure_aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def interval_days_for(score: float, consecutive_good: int = 0) -> float:
    base = MASTERED_INTERVAL_DAYS
    for threshold, days in BASE_INTERVAL_DAYS:
        if score < threshold:
            base = days
            break
    if score < GOOD_SCORE:
        return base  # a miss never earns a streak stretch
    multiplier = min(MAX_STREAK_MULTIPLIER, 1.0 + STREAK_STRETCH * max(0, consecutive_good - 1))
    return base * multiplier


def _reason_for(score: float, days_overdue: float) -> str:
    if score < 60.0:
        return "You missed this last time — worth a second attempt."
    if score < GOOD_SCORE:
        return "You got most of this but not all of it."
    if score < 100.0:
        return "Solid last time; a quick refresher keeps it that way."
    return f"Mastered {days_overdue + 30:.0f} days ago — checking it still sticks."


def due_reviews(items: list[ReviewItem], *, now: datetime | None = None, limit: int | None = None) -> list[DueReview]:
    """Everything whose rest interval has elapsed, most-worth-reviewing first."""
    current = _ensure_aware(now) if now is not None else datetime.now(UTC)

    due: list[DueReview] = []
    for item in items:
        days_since = max(0.0, (current - _ensure_aware(item.last_attempted_at)).total_seconds() / 86400)
        interval = interval_days_for(item.last_score, item.consecutive_good)
        if days_since < interval:
            continue
        days_overdue = days_since - interval
        # Weakness dominates ordering; overdue-ness only breaks ties between
        # questions that went comparably badly, so a long-forgotten mastered
        # question can never outrank one you actually got wrong.
        priority = round((100.0 - item.last_score) + min(days_overdue, 30.0) * 0.5, 2)
        due.append(
            DueReview(
                question_id=item.question_id,
                interview_type=item.interview_type,
                last_score=item.last_score,
                days_since_last_attempt=round(days_since, 2),
                interval_days=interval,
                days_overdue=round(days_overdue, 2),
                priority=priority,
                reason=_reason_for(item.last_score, days_overdue),
            )
        )

    due.sort(key=lambda d: (-d.priority, d.question_id))
    return due[:limit] if limit else due
