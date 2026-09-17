"""Readiness scoring (spec section 39) — pure, DB-free, deterministic.

**The documented formula.** Readiness combines three real signals, each
independently capped so no single one can dominate:

1. **Skill mastery** (50%) — the average `UserSkill.mastery_score` across
   interview-relevant skill categories (already computed by the existing
   Phase 2 `MasteryService`, itself a real, execution-derived score — see
   that module). This is the "do you actually know this" signal, built up
   over the whole platform, not just interview practice.
2. **Recent interview performance** (35%) — a recency-weighted average of
   the last `MAX_RECENT_INTERVIEWS` completed interviews' overall scores,
   using the same half-life decay shape as `MasteryService._weighted_score`
   (so this module stays consistent with the rest of the app's "recent
   matters more, but nothing is ever fully forgotten" philosophy) — capped
   so that a single interview can shift readiness by at most
   `MAX_SINGLE_INTERVIEW_SWING` points relative to the average of the
   others, directly satisfying spec section 39's "do not let one assessment
   dominate the score."
3. **Consistency** (15%) — a penalty for high variance across those same
   recent interviews: a candidate who scores 90/40/85/45 is less
   "interview ready" than one who steadily scores 70/72/68/71, even at the
   same average.

Case/Project performance folds into (1) via the skills those Case/Project
rubrics already feed into `UserSkill` — Phase 8 does not compute a separate
skill-independent score, so there is nothing further to add here without
double-counting.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import UTC, datetime

MAX_RECENT_INTERVIEWS = 8
RECENCY_HALF_LIFE_DAYS = 14.0
MAX_SINGLE_INTERVIEW_SWING = 15.0

MASTERY_WEIGHT = 0.50
RECENT_PERFORMANCE_WEIGHT = 0.35
CONSISTENCY_WEIGHT = 0.15


@dataclass
class CompletedInterview:
    overall_score: float
    completed_at: datetime
    interview_type_scores: dict[str, float] = field(default_factory=dict)  # for the per-domain breakdown


@dataclass
class ReadinessResult:
    overall_score: float  # 0-100
    mastery_component: float
    recent_performance_component: float
    consistency_component: float
    breakdown: dict[str, float] = field(default_factory=dict)  # per interview_type, from recent interviews


def _ensure_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _recency_weighted_average(interviews: list[CompletedInterview]) -> float:
    if not interviews:
        return 0.0
    now = datetime.now(UTC)
    total_weight = 0.0
    total = 0.0
    for interview in interviews:
        days_ago = max(0.0, (now - _ensure_aware(interview.completed_at)).total_seconds() / 86400)
        weight = 0.5 ** (days_ago / RECENCY_HALF_LIFE_DAYS)
        total_weight += weight
        total += interview.overall_score * weight
    return total / total_weight if total_weight else 0.0


def _capped_recent_performance(interviews: list[CompletedInterview]) -> float:
    """The recency-weighted average, but no single interview may pull the
    result more than `MAX_SINGLE_INTERVIEW_SWING` points away from the
    average of the *others* — a direct, mechanical enforcement of "one
    assessment must not dominate," rather than just hoping the recency
    weighting alone is gentle enough."""
    if not interviews:
        return 0.0
    if len(interviews) == 1:
        return interviews[0].overall_score

    raw = _recency_weighted_average(interviews)
    capped_scores = []
    for interview in interviews:
        others = [i.overall_score for i in interviews if i is not interview]
        others_avg = sum(others) / len(others)
        low, high = others_avg - MAX_SINGLE_INTERVIEW_SWING, others_avg + MAX_SINGLE_INTERVIEW_SWING
        capped_scores.append(min(max(interview.overall_score, low), high))

    capped_interviews = [
        CompletedInterview(overall_score=s, completed_at=i.completed_at)
        for s, i in zip(capped_scores, interviews, strict=True)
    ]
    return _recency_weighted_average(capped_interviews) if raw else 0.0


def _consistency_score(interviews: list[CompletedInterview]) -> float:
    """100 = perfectly consistent recent scores, decaying as their standard
    deviation grows — a stdev of 25+ points (a genuinely erratic spread,
    e.g. 90 then 40) drives this toward 0. With zero interviews there is
    nothing to be confident about (0, not a default 100); with exactly one,
    there's a real data point but no variance to measure yet, so it's not
    penalized."""
    if not interviews:
        return 0.0
    if len(interviews) == 1:
        return 100.0
    scores = [i.overall_score for i in interviews]
    stdev = statistics.pstdev(scores)
    return max(0.0, 100.0 - (stdev / 25.0) * 100.0)


def compute_readiness(
    skill_mastery_scores: list[float],
    recent_interviews: list[CompletedInterview],
) -> ReadinessResult:
    recent = sorted(recent_interviews, key=lambda i: i.completed_at, reverse=True)[:MAX_RECENT_INTERVIEWS]

    mastery_component = round(sum(skill_mastery_scores) / len(skill_mastery_scores), 1) if skill_mastery_scores else 0.0
    recent_performance_component = round(_capped_recent_performance(recent), 1)
    consistency_component = round(_consistency_score(recent), 1)

    overall = round(
        mastery_component * MASTERY_WEIGHT
        + recent_performance_component * RECENT_PERFORMANCE_WEIGHT
        + consistency_component * CONSISTENCY_WEIGHT,
        1,
    )

    breakdown: dict[str, list[float]] = {}
    for interview in recent:
        for interview_type, score in interview.interview_type_scores.items():
            breakdown.setdefault(interview_type, []).append(score)
    averaged_breakdown = {k: round(sum(v) / len(v), 1) for k, v in breakdown.items()}

    return ReadinessResult(
        overall_score=overall,
        mastery_component=mastery_component,
        recent_performance_component=recent_performance_component,
        consistency_component=consistency_component,
        breakdown=averaged_breakdown,
    )
