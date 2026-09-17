"""Interview scoring (spec section 37) — pure, DB-free, deterministic.

Every question answered in an interview already has a REAL, objectively
computed 0-100 score (SQL/Python/Excel execution grading, MC/short-answer
correctness, or Case/rubric self-assessment scoring — all from existing
Phase 2-8 engines). This module's only job is combining those real per-
question scores into the 6 standardized dimensions (spec section 37):

    Technical Correctness   30%
    Analytical Reasoning    20%
    Business Understanding  20%
    Communication           15%
    Problem Solving         10%
    Efficiency               5%

(the default weights — an InterviewTemplate can configure its own, spec
section 37 "Allow different weights by interview type").

**The formula**: each answered question contributes to one or more
dimensions, weighted by `DIMENSION_WEIGHTS_BY_QUESTION_TYPE` below (e.g. a
SQL question is 80% "did you get the real result right" / 20% "efficiency",
a Behavioral question is 100% Communication, a Business/Product Analytics
question splits across Business Understanding/Analytical Reasoning/Problem
Solving). A dimension's score is the weighted average of every question's
(score, weight-toward-this-dimension, question's own point value) that
contributes to it — no single question can dominate a dimension unless it's
the only one answered for it. The overall score is the weighted sum of the
6 dimensions using the template's (or the default) weights, renormalized
over only the dimensions that actually received any signal (so an interview
with no Behavioral round doesn't silently zero out Communication).
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIMENSIONS = (
    "Technical Correctness",
    "Analytical Reasoning",
    "Business Understanding",
    "Communication",
    "Problem Solving",
    "Efficiency",
)

DEFAULT_RUBRIC_WEIGHTS: dict[str, float] = {
    "Technical Correctness": 30.0,
    "Analytical Reasoning": 20.0,
    "Business Understanding": 20.0,
    "Communication": 15.0,
    "Problem Solving": 10.0,
    "Efficiency": 5.0,
}

# How much of a question's own score counts toward each dimension, by its
# InterviewQuestionType (or "CASE_STUDY" for a Case Study round question).
# Each row sums to 1.0 — a question's full score is always fully allocated,
# just split across the dimensions it actually exercises.
DIMENSION_WEIGHTS_BY_QUESTION_TYPE: dict[str, dict[str, float]] = {
    "SQL": {"Technical Correctness": 0.8, "Efficiency": 0.2},
    "PYTHON": {"Technical Correctness": 0.8, "Efficiency": 0.2},
    "EXCEL": {"Technical Correctness": 0.85, "Efficiency": 0.15},
    "STATISTICS": {"Technical Correctness": 0.5, "Analytical Reasoning": 0.5},
    "AB_TESTING": {"Analytical Reasoning": 0.4, "Business Understanding": 0.3, "Technical Correctness": 0.3},
    "PRODUCT_ANALYTICS": {"Business Understanding": 0.4, "Analytical Reasoning": 0.3, "Problem Solving": 0.3},
    "BUSINESS_ANALYTICS": {"Business Understanding": 0.4, "Analytical Reasoning": 0.3, "Problem Solving": 0.3},
    "DATA_INTERPRETATION": {"Analytical Reasoning": 0.5, "Problem Solving": 0.5},
    "DATA_VISUALIZATION": {"Communication": 0.4, "Analytical Reasoning": 0.6},
    "DATA_MODELING": {"Technical Correctness": 0.6, "Problem Solving": 0.4},
    "DATA_WAREHOUSING": {"Technical Correctness": 0.6, "Problem Solving": 0.4},
    "DBT": {"Technical Correctness": 0.6, "Problem Solving": 0.4},
    "DATA_ENGINEERING": {"Technical Correctness": 0.5, "Problem Solving": 0.5},
    "BEHAVIORAL": {"Communication": 0.7, "Problem Solving": 0.3},
    "CASE_STUDY": {
        "Analytical Reasoning": 0.3,
        "Business Understanding": 0.3,
        "Problem Solving": 0.2,
        "Communication": 0.2,
    },
}


@dataclass
class ScoredQuestion:
    """One answered question's real score, ready to be folded into the
    interview-level dimension breakdown."""

    interview_type: str  # InterviewQuestionType value, or "CASE_STUDY"
    score: float  # 0-100, already computed by the real grading engine
    time_limit_seconds: int | None = None
    time_spent_seconds: int | None = None


@dataclass
class DimensionScore:
    dimension: str
    score: float  # 0-100
    question_count: int


@dataclass
class InterviewScoreResult:
    overall: float  # 0-100
    dimensions: list[DimensionScore] = field(default_factory=list)


def _efficiency_score(question: ScoredQuestion) -> float | None:
    """A question with no time limit (untimed practice) contributes no
    efficiency signal at all, rather than a fabricated one. Otherwise:
    finishing at/under the limit is full credit; up to 50% over is a linear
    penalty; beyond that is zero — mirrors app/sql/evaluation.py's
    efficiency-ratio shape (a ratio-based fraction, not a hard cutoff)."""
    if not question.time_limit_seconds or question.time_spent_seconds is None:
        return None
    ratio = question.time_spent_seconds / question.time_limit_seconds
    if ratio <= 1.0:
        return 100.0
    if ratio >= 1.5:
        return 0.0
    return 100.0 * (1.0 - (ratio - 1.0) / 0.5)


def score_interview(
    questions: list[ScoredQuestion],
    rubric_weights: dict[str, float] | None = None,
) -> InterviewScoreResult:
    weights = rubric_weights or DEFAULT_RUBRIC_WEIGHTS

    dimension_totals: dict[str, float] = {d: 0.0 for d in DIMENSIONS}
    dimension_weight_sums: dict[str, float] = {d: 0.0 for d in DIMENSIONS}
    dimension_counts: dict[str, int] = {d: 0 for d in DIMENSIONS}

    for question in questions:
        allocation = DIMENSION_WEIGHTS_BY_QUESTION_TYPE.get(question.interview_type, {})
        for dimension, share in allocation.items():
            if dimension == "Efficiency":
                continue  # efficiency is computed separately, from time — not from `score`
            dimension_totals[dimension] += question.score * share
            dimension_weight_sums[dimension] += share
            dimension_counts[dimension] += 1

        efficiency = _efficiency_score(question)
        if efficiency is not None:
            eff_share = allocation.get("Efficiency", 0.0)
            if eff_share > 0:
                dimension_totals["Efficiency"] += efficiency * eff_share
                dimension_weight_sums["Efficiency"] += eff_share
                dimension_counts["Efficiency"] += 1

    dimensions = [
        DimensionScore(
            dimension=d,
            score=round(dimension_totals[d] / dimension_weight_sums[d], 1) if dimension_weight_sums[d] else 0.0,
            question_count=dimension_counts[d],
        )
        for d in DIMENSIONS
    ]

    # Renormalize over dimensions that actually received signal, so an
    # interview missing a whole round type (e.g. no Behavioral question at
    # all) doesn't silently drag "Communication" — and therefore the overall
    # score — down to zero for a dimension that was never even assessed.
    active = [d for d in dimensions if d.question_count > 0]
    active_weight = sum(weights.get(d.dimension, 0.0) for d in active)
    overall = (
        round(sum(d.score * weights.get(d.dimension, 0.0) for d in active) / active_weight, 1)
        if active_weight
        else 0.0
    )

    return InterviewScoreResult(overall=overall, dimensions=dimensions)
