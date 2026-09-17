"""Auto-grading for content-file-gradable exercise types.

Only MULTIPLE_CHOICE / TRUE_FALSE / SHORT_ANSWER can be graded purely from
content-file data (see app.content.schema.AUTO_GRADABLE_EXERCISE_TYPES).
CODE/SQL/PYTHON have dedicated execution engines elsewhere (app.sql.*,
app.python_lab.*) and never reach this module. Exercises with a `rubric`
(Phase 6, spec section 46 "Case Evaluation" — typically BUSINESS_REASONING/
DATA_INTERPRETATION case studies) are scored deterministically from which
rubric criteria the learner self-assessed their own free-text answer as
satisfying — a real, non-self-reported score, without requiring exact
wording or an AI grader (still out of scope until Phase 11). Everything
else with neither an execution engine nor a rubric falls back to
self-reported score, recorded as SUBMITTED.
"""

from dataclasses import dataclass

from app.content.schema import AUTO_GRADABLE_EXERCISE_TYPES, ExerciseContentFile

# A rubric-scored attempt "passes" (counts toward lesson progress / mastery
# as a pass rather than a fail) once it clears this share of total points —
# the same 70% bar used nowhere else numerically in this codebase but chosen
# to match this app's general "clearly more right than wrong" passing bar.
RUBRIC_PASS_THRESHOLD = 70.0


@dataclass
class GradeResult:
    is_auto_graded: bool
    is_correct: bool | None
    score: float | None  # 0-100


def is_auto_gradable(exercise_type: str) -> bool:
    return exercise_type in AUTO_GRADABLE_EXERCISE_TYPES


def grade(
    content: ExerciseContentFile, submitted_answer: str, rubric_selections: list[str] | None = None
) -> GradeResult:
    if content.rubric:
        if rubric_selections is None:
            return GradeResult(is_auto_graded=False, is_correct=None, score=None)
        total_points = sum(c.points for c in content.rubric)
        earned_points = sum(c.points for c in content.rubric if c.criterion in rubric_selections)
        score = (earned_points / total_points * 100) if total_points else 0.0
        return GradeResult(is_auto_graded=True, is_correct=score >= RUBRIC_PASS_THRESHOLD, score=score)

    if not is_auto_gradable(content.exercise_type):
        return GradeResult(is_auto_graded=False, is_correct=None, score=None)

    correct = (content.correct_answer or "").strip().casefold()
    submitted = (submitted_answer or "").strip().casefold()

    if content.exercise_type in ("MULTIPLE_CHOICE", "TRUE_FALSE"):
        is_correct = submitted == correct
    else:  # SHORT_ANSWER — lenient contains-match, since exact string match is too brittle
        is_correct = bool(correct) and correct in submitted

    return GradeResult(is_auto_graded=True, is_correct=is_correct, score=100.0 if is_correct else 0.0)
