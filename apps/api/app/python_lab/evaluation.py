"""Result-based scoring for Python exercises — never compares source code
text (two different implementations can correctly solve the same problem),
mirroring `app/sql/evaluation.py`'s philosophy and weights exactly for
consistency across the platform's exercise types.

Grading compares the *value* of one named result variable (e.g. `result`)
between the student's kernel and a fresh kernel that ran the exercise's
reference `python_solution_code` — never diffing the source, always the
computed output. Optional hidden tests are Python assertion snippets run in
the student's OWN kernel (so they see the student's variables) — no
hardcoded expected values are needed since a hidden test can compute its
own reference value at grading time, live, from the same dataset."""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.python_lab.base import DataFrameSummary, PythonError, PythonVariable

CORRECTNESS_WEIGHT = 70.0
EDGE_CASE_WEIGHT = 15.0
EFFICIENCY_WEIGHT = 10.0
EXPLANATION_WEIGHT = 5.0
PASS_THRESHOLD = 70.0

# Below this, an execution-time difference is measurement noise (OS/process
# scheduling jitter), not a real efficiency signal — two runs of the exact
# same code can easily differ by a few ms. Found via a real, reproducible
# flake: 25 back-to-back submissions of provably-correct, identical-to-the-
# reference code scored 100 twenty-four times and 95 once, purely from
# timing jitter between two sub-20ms kernel executions. Only skip the ratio
# check when BOTH sides are within the noise floor — a genuinely slow
# submission (student time above the floor) is still penalized normally
# even when the reference itself happens to run in a few ms.
MIN_MEANINGFUL_TIME_MS = 50

CORRECTNESS_TEST_NAME = "Correct result"


@dataclass
class TestOutcome:
    name: str
    passed: bool
    is_hidden: bool
    message: str


@dataclass
class AttemptEvaluation:
    passed: bool
    score: float
    correctness_score: float
    edge_case_score: float
    efficiency_score: float
    explanation_score: float


def _values_equal(a: object, b: object, tolerance: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), abs_tol=tolerance, rel_tol=tolerance)
    return a == b


def _sort_key(value: object) -> tuple:
    """A total-order key that never raises on mixed types within a column —
    ranks by type first, so None/number/other never get compared directly
    against each other during a Python `sorted()` call."""
    if value is None:
        return (0, "")
    if isinstance(value, bool):
        return (1, value)
    if isinstance(value, (int, float)):
        return (2, round(float(value), 9))
    return (3, str(value))


def compare_dataframes(
    student: DataFrameSummary,
    reference: DataFrameSummary,
    *,
    numeric_tolerance: float,
    row_order_matters: bool,
) -> TestOutcome:
    name = CORRECTNESS_TEST_NAME
    student_cols = [c.name for c in student.columns]
    reference_cols = [c.name for c in reference.columns]

    if set(student_cols) != set(reference_cols):
        missing = sorted(set(reference_cols) - set(student_cols))
        extra = sorted(set(student_cols) - set(reference_cols))
        parts = []
        if missing:
            parts.append(f"missing column(s): {', '.join(missing)}")
        if extra:
            parts.append(f"unexpected column(s): {', '.join(extra)}")
        return TestOutcome(
            name,
            False,
            False,
            "Your result's columns don't match what's expected — " + "; ".join(parts) + ".",
        )

    if student.row_count != reference.row_count:
        return TestOutcome(
            name,
            False,
            False,
            f"Expected {reference.row_count} row(s) in the result, yours has {student.row_count}.",
        )

    student_idx = {c: i for i, c in enumerate(student_cols)}
    reference_idx = {c: i for i, c in enumerate(reference_cols)}
    student_rows = list(student.preview_rows)
    reference_rows = list(reference.preview_rows)

    if not row_order_matters:
        student_rows = sorted(
            student_rows, key=lambda r: tuple(_sort_key(r[student_idx[c]]) for c in reference_cols)
        )
        reference_rows = sorted(
            reference_rows, key=lambda r: tuple(_sort_key(r[reference_idx[c]]) for c in reference_cols)
        )

    for row_index, (srow, rrow) in enumerate(zip(student_rows, reference_rows, strict=True)):
        for col in reference_cols:
            svalue = srow[student_idx[col]]
            rvalue = rrow[reference_idx[col]]
            if not _values_equal(svalue, rvalue, numeric_tolerance):
                position = "a row" if not row_order_matters else f"row {row_index + 1}"
                return TestOutcome(
                    name, False, False, f"Values differ in column '{col}' of {position} of your result."
                )

    return TestOutcome(name, True, False, "Your result matches the expected output.")


