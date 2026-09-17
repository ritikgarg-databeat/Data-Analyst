"""Unit tests for the Phase 9 pure interview engines (app/interview_engine/) —
scoring, readiness, weakness detection, adaptive selection, and plan
generation. All pure, DB-free functions — no fixtures needed."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.interview_engine.plan import generate_plan
from app.interview_engine.readiness import CompletedInterview, compute_readiness
from app.interview_engine.scoring import ScoredQuestion, score_interview
from app.interview_engine.selection import HistoryEntry, QuestionCandidate, select_next_question
from app.interview_engine.spaced_review import ReviewItem, due_reviews, interval_days_for
from app.interview_engine.weakness import AttemptSignal, CommunicationSignal, detect_communication_gap, detect_weaknesses


class TestScoring:
    def test_sql_questions_score_technical_and_efficiency(self) -> None:
        result = score_interview(
            [ScoredQuestion(interview_type="SQL", score=100.0, time_limit_seconds=600, time_spent_seconds=300)]
        )
        technical = next(d for d in result.dimensions if d.dimension == "Technical Correctness")
        efficiency = next(d for d in result.dimensions if d.dimension == "Efficiency")
        assert technical.score == 100.0
        assert efficiency.score == 100.0  # well under the time limit
        assert result.overall == 100.0

    def test_efficiency_penalized_when_over_time(self) -> None:
        result = score_interview(
            [ScoredQuestion(interview_type="SQL", score=100.0, time_limit_seconds=100, time_spent_seconds=140)]
        )
        efficiency = next(d for d in result.dimensions if d.dimension == "Efficiency")
        assert 0 < efficiency.score < 100

    def test_no_time_limit_contributes_no_efficiency_signal(self) -> None:
        result = score_interview([ScoredQuestion(interview_type="SQL", score=80.0, time_limit_seconds=None)])
        efficiency = next(d for d in result.dimensions if d.dimension == "Efficiency")
        assert efficiency.question_count == 0

    def test_behavioral_scores_only_communication_and_problem_solving(self) -> None:
        result = score_interview([ScoredQuestion(interview_type="BEHAVIORAL", score=90.0)])
        comm = next(d for d in result.dimensions if d.dimension == "Communication")
        problem = next(d for d in result.dimensions if d.dimension == "Problem Solving")
        technical = next(d for d in result.dimensions if d.dimension == "Technical Correctness")
        assert comm.score == 90.0
        assert problem.score == 90.0
        assert technical.question_count == 0

    def test_missing_dimension_does_not_drag_overall_to_zero(self) -> None:
        # Only a SQL question answered — no Behavioral/Business question at
        # all. Overall should reflect just the dimensions actually touched,
        # not be diluted by untouched ones defaulting to 0.
        result = score_interview([ScoredQuestion(interview_type="SQL", score=100.0)])
        assert result.overall == 100.0

    def test_custom_rubric_weights(self) -> None:
        result = score_interview(
            [ScoredQuestion(interview_type="SQL", score=100.0), ScoredQuestion(interview_type="BEHAVIORAL", score=0.0)],
            rubric_weights={"Technical Correctness": 90.0, "Communication": 10.0},
        )
        # Technical Correctness 100 * 90 + Communication 0 * 10, over active weight 100 -> 90
        assert result.overall == 90.0


class TestReadiness:
    def test_combines_mastery_and_recent_performance(self) -> None:
        now = datetime.now(UTC)
        result = compute_readiness(
            skill_mastery_scores=[80.0, 90.0],
            recent_interviews=[CompletedInterview(overall_score=70.0, completed_at=now)],
        )
        assert result.mastery_component == 85.0
        assert result.recent_performance_component == 70.0
        assert 0 < result.overall_score <= 100

    def test_single_interview_cannot_be_capped_against_itself(self) -> None:
        now = datetime.now(UTC)
        result = compute_readiness([70.0], [CompletedInterview(overall_score=95.0, completed_at=now)])
        assert result.recent_performance_component == 95.0

    def test_one_outlier_interview_is_capped_relative_to_others(self) -> None:
        now = datetime.now(UTC)
        interviews = [
            CompletedInterview(overall_score=70.0, completed_at=now - timedelta(days=1)),
            CompletedInterview(overall_score=72.0, completed_at=now - timedelta(days=2)),
            CompletedInterview(overall_score=10.0, completed_at=now - timedelta(days=3)),  # one bad day
        ]
        result = compute_readiness([80.0], interviews)
        # Without capping, the recency-weighted average would be dragged much
        # closer to the erratic 10 than a capped computation allows.
        uncapped_style = sum(i.overall_score for i in interviews) / len(interviews)
        assert result.recent_performance_component > uncapped_style

    def test_consistency_penalizes_erratic_scores(self) -> None:
        now = datetime.now(UTC)
        steady = compute_readiness(
            [70.0],
            [
                CompletedInterview(overall_score=70.0, completed_at=now),
                CompletedInterview(overall_score=72.0, completed_at=now - timedelta(days=1)),
            ],
        )
        erratic = compute_readiness(
            [70.0],
            [
                CompletedInterview(overall_score=95.0, completed_at=now),
                CompletedInterview(overall_score=20.0, completed_at=now - timedelta(days=1)),
            ],
        )
        assert steady.consistency_component > erratic.consistency_component

    def test_breakdown_averages_per_interview_type(self) -> None:
        now = datetime.now(UTC)
        result = compute_readiness(
            [70.0],
            [
                CompletedInterview(overall_score=80.0, completed_at=now, interview_type_scores={"SQL": 90.0}),
                CompletedInterview(
                    overall_score=60.0, completed_at=now - timedelta(days=1), interview_type_scores={"SQL": 70.0}
                ),
            ],
        )
        assert result.breakdown["SQL"] == 80.0

    def test_no_history_at_all_is_zero_not_an_error(self) -> None:
        result = compute_readiness([], [])
        assert result.overall_score == 0.0


class TestWeaknessDetection:
    def test_knowledge_gap_from_repeated_conceptual_failures(self) -> None:
        signals = [
            AttemptSignal(interview_type="STATISTICS", is_conceptual=True, is_execution=False, is_rubric_scored=False, score=30.0)
            for _ in range(3)
        ]
        findings = detect_weaknesses(signals)
        assert any(f.gap_type == "Knowledge" and f.interview_type == "STATISTICS" for f in findings)

    def test_execution_gap_from_hidden_test_misses(self) -> None:
        signals = [
            AttemptSignal(
                interview_type="SQL",
                is_conceptual=False,
                is_execution=True,
                is_rubric_scored=False,
                score=85.0,
                hidden_tests_passed=1,
                hidden_tests_total=3,
            )
            for _ in range(2)
        ]
        findings = detect_weaknesses(signals)
        assert any(f.gap_type == "Execution" and f.interview_type == "SQL" for f in findings)

    def test_reasoning_gap_from_low_rubric_scores(self) -> None:
        signals = [
            AttemptSignal(
                interview_type="BUSINESS_ANALYTICS", is_conceptual=False, is_execution=False, is_rubric_scored=True, score=40.0
            )
            for _ in range(2)
        ]
        findings = detect_weaknesses(signals)
        assert any(f.gap_type == "Reasoning" for f in findings)

    def test_speed_gap_from_correct_but_slow_answers(self) -> None:
        signals = [
            AttemptSignal(
                interview_type="PYTHON",
                is_conceptual=False,
                is_execution=True,
                is_rubric_scored=False,
                score=90.0,
                time_limit_seconds=100,
                time_spent_seconds=200,
            )
            for _ in range(2)
        ]
        findings = detect_weaknesses(signals)
        assert any(f.gap_type == "Speed" for f in findings)

    def test_single_failure_is_not_enough_to_flag(self) -> None:
        signals = [
            AttemptSignal(interview_type="SQL", is_conceptual=True, is_execution=False, is_rubric_scored=False, score=10.0)
        ]
        assert detect_weaknesses(signals) == []

    def test_communication_gap(self) -> None:
        signals = [
            CommunicationSignal(interview_type="BEHAVIORAL", category_scores={"Communication": 40.0}),
            CommunicationSignal(interview_type="BEHAVIORAL", category_scores={"Communication": 45.0}),
        ]
        finding = detect_communication_gap(signals)
        assert finding is not None
        assert finding.gap_type == "Communication"

    def test_no_communication_gap_when_scores_are_fine(self) -> None:
        signals = [CommunicationSignal(interview_type="BEHAVIORAL", category_scores={"Communication": 90.0})]
        assert detect_communication_gap(signals) is None


class TestAdaptiveSelection:
    def test_prefers_unseen_question(self) -> None:
        candidates = [
            QuestionCandidate(id="q1", interview_type="SQL", difficulty="INTERMEDIATE"),
            QuestionCandidate(id="q2", interview_type="SQL", difficulty="INTERMEDIATE"),
        ]
        history = [HistoryEntry(question_id="q1", interview_type="SQL", difficulty="INTERMEDIATE", score=90.0)]
        chosen = select_next_question(candidates, history, "SQL")
        assert chosen is not None
        assert chosen.id == "q2"

    def test_escalates_difficulty_after_a_fast_high_score(self) -> None:
        candidates = [
            QuestionCandidate(id="easy", interview_type="SQL", difficulty="INTERMEDIATE"),
            QuestionCandidate(id="hard", interview_type="SQL", difficulty="ADVANCED"),
        ]
        history = [
            HistoryEntry(
                question_id="answered",
                interview_type="SQL",
                difficulty="INTERMEDIATE",
                score=95.0,
                time_limit_seconds=600,
                time_spent_seconds=200,
            )
        ]
        chosen = select_next_question(candidates, history, "SQL")
        assert chosen is not None
        assert chosen.difficulty == "ADVANCED"

    def test_steps_back_after_a_failure(self) -> None:
        candidates = [
            QuestionCandidate(id="med", interview_type="SQL", difficulty="INTERMEDIATE"),
            QuestionCandidate(id="hard", interview_type="SQL", difficulty="ADVANCED"),
        ]
        history = [
            HistoryEntry(question_id="answered", interview_type="SQL", difficulty="ADVANCED", score=20.0)
        ]
        chosen = select_next_question(candidates, history, "SQL")
        assert chosen is not None
        assert chosen.difficulty == "INTERMEDIATE"

    def test_allows_repeats_only_once_pool_is_exhausted_and_never_a_mastered_one_first(self) -> None:
        candidates = [QuestionCandidate(id="q1", interview_type="SQL", difficulty="INTERMEDIATE")]
        history = [HistoryEntry(question_id="q1", interview_type="SQL", difficulty="INTERMEDIATE", score=95.0)]
        # Only one candidate exists and it's already mastered — still returned (last resort), not None.
        chosen = select_next_question(candidates, history, "SQL")
        assert chosen is not None
        assert chosen.id == "q1"

    def test_returns_none_for_a_type_with_no_candidates(self) -> None:
        assert select_next_question([], [], "SQL") is None


class TestPlanGeneration:
    def test_plan_is_seven_days_ending_in_mock_then_review(self) -> None:
        from app.interview_engine.weakness import WeaknessFinding

        readiness = compute_readiness([70.0], [])
        weaknesses = [
            WeaknessFinding(gap_type="Knowledge", interview_type="STATISTICS", occurrences=3, average_score=40.0, detail="d")
        ]
        days = generate_plan(weaknesses, readiness)
        assert len(days) == 7
        assert days[0].focus_area == "STATISTICS"
        assert days[5].task_type == "MOCK_INTERVIEW"
        assert days[6].task_type == "REVIEW"

    def test_plan_falls_back_to_readiness_breakdown_when_no_weaknesses_detected(self) -> None:
        readiness = compute_readiness(
            [70.0],
            [CompletedInterview(overall_score=70.0, completed_at=datetime.now(UTC), interview_type_scores={"SQL": 30.0, "PYTHON": 90.0})],
        )
        days = generate_plan([], readiness)
        # SQL is the lowest-scoring domain in the breakdown -> should be prioritized.
        assert days[0].focus_area == "SQL"


class TestSpacedReview:
    def test_interval_grows_with_score(self) -> None:
        assert interval_days_for(30.0) == 1.0
        assert interval_days_for(70.0) == 3.0
        assert interval_days_for(90.0) == 10.0
        assert interval_days_for(100.0) == 30.0

    def test_consecutive_good_answers_stretch_the_interval_up_to_a_cap(self) -> None:
        base = interval_days_for(90.0, consecutive_good=1)
        stretched = interval_days_for(90.0, consecutive_good=3)
        capped = interval_days_for(90.0, consecutive_good=100)
        assert stretched > base
        assert capped == base * 2.0  # MAX_STREAK_MULTIPLIER

    def test_a_miss_never_earns_a_streak_stretch(self) -> None:
        assert interval_days_for(40.0, consecutive_good=5) == interval_days_for(40.0, consecutive_good=0)

    def test_a_question_answered_moments_ago_is_not_yet_due(self) -> None:
        now = datetime.now(UTC)
        items = [ReviewItem(question_id="q1", interview_type="SQL", last_score=40.0, last_attempted_at=now)]
        assert due_reviews(items, now=now) == []

    def test_a_missed_question_becomes_due_after_its_short_interval_elapses(self) -> None:
        now = datetime.now(UTC)
        items = [
            ReviewItem(
                question_id="q1", interview_type="SQL", last_score=40.0, last_attempted_at=now - timedelta(days=2)
            )
        ]
        due = due_reviews(items, now=now)
        assert len(due) == 1
        assert due[0].question_id == "q1"
        assert due[0].days_overdue > 0

    def test_a_mastered_question_is_not_due_after_only_a_few_days(self) -> None:
        now = datetime.now(UTC)
        items = [
            ReviewItem(
                question_id="q1", interview_type="SQL", last_score=100.0, last_attempted_at=now - timedelta(days=5)
            )
        ]
        assert due_reviews(items, now=now) == []

    def test_ordering_prioritizes_worse_scores_over_more_overdue_mastered_items(self) -> None:
        now = datetime.now(UTC)
        items = [
            ReviewItem(
                question_id="mastered-but-old",
                interview_type="SQL",
                last_score=100.0,
                last_attempted_at=now - timedelta(days=60),
            ),
            ReviewItem(
                question_id="missed-recently",
                interview_type="SQL",
                last_score=20.0,
                last_attempted_at=now - timedelta(days=2),
            ),
        ]
        due = due_reviews(items, now=now)
        assert due[0].question_id == "missed-recently"

    def test_limit_caps_the_returned_queue(self) -> None:
        now = datetime.now(UTC)
        items = [
            ReviewItem(
                question_id=f"q{i}", interview_type="SQL", last_score=10.0, last_attempted_at=now - timedelta(days=5)
            )
            for i in range(10)
        ]
        assert len(due_reviews(items, now=now, limit=3)) == 3
