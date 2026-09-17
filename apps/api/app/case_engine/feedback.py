"""Deterministic post-submission feedback (spec section 54) — no AI/LLM
grading (explicitly out of scope until Phase 11's "AI... case-study
evaluator"). Every bucket is derived purely from the rubric category scores
already computed by app/case_engine/grading.py, using the category-name
conventions this platform's own case content follows (spec section 22's
nine category names) — an unrecognized category name still gets bucketed
into general well/missed feedback, it just skips the more specific
technical/business/communication buckets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.case_engine.grading import CategoryScore, ScoreResult

STRONG_THRESHOLD = 80.0
WEAK_THRESHOLD = 60.0

_TECHNICAL_HINTS = ("technical", "data quality", "statistical")
_BUSINESS_HINTS = ("problem framing", "analytical approach", "insight", "business impact")
_COMMUNICATION_HINTS = ("recommendation", "communication")


@dataclass
class Feedback:
    what_went_well: list[str] = field(default_factory=list)
    what_missed: list[str] = field(default_factory=list)
    technical_issues: list[str] = field(default_factory=list)
    business_reasoning_issues: list[str] = field(default_factory=list)
    communication_issues: list[str] = field(default_factory=list)


def _matches(name: str, hints: tuple[str, ...]) -> bool:
    lowered = name.lower()
    return any(hint in lowered for hint in hints)


def build_feedback(score: ScoreResult) -> Feedback:
    feedback = Feedback()
    for cat in score.categories:
        _bucket_category(cat, feedback)
    return feedback


def _bucket_category(cat: CategoryScore, feedback: Feedback) -> None:
    if cat.pct >= STRONG_THRESHOLD:
        feedback.what_went_well.append(f"{cat.category} ({cat.pct:.0f}%)")
        return

    if cat.pct < WEAK_THRESHOLD:
        feedback.what_missed.append(f"{cat.category} ({cat.pct:.0f}%)")
        if _matches(cat.category, _TECHNICAL_HINTS):
            feedback.technical_issues.append(cat.category)
        elif _matches(cat.category, _BUSINESS_HINTS):
            feedback.business_reasoning_issues.append(cat.category)
        elif _matches(cat.category, _COMMUNICATION_HINTS):
            feedback.communication_issues.append(cat.category)