def _compare_plain_values(
    student_value: object, reference_value: object, numeric_tolerance: float
) -> TestOutcome:
    name = CORRECTNESS_TEST_NAME
    if isinstance(reference_value, list):
        if not isinstance(student_value, list) or len(student_value) != len(reference_value):
            return TestOutcome(name, False, False, f"Expected a list of {len(reference_value)} item(s).")
        for s, r in zip(student_value, reference_value, strict=True):
            if not _values_equal(s, r, numeric_tolerance):
                return TestOutcome(name, False, False, "One or more items in your result list don't match.")
        return TestOutcome(name, True, False, "Your result matches the expected output.")

    if isinstance(reference_value, dict):
        if not isinstance(student_value, dict):
            return TestOutcome(name, False, False, "Expected a dict-shaped result.")
        if set(student_value) != set(reference_value):
            return TestOutcome(name, False, False, "Your result's keys don't match what's expected.")
        for key, rvalue in reference_value.items():
            if not _values_equal(student_value.get(key), rvalue, numeric_tolerance):
                return TestOutcome(name, False, False, f"The value for key '{key}' doesn't match.")
        return TestOutcome(name, True, False, "Your result matches the expected output.")

    if not _values_equal(student_value, reference_value, numeric_tolerance):
        return TestOutcome(name, False, False, "Your result doesn't match the expected value.")
    return TestOutcome(name, True, False, "Your result matches the expected output.")


def compare_result_variable(
    student: PythonVariable | None,
    reference: PythonVariable | None,
    *,
    result_variable: str,
    numeric_tolerance: float = 1e-6,
    row_order_matters: bool = False,
) -> TestOutcome:
    name = CORRECTNESS_TEST_NAME
    if reference is None:
        return TestOutcome(
            name,
            False,
            False,
            "This exercise's reference solution did not produce a result — please report this.",
        )
    if student is None:
        return TestOutcome(
            name, False, False, f"Your code did not define a variable named '{result_variable}'."
        )

    if reference.dataframe is not None:
        if student.dataframe is None:
            return TestOutcome(
                name,
                False,
                False,
                f"Expected '{result_variable}' to be a DataFrame, but it's a {student.type_name}.",
            )
        return compare_dataframes(
            student.dataframe,
            reference.dataframe,
            numeric_tolerance=numeric_tolerance,
            row_order_matters=row_order_matters,
        )

    if student.dataframe is not None:
        return TestOutcome(
            name, False, False, f"Expected a plain value for '{result_variable}', but got a DataFrame."
        )

    return _compare_plain_values(student.value, reference.value, numeric_tolerance)


def hidden_test_outcome(name: str, execution_status: str, error: PythonError | None) -> TestOutcome:
    if execution_status == "success":
        return TestOutcome(name, True, True, "Passed.")
    message = f"{error.error_type}: {error.message}" if error else "The check did not pass."
    return TestOutcome(name, False, True, message[:500])


def score_attempt(
    *,
    correctness_outcome: TestOutcome,
    hidden_outcomes: list[TestOutcome],
    student_execution_time_ms: int,
    reference_execution_time_ms: int,
) -> AttemptEvaluation:
    correctness_score = CORRECTNESS_WEIGHT if correctness_outcome.passed else 0.0

    if not correctness_outcome.passed:
        edge_case_score = 0.0
        efficiency_score = 0.0
        explanation_score = 0.0
    else:
        edge_case_ratio = (
            sum(1 for o in hidden_outcomes if o.passed) / len(hidden_outcomes) if hidden_outcomes else 1.0
        )
        edge_case_score = EDGE_CASE_WEIGHT * edge_case_ratio

        if (
            reference_execution_time_ms <= 0
            or (
                student_execution_time_ms <= MIN_MEANINGFUL_TIME_MS
                and reference_execution_time_ms <= MIN_MEANINGFUL_TIME_MS
            )
        ):
            efficiency_score = EFFICIENCY_WEIGHT
        else:
            ratio = student_execution_time_ms / max(reference_execution_time_ms, 1)
            if ratio <= 1.5:
                efficiency_score = EFFICIENCY_WEIGHT
            elif ratio <= 3.0:
                efficiency_score = EFFICIENCY_WEIGHT * 0.5
            else:
                efficiency_score = 0.0

        explanation_score = EXPLANATION_WEIGHT

    total = round(correctness_score + edge_case_score + efficiency_score + explanation_score, 1)
    return AttemptEvaluation(
        passed=total >= PASS_THRESHOLD,
        score=total,
        correctness_score=correctness_score,
        edge_case_score=edge_case_score,
        efficiency_score=efficiency_score,
        explanation_score=explanation_score,
    )
