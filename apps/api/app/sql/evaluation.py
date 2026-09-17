"""Result-based SQL exercise evaluation.

Never compares SQL text — two different queries can correctly solve the
same problem. Instead: execute the student's query and a reference
`solution_query` against the same dataset, then compare the *results*.

Two kinds of checks, both derived from query results rather than
per-exercise hand-authored expected data (which would be brittle and hard
to keep in sync with the dataset):

1. Full-result match (always run) — row count, column count, and cell
   values (row-order and numeric-tolerance configurable) between the
   student's result and `solution_query`'s result. This is "Correctness."
2. Row checks (optional, exercise-authored `sql_hidden_tests`) — a small
   reference query returns one or more "key" columns plus an expected
   value column; the evaluator looks up the matching row(s) in the
   student's *own* result by key and checks the value. This is how an
   exercise author targets a specific edge case (e.g. "a customer with
   zero orders should still appear with revenue 0") without needing a
   separate physical dataset per test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.sql.engines.base import SqlExecutionResult

# A narrow, deliberately-scoped anti-cheat check — NOT a general text-based
# grader (this evaluator is otherwise 100% result-based; see module
# docstring). It exists only because a real, live-reproduced gap was found:
# when an exercise's own canonical answer is an empty result set (e.g. "no
# duplicate order_ids exist"), a student query with an unconditionally-false
# filter (e.g. `WHERE 1=0`) also returns zero rows and matches perfectly,
# passing with full credit despite performing none of the exercise's actual
# logic. No purely result-based check can ever distinguish "correctly
# empty" from "vacuously empty" (an absence-check is trivially satisfied by
# an empty result either way) — this catches the specific, unambiguous,
# extremely-unlikely-to-appear-in-a-genuine-query literal patterns real
# vacuous submissions actually use.
_ALWAYS_FALSE_PATTERN = re.compile(r"\b(1\s*=\s*0|0\s*=\s*1)\b", re.IGNORECASE)

CORRECTNESS_WEIGHT = 70.0
EDGE_CASE_WEIGHT = 15.0
EFFICIENCY_WEIGHT = 10.0
EXPLANATION_WEIGHT = 5.0  # not auto-gradable without an execution-independent grader — flat credit for now
PASS_THRESHOLD = CORRECTNESS_WEIGHT  # getting the core result right is enough to pass

# Below this, an execution-time difference is measurement noise, not a real
# efficiency signal — see app/python_lab/evaluation.py's identical constant
# for the reproduced flake that motivated it (25 back-to-back submissions of
# provably-correct code scored 100 all but once, purely from timing jitter
# between two sub-20ms executions).
MIN_MEANINGFUL_TIME_MS = 50


@dataclass
class HiddenTestSpec:
    name: str
    query: str
    key_columns: int = (
        1  # leading columns of `query`'s result are the lookup key; the last is the expected value
    )


@dataclass
class TestOutcome:
    name: str
    passed: bool
    is_hidden: bool
    message: str


@dataclass
class EvaluationResult:
    score: float  # 0-100
    passed: bool
    correctness_passed: bool
    test_outcomes: list[TestOutcome] = field(default_factory=list)
    student_error: str | None = None


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cells_equal(a: object, b: object, tolerance: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if _is_number(a) and _is_number(b):
        return abs(float(a) - float(b)) <= tolerance
    return a == b


def _row_key(row: list, tolerance: float) -> tuple:
    """A comparable, order-independent sort/lookup key for a row."""
    normalized = []
    for value in row:
        if _is_number(value) and tolerance > 0:
            normalized.append(round(float(value) / tolerance) * tolerance)
        else:
            normalized.append(value)
    return tuple(str(v) for v in normalized)


def compare_full_result(
    student: SqlExecutionResult,
    expected: SqlExecutionResult,
    *,
    ignore_row_order: bool = True,
    numeric_tolerance: float = 0.01,
    student_query: str | None = None,
) -> TestOutcome:
    name = "Correct results"
    if len(expected.rows) == 0 and student_query and _ALWAYS_FALSE_PATTERN.search(student_query):
        return TestOutcome(
            name,
            False,
            is_hidden=False,
            message=(
                "Your query returned zero rows, matching this exercise's expected empty result — but it "
                "contains an unconditionally-false condition, which returns zero rows regardless of "
                "whether your actual logic is correct. Write a query that would return real rows for a "
                "genuinely matching case, even if none exist in this dataset."
            ),
        )
    if len(student.columns) != len(expected.columns):
        return TestOutcome(
            name,
            False,
            is_hidden=False,
            message=(
                f"Expected {len(expected.columns)} column(s) in the result, "
                f"your query returned {len(student.columns)}."
            ),
        )
    if len(student.rows) != len(expected.rows):
        return TestOutcome(
            name,
            False,
            is_hidden=False,
            message=f"Expected {len(expected.rows)} row(s), your query returned {len(student.rows)}.",
        )

    student_rows, expected_rows = student.rows, expected.rows
    if ignore_row_order:
        student_rows = sorted(student_rows, key=lambda r: _row_key(r, numeric_tolerance))
        expected_rows = sorted(expected_rows, key=lambda r: _row_key(r, numeric_tolerance))

    for row_index, (srow, erow) in enumerate(zip(student_rows, expected_rows, strict=True)):
        for col_index, (svalue, evalue) in enumerate(zip(srow, erow, strict=True)):
            if not _cells_equal(svalue, evalue, numeric_tolerance):
                position = "a row" if ignore_row_order else f"row {row_index + 1}"
                return TestOutcome(
                    name,
                    False,
                    is_hidden=False,
                    message=f"Values differ in column {col_index + 1} of {position} of your result.",
                )

    return TestOutcome(name, True, is_hidden=False, message="Your result matches the expected output.")


def run_hidden_row_check(
    student: SqlExecutionResult, test: HiddenTestSpec, reference: SqlExecutionResult
) -> TestOutcome:
    """`reference` is the already-executed result of `test.query`. Each of its
    rows is `[*key_columns, expected_value]`; verifies the matching row(s)
    exist in the student's result with the correct trailing value."""
    if not reference.is_success:
        return TestOutcome(test.name, False, is_hidden=True, message="Could not evaluate this hidden test.")

    # The expected "value" is always the LAST column of each row (not
    # necessarily immediately after the key columns) — this tolerates a
    # student result with a few extra columns beyond key+value.
    student_index: dict[tuple, object] = {}
    for row in student.rows:
        if len(row) <= test.key_columns:
            continue
        key = tuple(str(v) for v in row[: test.key_columns])
        student_index[key] = row[-1]

    for ref_row in reference.rows:
        key = tuple(str(v) for v in ref_row[: test.key_columns])
        expected_value = ref_row[-1]
        if key not in student_index:
            return TestOutcome(test.name, False, is_hidden=True, message="Failed on a hidden edge case.")
        if not _cells_equal(student_index[key], expected_value, 0.01):
            return TestOutcome(test.name, False, is_hidden=True, message="Failed on a hidden edge case.")

    return TestOutcome(test.name, True, is_hidden=True, message="Passed.")


