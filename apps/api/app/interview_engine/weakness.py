"""Interview weakness detection (spec section 40) — pure, DB-free,
deterministic classification into 5 gap types from real attempt history.
No AI/LLM anywhere — every rule below is a plain threshold over real,
already-computed signals (scores, hidden-test pass/fail, time spent).

- **Knowledge gap** — repeated failures (score < FAIL_THRESHOLD) on
  conceptual questions (MULTIPLE_CHOICE/TRUE_FALSE/SHORT_ANSWER-backed) for
  the same `interview_type`, at least MIN_OCCURRENCES times: doesn't know
  the concept, not just executing it poorly.
- **Execution gap** — a SQL/Python/Excel question where the *hidden* tests
  failed but the main correctness check passed (or the overall score is
  high but not perfect) repeatedly: understands the approach, keeps
  tripping on real edge cases.
- **Reasoning gap** — a rubric-scored BUSINESS_REASONING/DATA_INTERPRETATION/
  CASE_STUDY question scoring low on its "framing"/"reasoning"-flavored
  categories repeatedly: can't structure an ambiguous problem.
- **Communication gap** — a BEHAVIORAL or rubric-scored question where the
  technical/reasoning categories score fine but a "communication"-flavored
  category scores low: knows the material, explains it poorly.
- **Speed gap** — repeatedly finishing correct answers well past the time
  limit: gets there, just too slowly for a real interview.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

FAIL_THRESHOLD = 60.0
MIN_OCCURRENCES = 2
SPEED_OVERRUN_RATIO = 1.3  # 30% over the time limit counts as a speed miss


@dataclass
class AttemptSignal:
    interview_type: str
    is_conceptual: bool  # MULTIPLE_CHOICE / TRUE_FALSE / SHORT_ANSWER backed
    is_execution: bool  # SQL / PYTHON / EXCEL backed (real hidden-test grading)
    is_rubric_scored: bool  # BUSINESS_REASONING / DATA_INTERPRETATION / CASE_STUDY / BEHAVIORAL
    score: float
    hidden_tests_passed: int | None = None
    hidden_tests_total: int | None = None
    time_limit_seconds: int | None = None
    time_spent_seconds: int | None = None


@dataclass
class WeaknessFinding:
    gap_type: str  # "Knowledge" | "Execution" | "Reasoning" | "Communication" | "Speed"
    interview_type: str
    occurrences: int
    average_score: float
    detail: str


def detect_weaknesses(signals: list[AttemptSignal]) -> list[WeaknessFinding]:
    findings: list[WeaknessFinding] = []
    by_type: dict[str, list[AttemptSignal]] = defaultdict(list)
    for signal in signals:
        by_type[signal.interview_type].append(signal)

    for interview_type, group in by_type.items():
        # Knowledge gap: conceptual questions failed repeatedly.
        conceptual_fails = [s for s in group if s.is_conceptual and s.score < FAIL_THRESHOLD]
        if len(conceptual_fails) >= MIN_OCCURRENCES:
            findings.append(
                WeaknessFinding(
                    gap_type="Knowledge",
                    interview_type=interview_type,
                    occurrences=len(conceptual_fails),
                    average_score=round(sum(s.score for s in conceptual_fails) / len(conceptual_fails), 1),
                    detail=f"{len(conceptual_fails)} conceptual {interview_type} questions answered incorrectly.",
                )
            )

        # Execution gap: real execution questions that pass the main check
        # but repeatedly miss hidden edge cases.
        execution_edge_misses = [
            s
            for s in group
            if s.is_execution
            and s.hidden_tests_total
            and s.hidden_tests_passed is not None
            and s.hidden_tests_passed < s.hidden_tests_total
            and s.score >= FAIL_THRESHOLD
        ]
        if len(execution_edge_misses) >= MIN_OCCURRENCES:
            findings.append(
                WeaknessFinding(
                    gap_type="Execution",
                    interview_type=interview_type,
                    occurrences=len(execution_edge_misses),
                    average_score=round(
                        sum(s.score for s in execution_edge_misses) / len(execution_edge_misses), 1
                    ),
                    detail=(
                        f"Core logic is right, but {len(execution_edge_misses)} {interview_type} "
                        "submissions missed hidden edge cases."
                    ),
                )
            )

        # Reasoning gap: rubric-scored (case/business-reasoning) questions
        # scoring low overall, repeatedly.
        reasoning_fails = [s for s in group if s.is_rubric_scored and not s.is_conceptual and s.score < FAIL_THRESHOLD]
        if len(reasoning_fails) >= MIN_OCCURRENCES:
            findings.append(
                WeaknessFinding(
                    gap_type="Reasoning",
                    interview_type=interview_type,
                    occurrences=len(reasoning_fails),
                    average_score=round(sum(s.score for s in reasoning_fails) / len(reasoning_fails), 1),
                    detail=f"{len(reasoning_fails)} ambiguous {interview_type} problems scored low overall.",
                )
            )

        # Speed gap: correct answers, consistently over time.
        slow_but_correct = [
            s
            for s in group
            if s.score >= FAIL_THRESHOLD
            and s.time_limit_seconds
            and s.time_spent_seconds is not None
            and s.time_spent_seconds > s.time_limit_seconds * SPEED_OVERRUN_RATIO
        ]
        if len(slow_but_correct) >= MIN_OCCURRENCES:
            findings.append(
                WeaknessFinding(
                    gap_type="Speed",
                    interview_type=interview_type,
                    occurrences=len(slow_but_correct),
                    average_score=round(sum(s.score for s in slow_but_correct) / len(slow_but_correct), 1),
                    detail=f"{len(slow_but_correct)} correct {interview_type} answers ran well past the time limit.",
                )
            )

    findings.sort(key=lambda f: f.occurrences, reverse=True)
    return findings


@dataclass
class CommunicationSignal:
    """A rubric-scored question's per-category breakdown, when available
    (Case attempts already carry this; a BEHAVIORAL exercise's flat rubric
    is treated as 100% communication-flavored)."""

    interview_type: str
    category_scores: dict[str, float] = field(default_factory=dict)


_COMMUNICATION_HINTS = ("communication", "presentation", "explain")


def detect_communication_gap(signals: list[CommunicationSignal]) -> WeaknessFinding | None:
    comm_scores = []
    for signal in signals:
        for category, score in signal.category_scores.items():
            if any(hint in category.lower() for hint in _COMMUNICATION_HINTS):
                comm_scores.append(score)
    if len(comm_scores) < MIN_OCCURRENCES:
        return None
    average = sum(comm_scores) / len(comm_scores)
    if average >= FAIL_THRESHOLD:
        return None
    return WeaknessFinding(
        gap_type="Communication",
        interview_type="BEHAVIORAL",
        occurrences=len(comm_scores),
        average_score=round(average, 1),
        detail=f"Communication-flavored rubric criteria averaged {round(average, 1)}% across {len(comm_scores)} answers.",
    )
