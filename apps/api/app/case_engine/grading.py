"""Rubric + technical scoring for a completed CaseAttempt (or Project) —
spec sections 22-24, 41-42. Generalizes app/services/grading.py's flat,
self-assessed rubric mechanism (Phase 6) to weighted categories: each
category's score is either the learner's own checklist self-assessment
(checked-points / total-points, exactly like Phase 6) or, for a category
marked `is_technical` in its content, an OBJECTIVE score computed from real
ExerciseAttempt pass/fail — spec section 23's "use actual execution/testing
where possible... do not score only based on written explanations."

Pure functions only — no DB access, no session. The DB-aware lookup of
which required exercises actually passed lives in the calling service
(app/services/case_service.py), which is what makes this module trivially
unit-testable without a database.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryScore:
    category: str
    weight: float
    earned_points: float
    total_points: float
    pct: float  # 0-100 — this category's own percentage, before weighting
    is_technical: bool = False


@dataclass
class ScoreResult:
    overall: float  # 0-100
    categories: list[CategoryScore] = field(default_factory=list)


def score_rubric(
    rubric: list[dict],
    rubric_selections: dict[str, list[str]],
    *,
    technical_pct: float | None = None,
) -> ScoreResult:
    """`rubric` is the Case/ProjectTemplate's own `rubric` JSON
    (`[{category, weight, criteria: [{criterion, points}], is_technical}]`).
    `rubric_selections` is `{category: [criterion, ...]}` — which criteria
    the learner checked off as satisfied for each non-technical category.
    `technical_pct` is the objectively-computed 0-100 score for whichever
    category (if any) has `is_technical: true` — required_exercise_slugs
    passed / required_exercise_slugs total, computed by the caller.
    """
    categories: list[CategoryScore] = []

    for category_spec in rubric:
        name = category_spec["category"]
        weight = category_spec["weight"]
        criteria = category_spec.get("criteria", [])
        is_technical = category_spec.get("is_technical", False)
        total_points = sum(c["points"] for c in criteria)

        if is_technical and technical_pct is not None:
            pct = technical_pct
            earned = round(pct / 100 * total_points, 2) if total_points else 0.0
        else:
            selected = set(rubric_selections.get(name, []))
            earned = sum(c["points"] for c in criteria if c["criterion"] in selected)
            pct = round(earned / total_points * 100, 1) if total_points else 0.0

        categories.append(
            CategoryScore(
                category=name,
                weight=weight,
                earned_points=earned,
                total_points=total_points,
                pct=pct,
                is_technical=is_technical,
            )
        )

    overall = round(sum(cat.pct * cat.weight / 100 for cat in categories), 1)
    return ScoreResult(overall=overall, categories=categories)


def technical_category_name(rubric: list[dict]) -> str | None:
    """The name of the rubric category (if any) whose score should come from
    real exercise-attempt pass/fail rather than self-assessment."""
    for category_spec in rubric:
        if category_spec.get("is_technical"):
            return category_spec["category"]
    return None
