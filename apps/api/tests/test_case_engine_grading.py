"""Unit tests for the Phase 8 Case/Project rubric scoring + deterministic
feedback engine (app/case_engine/grading.py, app/case_engine/feedback.py) —
pure, DB-free functions, so these run with no fixtures at all."""

from __future__ import annotations

from app.case_engine.feedback import build_feedback
from app.case_engine.grading import score_rubric, technical_category_name

RUBRIC = [
    {
        "category": "Problem Framing",
        "weight": 40,
        "criteria": [
            {"criterion": "Identifies the right metric", "points": 60},
            {"criterion": "Scopes the timeframe", "points": 40},
        ],
    },
    {
        "category": "Technical Analysis",
        "weight": 60,
        "is_technical": True,
        "criteria": [
            {"criterion": "Uses window functions correctly", "points": 100},
        ],
    },
]


class TestScoreRubric:
    def test_full_self_assessed_credit(self) -> None:
        result = score_rubric(
            RUBRIC,
            {"Problem Framing": ["Identifies the right metric", "Scopes the timeframe"]},
            technical_pct=100.0,
        )
        assert result.overall == 100.0
        framing = next(c for c in result.categories if c.category == "Problem Framing")
        assert framing.pct == 100.0
        assert framing.earned_points == 100

    def test_partial_self_assessed_credit(self) -> None:
        result = score_rubric(
            RUBRIC, {"Problem Framing": ["Scopes the timeframe"]}, technical_pct=100.0
        )
        framing = next(c for c in result.categories if c.category == "Problem Framing")
        assert framing.pct == 40.0
        # overall = 40*0.4 + 100*0.6 = 16 + 60 = 76
        assert result.overall == 76.0

    def test_no_criteria_checked_scores_zero_for_that_category(self) -> None:
        result = score_rubric(RUBRIC, {}, technical_pct=100.0)
        framing = next(c for c in result.categories if c.category == "Problem Framing")
        assert framing.pct == 0.0
        assert framing.earned_points == 0

    def test_unrecognized_criterion_ignored(self) -> None:
        result = score_rubric(RUBRIC, {"Problem Framing": ["not a real criterion"]}, technical_pct=100.0)
        framing = next(c for c in result.categories if c.category == "Problem Framing")
        assert framing.pct == 0.0

    def test_technical_category_uses_objective_pct_not_self_assessment(self) -> None:
        # Even if the learner "checks off" the technical criterion themselves,
        # the objective technical_pct always wins for an is_technical category.
        result = score_rubric(
            RUBRIC,
            {
                "Problem Framing": ["Identifies the right metric", "Scopes the timeframe"],
                "Technical Analysis": ["Uses window functions correctly"],
            },
            technical_pct=0.0,
        )
        technical = next(c for c in result.categories if c.category == "Technical Analysis")
        assert technical.pct == 0.0
        assert technical.earned_points == 0.0

    def test_technical_category_falls_back_to_self_assessment_when_pct_is_none(self) -> None:
        # No required_exercise_slugs configured (technical_pct=None) -> even an
        # is_technical category is scored from the learner's own checklist —
        # the same convention ProjectService.submit_project relies on, since
        # ProjectTemplate has no required_exercise_slugs concept at all.
        result = score_rubric(
            RUBRIC,
            {"Technical Analysis": ["Uses window functions correctly"]},
            technical_pct=None,
        )
        technical = next(c for c in result.categories if c.category == "Technical Analysis")
        assert technical.pct == 100.0

    def test_weighting_combines_categories_correctly(self) -> None:
        result = score_rubric(
            RUBRIC,
            {"Problem Framing": ["Identifies the right metric"]},  # 60/100 = 60%
            technical_pct=50.0,
        )
        # overall = 60*0.4 + 50*0.6 = 24 + 30 = 54
        assert result.overall == 54.0


class TestTechnicalCategoryName:
    def test_returns_the_is_technical_category(self) -> None:
        assert technical_category_name(RUBRIC) == "Technical Analysis"

    def test_returns_none_when_no_category_is_technical(self) -> None:
        rubric = [{"category": "Communication", "weight": 100, "criteria": []}]
        assert technical_category_name(rubric) is None


class TestBuildFeedback:
    def test_strong_category_goes_to_what_went_well(self) -> None:
        result = score_rubric(RUBRIC, {}, technical_pct=90.0)
        feedback = build_feedback(result)
        assert any("Technical Analysis" in item for item in feedback.what_went_well)

    def test_weak_category_goes_to_what_missed_and_technical_issues(self) -> None:
        result = score_rubric(RUBRIC, {}, technical_pct=10.0)
        feedback = build_feedback(result)
        assert any("Technical Analysis" in item for item in feedback.what_missed)
        assert any("Technical Analysis" in item for item in feedback.technical_issues)

    def test_weak_business_category_bucketed_as_business_reasoning(self) -> None:
        result = score_rubric(RUBRIC, {}, technical_pct=90.0)  # Problem Framing left at 0%
        feedback = build_feedback(result)
        assert any("Problem Framing" in item for item in feedback.business_reasoning_issues)

    def test_mid_range_category_is_neither_well_nor_missed(self) -> None:
        rubric = [{"category": "Communication", "weight": 100, "criteria": [{"criterion": "A", "points": 100}]}]
        result = score_rubric(rubric, {"Communication": []}, technical_pct=None)
        # Force a mid-range score by hand-checking half the points via two criteria
        rubric = [
            {
                "category": "Communication",
                "weight": 100,
                "criteria": [{"criterion": "A", "points": 70}, {"criterion": "B", "points": 30}],
            }
        ]
        result = score_rubric(rubric, {"Communication": ["A"]}, technical_pct=None)
        assert result.categories[0].pct == 70.0
        feedback = build_feedback(result)
        assert feedback.what_went_well == []
        assert feedback.what_missed == []
