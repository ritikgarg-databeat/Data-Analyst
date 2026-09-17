"""Generic, per-lesson-configurable completion rules.

`Lesson.completion_criteria` (JSON: {"type": ..., "threshold": ...}) selects
which rule applies. New lesson types can define new rule types here without
touching callers — `evaluate_completion` is the single dispatch point.
"""

from dataclasses import dataclass

from app.models.enums import CompletionRuleType
from app.models.lesson import Lesson
from app.models.lesson_progress import LessonProgress

DEFAULT_CRITERIA: dict[str, object] = {"type": CompletionRuleType.READING_PERCENT.value, "threshold": 90.0}


@dataclass
class CompletionContext:
    """Everything a completion rule might need, gathered once by the caller."""

    lesson: Lesson
    progress: LessonProgress
    best_exercise_score_percent: float | None  # best score across this lesson's exercises, 0-100
    best_assessment_score_percent: float | None  # best score on the lesson's module assessment, 0-100


def get_criteria(lesson: Lesson) -> dict[str, object]:
    return lesson.completion_criteria or DEFAULT_CRITERIA


def evaluate_completion(ctx: CompletionContext) -> bool:
    criteria = get_criteria(ctx.lesson)
    rule_type = criteria.get("type", CompletionRuleType.READING_PERCENT.value)
    threshold = float(criteria.get("threshold", 90.0))  # type: ignore[arg-type]

    if rule_type == CompletionRuleType.READING_PERCENT.value:
        return ctx.progress.progress_percent >= threshold

    if rule_type == CompletionRuleType.EXERCISE_SCORE.value:
        reading_done = ctx.progress.progress_percent >= 90.0
        exercise_ok = (ctx.best_exercise_score_percent or 0.0) >= threshold
        return reading_done and exercise_ok

    if rule_type == CompletionRuleType.ASSESSMENT_SCORE.value:
        return (ctx.best_assessment_score_percent or 0.0) >= threshold

    return ctx.progress.progress_percent >= 90.0
