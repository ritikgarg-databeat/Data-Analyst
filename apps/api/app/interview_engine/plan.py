"""Personalized interview plan generation (spec section 41) — deterministic,
built from the real weakness/readiness outputs above, not a hardcoded
template. Days 1-5 target the most significant detected weaknesses (or, if
none have been detected yet — e.g. a brand-new user — the lowest-scoring
domains from the readiness breakdown instead, so a first-time plan is still
personalized rather than generic); Day 6 is always a full mock interview;
Day 7 is always a weakness review, matching spec section 41's example shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.interview_engine.readiness import ReadinessResult
from app.interview_engine.weakness import WeaknessFinding

PLAN_LENGTH_DAYS = 7
FOCUS_DAYS = 5


@dataclass
class PlanDay:
    day_number: int
    focus_area: str
    title: str
    task_type: str  # "PRACTICE" | "MOCK_INTERVIEW" | "REVIEW"
    task_ref: str | None
    description: str


def _title_for(interview_type: str) -> str:
    return interview_type.replace("_", " ").title()


def generate_plan(weaknesses: list[WeaknessFinding], readiness: ReadinessResult) -> list[PlanDay]:
    days: list[PlanDay] = []

    focus_items: list[tuple[str, str]] = [(w.interview_type, w.detail) for w in weaknesses[:FOCUS_DAYS]]

    if len(focus_items) < FOCUS_DAYS:
        # Fill remaining days from the readiness breakdown's lowest-scoring
        # domains not already covered by a detected weakness.
        covered = {t for t, _ in focus_items}
        weakest_domains = sorted(readiness.breakdown.items(), key=lambda kv: kv[1])
        for domain, score in weakest_domains:
            if len(focus_items) >= FOCUS_DAYS:
                break
            if domain in covered:
                continue
            focus_items.append((domain, f"{_title_for(domain)} is currently your lowest-scoring area ({score:.0f}%)."))
            covered.add(domain)

    for i, (interview_type, detail) in enumerate(focus_items, start=1):
        days.append(
            PlanDay(
                day_number=i,
                focus_area=interview_type,
                title=f"{_title_for(interview_type)} Practice",
                task_type="PRACTICE",
                task_ref=interview_type,
                description=detail,
            )
        )

    while len(days) < FOCUS_DAYS:
        days.append(
            PlanDay(
                day_number=len(days) + 1,
                focus_area="General",
                title="General Practice",
                task_type="PRACTICE",
                task_ref=None,
                description="No specific weakness detected yet — keep practicing broadly across all rounds.",
            )
        )

    days.append(
        PlanDay(
            day_number=FOCUS_DAYS + 1,
            focus_area="Mock Interview",
            title="Full Mock Interview",
            task_type="MOCK_INTERVIEW",
            task_ref=None,
            description="A full timed mock interview spanning multiple rounds, to simulate the real thing.",
        )
    )
    days.append(
        PlanDay(
            day_number=FOCUS_DAYS + 2,
            focus_area="Weakness Review",
            title="Weakness Review",
            task_type="REVIEW",
            task_ref=None,
            description="Review missed questions from the week and retry the weakest section.",
        )
    )
    return days