def score_attempt(
    *,
    correctness_outcome: TestOutcome,
    hidden_outcomes: list[TestOutcome],
    student_execution_time_ms: int,
    reference_execution_time_ms: int,
) -> EvaluationResult:
    correctness_fraction = 1.0 if correctness_outcome.passed else 0.0

    if hidden_outcomes:
        edge_case_fraction = sum(1 for o in hidden_outcomes if o.passed) / len(hidden_outcomes)
    else:
        edge_case_fraction = 1.0

    if reference_execution_time_ms <= 0 or (
        student_execution_time_ms <= MIN_MEANINGFUL_TIME_MS
        and reference_execution_time_ms <= MIN_MEANINGFUL_TIME_MS
    ):
        efficiency_fraction = 1.0
    else:
        ratio = student_execution_time_ms / reference_execution_time_ms
        if ratio <= 3:
            efficiency_fraction = 1.0
        elif ratio >= 10:
            efficiency_fraction = 0.0
        else:
            efficiency_fraction = 1.0 - (ratio - 3) / 7

    explanation_fraction = 1.0  # flat credit — see module docstring

    # Efficiency/explanation only count once the core result is actually correct.
    if not correctness_outcome.passed:
        edge_case_fraction = 0.0
        efficiency_fraction = 0.0
        explanation_fraction = 0.0

    score = (
        CORRECTNESS_WEIGHT * correctness_fraction
        + EDGE_CASE_WEIGHT * edge_case_fraction
        + EFFICIENCY_WEIGHT * efficiency_fraction
        + EXPLANATION_WEIGHT * explanation_fraction
    )
    score = round(score, 1)

    return EvaluationResult(
        score=score,
        passed=score >= PASS_THRESHOLD,
        correctness_passed=correctness_outcome.passed,
        test_outcomes=[correctness_outcome, *hidden_outcomes],
    )
