"""Unit tests for the rubric-based scoring path added to app/services/grading.py
(Phase 6, spec section 46) — self-assessed rubric criteria produce a real,
deterministic score instead of falling back to a self-reported one."""

from __future__ import annotations

from app.content.schema import ExerciseContentFile, RubricCriterion
from app.services.grading import grade


def _content(**overrides) -> ExerciseContentFile:
    base = dict(
        slug="test-case",
        title="Test Case",
        description="A test case",
        exercise_type="BUSINESS_REASONING",
        difficulty="ADVANCED",
        points=25,
        prompt="Diagnose the issue.",
        explanation="A strong answer segments before hypothesizing.",
    )
    base.update(overrides)
    return ExerciseContentFile(**base)


class TestRubricGrading:
    def test_full_credit_when_all_criteria_checked(self) -> None:
        content = _content(
            rubric=[
                RubricCriterion(criterion="Checks the time trend", points=40),
                RubricCriterion(criterion="Segments by channel", points=60),
            ]
        )
        result = grade(
            content, "my answer", rubric_selections=["Checks the time trend", "Segments by channel"]
        )
        assert result.is_auto_graded is True
        assert result.score == 100.0
        assert result.is_correct is True

    def test_partial_credit_when_some_criteria_checked(self) -> None:
        content = _content(
            rubric=[
                RubricCriterion(criterion="Checks the time trend", points=40),
                RubricCriterion(criterion="Segments by channel", points=60),
            ]
        )
        result = grade(content, "my answer", rubric_selections=["Checks the time trend"])
        assert result.score == 40.0
        assert result.is_correct is False  # below the 70% pass threshold

    def test_no_criteria_checked_scores_zero(self) -> None:
        content = _content(rubric=[RubricCriterion(criterion="A", points=100)])
        result = grade(content, "my answer", rubric_selections=[])
        assert result.score == 0.0
        assert result.is_correct is False

    def test_pending_when_rubric_present_but_no_selections_yet(self) -> None:
        content = _content(rubric=[RubricCriterion(criterion="A", points=100)])
        result = grade(content, "my answer", rubric_selections=None)
        assert result.is_auto_graded is False
        assert result.score is None

    def test_unrecognized_criterion_string_ignored(self) -> None:
        content = _content(rubric=[RubricCriterion(criterion="A", points=100)])
        result = grade(content, "my answer", rubric_selections=["not-a-real-criterion"])
        assert result.score == 0.0

    def test_no_rubric_falls_back_to_existing_auto_gradable_path(self) -> None:
        content = _content(
            exercise_type="MULTIPLE_CHOICE",
            choices=["A", "B"],
            correct_answer="A",
        )
        result = grade(content, "A")
        assert result.is_auto_graded is True
        assert result.is_correct is True
        assert result.score == 100.0

    def test_no_rubric_non_gradable_type_unchanged(self) -> None:
        content = _content(exercise_type="DATA_INTERPRETATION")
        result = grade(content, "my answer")
        assert result.is_auto_graded is False
        assert result.score is None

    def test_pass_threshold_boundary(self) -> None:
        content = _content(
            rubric=[
                RubricCriterion(criterion="A", points=70),
                RubricCriterion(criterion="B", points=30),
            ]
        )
        exactly_70 = grade(content, "answer", rubric_selections=["A"])
        assert exactly_70.score == 70.0
        assert exactly_70.is_correct is True
