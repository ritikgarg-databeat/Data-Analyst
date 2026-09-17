"""Result-based Excel exercise evaluation — mirrors app/sql/evaluation.py's
philosophy exactly: never compare formula *text* (two different formulas can
correctly compute the same answer). The student's submitted workbook is
evaluated for real by the same `formula_engine` that also evaluates the
authored solution workbook, then the two are compared cell-by-cell at the
exercise-authored `check_cells` only — a student is free to build whatever
helper columns/formulas they like en route to those cells.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.excel_lab.formula_engine import Workbook, evaluate_workbook, get_evaluated_cell

PASS_THRESHOLD = 70.0


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
    test_outcomes: list[TestOutcome] = field(default_factory=list)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _cells_equal(actual: object, expected: object, tolerance: float) -> bool:
    if actual is None or expected is None:
        return actual is None and expected is None
    if _is_number(actual) and _is_number(expected):
        return abs(float(actual) - float(expected)) <= tolerance
    if isinstance(actual, str) and isinstance(expected, str):
        return actual.strip() == expected.strip()
    return actual == expected


def _split_ref(ref: str, default_sheet: str) -> tuple[str, str]:
    if "!" in ref:
        sheet, cell = ref.split("!", 1)
        return sheet, cell
    return default_sheet, ref


def grade_excel_submission(
    student_sheets: Workbook,
    solution_sheets: Workbook,
    check_cells: list[str],
    *,
    numeric_tolerance: float = 0.01,
) -> EvaluationResult:
    """`check_cells` entries are `"Sheet!A1"`, or a bare `"A1"` (resolved
    against the first sheet in `solution_sheets`) for single-sheet exercises."""
    student_evaluated = evaluate_workbook(student_sheets)
    solution_evaluated = evaluate_workbook(solution_sheets)
    default_sheet = next(iter(solution_sheets), "Sheet1")

    outcomes: list[TestOutcome] = []
    for ref in check_cells:
        sheet, cell = _split_ref(ref, default_sheet)
        expected = get_evaluated_cell(solution_evaluated, sheet, cell)
        actual = get_evaluated_cell(student_evaluated, sheet, cell)
        ok = _cells_equal(actual, expected, numeric_tolerance)
        outcomes.append(
            TestOutcome(
                name=ref,
                passed=ok,
                is_hidden=False,
                message="Correct." if ok else f"Expected {expected!r} at {ref}, got {actual!r}.",
            )
        )

    if not outcomes:
        return EvaluationResult(score=0.0, passed=False, test_outcomes=[])

    passed_count = sum(1 for o in outcomes if o.passed)
    score = round(100 * passed_count / len(outcomes), 1)
    return EvaluationResult(score=score, passed=score >= PASS_THRESHOLD, test_outcomes=outcomes)
