from app.python_lab.evaluation import TestOutcome, score_attempt


def _outcome(*, passed: bool, name: str = "Correct result") -> TestOutcome:
    return TestOutcome(name=name, passed=passed, is_hidden=False, message="")


class TestScoreAttempt:
    def test_full_correctness_and_no_hidden_tests_scores_100(self):
        result = score_attempt(
            correctness_outcome=_outcome(passed=True),
            hidden_outcomes=[],
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )
        assert result.passed is True
        assert result.score == 100.0

    def test_failed_correctness_scores_zero_regardless_of_hidden_tests(self):
        result = score_attempt(
            correctness_outcome=_outcome(passed=False),
            hidden_outcomes=[_outcome(passed=True, name="edge 1")],
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )
        assert result.passed is False
        assert result.score == 0.0

    def test_partial_hidden_test_failures_reduce_score(self):
        result = score_attempt(
            correctness_outcome=_outcome(passed=True),
            hidden_outcomes=[_outcome(passed=True, name="edge 1"), _outcome(passed=False, name="edge 2")],
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )
        # 70 (correctness) + 15*0.5 (half the hidden tests) + 10 (efficiency) + 5 (explanation)
        assert result.score == 92.5
        assert result.passed is True

    def test_much_slower_execution_loses_efficiency_credit_but_still_passes(self):
        result = score_attempt(
            correctness_outcome=_outcome(passed=True),
            hidden_outcomes=[],
            student_execution_time_ms=1000,
            reference_execution_time_ms=50,  # 20x slower, well above the noise floor
        )
        assert result.passed is True
        assert result.score == 90.0  # loses the full 10-point efficiency component

    def test_sub_noise_floor_timing_never_loses_efficiency_credit(self):
        """Regression test for a real, reproduced flake: two near-identical,
        very-fast kernel executions can differ by a few ms purely from OS/
        process scheduling jitter — a ratio-based comparison of sub-50ms
        times isn't a real efficiency signal. Reproduced directly: 25 back-
        to-back submissions of provably-correct code scored 100 twenty-four
        times and 95 once. See MIN_MEANINGFUL_TIME_MS's docstring."""
        result = score_attempt(
            correctness_outcome=_outcome(passed=True),
            hidden_outcomes=[],
            student_execution_time_ms=8,
            reference_execution_time_ms=2,  # a 4x ratio — would have lost credit pre-fix
        )
        assert result.score == 100.0

    def test_a_genuinely_slow_submission_still_loses_credit_even_with_a_fast_reference(self):
        """The noise-floor guard must not blanket-exempt every submission —
        only when BOTH sides are tiny. A student time far above the floor
        is still penalized normally."""
        result = score_attempt(
            correctness_outcome=_outcome(passed=True),
            hidden_outcomes=[],
            student_execution_time_ms=500,
            reference_execution_time_ms=2,
        )
        assert result.score < 100.0
