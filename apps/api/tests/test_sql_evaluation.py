from app.sql.engines.base import ColumnInfo, SqlExecutionResult
from app.sql.evaluation import (
    HiddenTestSpec,
    compare_full_result,
    run_hidden_row_check,
    score_attempt,
)


def _result(rows: list[list], columns: list[str] | None = None) -> SqlExecutionResult:
    cols = columns or ([f"c{i}" for i in range(len(rows[0]))] if rows else [])
    return SqlExecutionResult(
        status="success",
        engine="duckdb",
        columns=[ColumnInfo(name=c, type="VARCHAR") for c in cols],
        rows=rows,
        row_count=len(rows),
    )


class TestCompareFullResult:
    def test_identical_rows_in_same_order_pass(self):
        student = _result([[1, "a"], [2, "b"]])
        expected = _result([[1, "a"], [2, "b"]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is True

    def test_row_order_is_ignored_by_default(self):
        student = _result([[2, "b"], [1, "a"]])
        expected = _result([[1, "a"], [2, "b"]])

        outcome = compare_full_result(student, expected, ignore_row_order=True)

        assert outcome.passed is True

    def test_row_order_matters_when_configured(self):
        student = _result([[2, "b"], [1, "a"]])
        expected = _result([[1, "a"], [2, "b"]])

        outcome = compare_full_result(student, expected, ignore_row_order=False)

        assert outcome.passed is False

    def test_row_count_mismatch_fails_with_a_safe_message(self):
        student = _result([[1, "a"]])
        expected = _result([[1, "a"], [2, "b"]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is False
        assert "2" in outcome.message  # reveals count, not the hidden values
        assert "b" not in outcome.message

    def test_column_count_mismatch_fails(self):
        student = _result([[1, "a", "extra"]])
        expected = _result([[1, "a"]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is False

    def test_numeric_values_within_tolerance_pass(self):
        student = _result([[100.004]])
        expected = _result([[100.0]])

        outcome = compare_full_result(student, expected, numeric_tolerance=0.01)

        assert outcome.passed is True

    def test_numeric_values_outside_tolerance_fail(self):
        student = _result([[100.5]])
        expected = _result([[100.0]])

        outcome = compare_full_result(student, expected, numeric_tolerance=0.01)

        assert outcome.passed is False

    def test_null_equals_null(self):
        student = _result([[None, "a"]])
        expected = _result([[None, "a"]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is True

    def test_null_does_not_equal_zero(self):
        student = _result([[0]])
        expected = _result([[None]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is False

    def test_exact_string_values_are_case_sensitive(self):
        student = _result([["Completed"]])
        expected = _result([["completed"]])

        outcome = compare_full_result(student, expected)

        assert outcome.passed is False


class TestVacuousEmptyResultIsRejected:
    """Regression tests for a real, live-reproduced bug: an exercise whose
    canonical answer is an empty result set (e.g. "no duplicate order_ids
    exist") used to give full correctness credit to ANY query returning zero
    rows with a matching column count — including a query with an
    unconditionally-false filter that performs none of the exercise's actual
    logic, confirmed against a real shipped exercise
    (de-sql-duplicate-order-id-check)."""

    def test_a_where_1_equals_0_submission_against_an_empty_expected_result_is_rejected(self):
        student = _result([], columns=["order_id", "occurrences"])
        expected = _result([], columns=["order_id", "occurrences"])

        outcome = compare_full_result(
            student,
            expected,
            student_query="SELECT order_id, COUNT(*) AS occurrences FROM orders WHERE 1=0 GROUP BY order_id",
        )

        assert outcome.passed is False
        assert "unconditionally-false" in outcome.message

    def test_a_where_0_equals_1_submission_is_also_rejected(self):
        student = _result([], columns=["x"])
        expected = _result([], columns=["x"])

        outcome = compare_full_result(student, expected, student_query="SELECT 1 AS x WHERE 0=1")

        assert outcome.passed is False

    def test_a_genuinely_correct_empty_result_query_still_passes(self):
        """The real, legitimate reference query for the same exercise —
        no always-false pattern — must still pass; this fix must not break
        a genuinely correct empty-result submission."""
        student = _result([], columns=["order_id", "occurrences"])
        expected = _result([], columns=["order_id", "occurrences"])

        outcome = compare_full_result(
            student,
            expected,
            student_query=(
                "SELECT order_id, COUNT(*) AS occurrences FROM orders "
                "GROUP BY order_id HAVING COUNT(*) > 1"
            ),
        )

        assert outcome.passed is True

    def test_a_where_1_equals_0_submission_against_a_non_empty_expected_result_is_unaffected(self):
        """The always-false check is scoped to the empty-expected-result
        case only — it must never fire when the exercise's real answer has
        rows (the row-count mismatch below already fails it correctly)."""
        student = _result([])
        expected = _result([[1, "a"]])

        outcome = compare_full_result(student, expected, student_query="SELECT * FROM t WHERE 1=0")

        assert outcome.passed is False
        assert "unconditionally-false" not in outcome.message


class TestHiddenRowCheck:
    def test_passes_when_student_result_contains_the_expected_keyed_value(self):
        student = _result([[1, "alice", 500.0], [2, "bob", 0.0]])
        reference = _result([[2, 0.0]])  # key=customer_id 2, expected value=0.0
        test = HiddenTestSpec(name="Zero-order customer shows 0", query="...", key_columns=1)

        outcome = run_hidden_row_check(student, test, reference)

        assert outcome.passed is True

    def test_fails_when_key_is_missing_from_student_result(self):
        student = _result([[1, "alice", 500.0]])
        reference = _result([[2, 0.0]])
        test = HiddenTestSpec(name="Zero-order customer shows 0", query="...", key_columns=1)

        outcome = run_hidden_row_check(student, test, reference)

        assert outcome.passed is False
        # The failure message must not leak the hidden expected value.
        assert "0.0" not in outcome.message

    def test_fails_when_value_is_wrong(self):
        student = _result([[2, "bob", 99.0]])
        reference = _result([[2, 0.0]])
        test = HiddenTestSpec(name="Zero-order customer shows 0", query="...", key_columns=1)

        outcome = run_hidden_row_check(student, test, reference)

        assert outcome.passed is False

    def test_supports_composite_keys(self):
        student = _result([["US", "2024-01", 100.0]])
        reference = _result([["US", "2024-01", 100.0]])
        test = HiddenTestSpec(name="Country-month revenue", query="...", key_columns=2)

        outcome = run_hidden_row_check(student, test, reference)

        assert outcome.passed is True


class TestScoreAttempt:
    def test_full_correctness_and_no_hidden_tests_scores_at_least_the_pass_threshold(self):
        correctness = _outcome(passed=True)

        result = score_attempt(
            correctness_outcome=correctness,
            hidden_outcomes=[],
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )

        assert result.passed is True
        assert result.score == 100.0  # correctness + full edge-case/efficiency/explanation credit

    def test_failed_correctness_fails_regardless_of_hidden_tests(self):
        correctness = _outcome(passed=False)
        hidden = [_outcome(passed=True, name="edge 1")]

        result = score_attempt(
            correctness_outcome=correctness,
            hidden_outcomes=hidden,
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )

        assert result.passed is False
        assert result.score == 0.0

    def test_partial_hidden_test_failures_reduce_score_but_can_still_pass(self):
        correctness = _outcome(passed=True)
        hidden = [_outcome(passed=True, name="edge 1"), _outcome(passed=False, name="edge 2")]

        result = score_attempt(
            correctness_outcome=correctness,
            hidden_outcomes=hidden,
            student_execution_time_ms=50,
            reference_execution_time_ms=50,
        )

        # 70 (correctness) + 15*0.5 (half the hidden tests) + 10 (efficiency) + 5 (explanation)
        assert result.score == 92.5
        assert result.passed is True  # correctness alone already clears the pass threshold

    def test_much_slower_query_loses_efficiency_credit_but_still_passes_on_correctness(self):
        correctness = _outcome(passed=True)

        result = score_attempt(
            correctness_outcome=correctness,
            hidden_outcomes=[],
            student_execution_time_ms=1000,
            reference_execution_time_ms=50,  # 20x slower
        )

        assert result.passed is True
        assert result.score == 90.0  # loses the full 10-point efficiency component

    def test_sub_noise_floor_timing_never_loses_efficiency_credit(self):
        """Regression test for a real, reproduced flake: two near-identical,
        very-fast executions can differ by a few ms purely from OS/process
        scheduling jitter — a ratio-based comparison of sub-50ms times isn't
        a real efficiency signal. See MIN_MEANINGFUL_TIME_MS's docstring."""
        correctness = _outcome(passed=True)

        result = score_attempt(
            correctness_outcome=correctness,
            hidden_outcomes=[],
            student_execution_time_ms=8,
            reference_execution_time_ms=2,  # a 4x ratio, but both are noise-floor tiny
        )

        assert result.score == 100.0


def _outcome(*, passed: bool, name: str = "Correct results"):
    from app.sql.evaluation import TestOutcome

    return TestOutcome(name=name, passed=passed, is_hidden=False, message="")
