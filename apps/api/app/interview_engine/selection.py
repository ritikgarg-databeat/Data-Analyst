"""Deterministic (non-AI) adaptive question selection (spec sections 35-36).

Two rules, both simple and inspectable:

1. **Avoid repeats of already-mastered questions** (spec 35) — prefer a
   question the learner hasn't seen at all; if the pool of a given type is
   exhausted, allow repeats of anything *not* already mastered (scored
   `MASTERY_SCORE`+) before ever repeating a mastered one.
2. **Adaptive difficulty** (spec 36) — look at the most recent question of
   the *same* interview_type: answered very well and comfortably within the
   time limit -> the next one steps up a difficulty tier; failed outright ->
   the next one steps back down to (at most) INTERMEDIATE, never straight to
   the hardest tier's opposite extreme; otherwise the difficulty holds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

DIFFICULTY_ORDER = ["BEGINNER", "INTERMEDIATE", "ADVANCED"]
MASTERY_SCORE = 85.0
FAST_RATIO_THRESHOLD = 0.8  # finishing in <=80% of the time limit counts as "comfortably fast"


@dataclass
class QuestionCandidate:
    id: str
    interview_type: str
    difficulty: str
    is_active: bool = True


@dataclass
class HistoryEntry:
    question_id: str
    interview_type: str
    difficulty: str
    score: float
    time_limit_seconds: int | None = None
    time_spent_seconds: int | None = None
    answered_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def _next_difficulty(previous_difficulty: str, previous_score: float, ratio: float | None) -> str:
    idx = DIFFICULTY_ORDER.index(previous_difficulty) if previous_difficulty in DIFFICULTY_ORDER else 1
    if previous_score >= MASTERY_SCORE and (ratio is None or ratio <= FAST_RATIO_THRESHOLD):
        return DIFFICULTY_ORDER[min(idx + 1, len(DIFFICULTY_ORDER) - 1)]
    if previous_score < 60.0:
        return DIFFICULTY_ORDER[min(idx, 1)]  # step back, but land on INTERMEDIATE at worst — "another medium question"
    return previous_difficulty


def select_next_question(
    candidates: list[QuestionCandidate],
    history: list[HistoryEntry],
    target_interview_type: str,
) -> QuestionCandidate | None:
    pool = [c for c in candidates if c.interview_type == target_interview_type and c.is_active]
    if not pool:
        return None

    answered_ids = {h.question_id for h in history}
    mastered_ids = {h.question_id for h in history if h.score >= MASTERY_SCORE}
    unseen = [c for c in pool if c.id not in answered_ids]
    usable = unseen or [c for c in pool if c.id not in mastered_ids] or pool

    same_type_history = sorted(
        (h for h in history if h.interview_type == target_interview_type),
        key=lambda h: h.answered_at,
        reverse=True,
    )
    if same_type_history:
        last = same_type_history[0]
        ratio = (
            last.time_spent_seconds / last.time_limit_seconds
            if last.time_limit_seconds and last.time_spent_seconds is not None
            else None
        )
        target_difficulty = _next_difficulty(last.difficulty, last.score, ratio)
    else:
        target_difficulty = "INTERMEDIATE"

    exact = sorted((c for c in usable if c.difficulty == target_difficulty), key=lambda c: c.id)
    if exact:
        return exact[0]

    target_index = DIFFICULTY_ORDER.index(target_difficulty)
    by_closeness = sorted(
        usable,
        key=lambda c: (
            abs(DIFFICULTY_ORDER.index(c.difficulty) - target_index) if c.difficulty in DIFFICULTY_ORDER else 99,
            c.id,
        ),
    )
    return by_closeness[0]
