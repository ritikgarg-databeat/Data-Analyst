"""Readiness / weakness / plan orchestration (Phase 9) — the DB-aware layer
around the pure `app/interview_engine/{readiness,weakness,plan}.py` modules.
Pulls its inputs from two REAL, already-existing sources: `UserSkill.mastery_
score` (computed by the existing `MasteryService` off real graded attempts)
and completed `Interview` rows (scored by `app/interview_engine/scoring.py`
at submit time) — never a second parallel scoring system.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.interview_engine.plan import PlanDay, generate_plan
from app.interview_engine.readiness import CompletedInterview, ReadinessResult, compute_readiness
from app.interview_engine.weakness import (
    AttemptSignal,
    CommunicationSignal,
    WeaknessFinding,
    detect_communication_gap,
    detect_weaknesses,
)
from app.models.case import CaseAttempt
from app.models.enums import ExerciseType, InterviewStatus
from app.models.excel_lab import ExcelExerciseTestResult
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview, InterviewPlan, InterviewQuestion, ReadinessSnapshot
from app.models.python_lab import PythonExerciseTestResult
from app.models.sql_lab import SqlExerciseTestResult
from app.models.user_skill import UserSkill
from app.schemas.interview import (
    InterviewPlanSchema,
    PlanDaySchema,
    ReadinessResponse,
    ReadinessSnapshotSchema,
    WeaknessFindingSchema,
)

CONCEPTUAL_TYPES = {ExerciseType.MULTIPLE_CHOICE, ExerciseType.TRUE_FALSE, ExerciseType.SHORT_ANSWER}
EXECUTION_TYPES = {ExerciseType.SQL, ExerciseType.PYTHON, ExerciseType.EXCEL}
RUBRIC_SCORED_TYPES = {ExerciseType.BUSINESS_REASONING, ExerciseType.DATA_INTERPRETATION, ExerciseType.INTERVIEW_RESPONSE}

_HIDDEN_TEST_MODELS = (SqlExerciseTestResult, PythonExerciseTestResult, ExcelExerciseTestResult)


class InterviewReadinessService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Input gathering -----------------------------------------------------

    def _skill_mastery_scores(self, user_id: str) -> list[float]:
        stmt = select(UserSkill).where(UserSkill.user_id == user_id, UserSkill.questions_attempted > 0)
        return [row.mastery_score for row in self.db.execute(stmt).scalars().all()]

    def _completed_interviews(self, user_id: str) -> list[Interview]:
        stmt = (
            select(Interview)
            .where(
                Interview.user_id == user_id,
                Interview.status == InterviewStatus.COMPLETED,
                Interview.completed_at.is_not(None),
            )
            .order_by(Interview.completed_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def _interview_type_breakdown(self, interview: Interview) -> dict[str, float]:
        """Per-`interview_type` average score for one completed interview —
        distinct from `Interview.score["dimensions"]` (the 6 scoring
        dimensions), used here purely for the readiness trend's per-domain
        breakdown and the plan's "lowest scoring domain" fallback. Covers
        both exercise-backed rounds and Case Study rounds (which score via
        `case_attempt_id`, not `exercise_attempt_id`) so a user who does
        mostly case studies still gets a real per-type breakdown instead of
        one that's silently empty for that type."""
        totals: dict[str, list[float]] = {}
        for attempt in interview.question_attempts:
            section = next((s for s in interview.sections if s.id == attempt.section_id), None)
            if section is None:
                continue
            if attempt.exercise_attempt_id:
                exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
                if exercise_attempt and exercise_attempt.score is not None:
                    totals.setdefault(section.interview_type, []).append(exercise_attempt.score)
            elif attempt.case_attempt_id:
                case_attempt = self.db.get(CaseAttempt, attempt.case_attempt_id)
                if case_attempt and case_attempt.score is not None:
                    totals.setdefault(section.interview_type, []).append(case_attempt.score["overall"])
        return {k: round(sum(v) / len(v), 1) for k, v in totals.items()}

    def _to_completed_interview(self, interview: Interview) -> CompletedInterview | None:
        if not interview.score or interview.completed_at is None:
            return None
        return CompletedInterview(
            overall_score=interview.score["overall"],
            completed_at=interview.completed_at,
            interview_type_scores=self._interview_type_breakdown(interview),
        )

    def compute(self, user_id: str) -> tuple[ReadinessResult, list[Interview]]:
        mastery_scores = self._skill_mastery_scores(user_id)
        completed = self._completed_interviews(user_id)
        completed_dcs = [dc for i in completed if (dc := self._to_completed_interview(i)) is not None]
        return compute_readiness(mastery_scores, completed_dcs), completed

    def get_readiness(self, user_id: str) -> ReadinessResponse:
        result, _ = self.compute(user_id)
        ranked = sorted(result.breakdown.items(), key=lambda kv: kv[1], reverse=True)
        strongest = [k for k, _ in ranked[:3]]
        weakest = [k for k, _ in ranked[-3:][::-1]] if ranked else []
        return ReadinessResponse(
            overall_score=result.overall_score,
            mastery_component=result.mastery_component,
            recent_performance_component=result.recent_performance_component,
            consistency_component=result.consistency_component,
            breakdown=result.breakdown,
            strongest=strongest,
            weakest=weakest,
        )

    def snapshot_readiness(self, user_id: str) -> ReadinessSnapshotSchema:
        result, _ = self.compute(user_id)
        snapshot = ReadinessSnapshot(
            user_id=user_id,
            overall_score=result.overall_score,
            breakdown=result.breakdown,
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return ReadinessSnapshotSchema(
            id=snapshot.id,
            computed_at=snapshot.computed_at,
            overall_score=snapshot.overall_score,
            breakdown=snapshot.breakdown,
        )

    def get_history(self, user_id: str) -> list[ReadinessSnapshotSchema]:
        stmt = (
            select(ReadinessSnapshot)
            .where(ReadinessSnapshot.user_id == user_id)
            .order_by(ReadinessSnapshot.computed_at.asc())
        )
        return [
            ReadinessSnapshotSchema(
                id=s.id, computed_at=s.computed_at, overall_score=s.overall_score, breakdown=s.breakdown
            )
            for s in self.db.execute(stmt).scalars().all()
        ]

    # --- Weaknesses ----------------------------------------------------------

    def _hidden_test_counts(self, exercise_attempt_id: str) -> tuple[int, int]:
        passed = 0
        total = 0
        for model in _HIDDEN_TEST_MODELS:
            stmt = select(model).where(model.attempt_id == exercise_attempt_id, model.is_hidden.is_(True))
            for row in self.db.execute(stmt).scalars().all():
                total += 1
                if row.passed:
                    passed += 1
        return passed, total

    def _attempt_signals(self, user_id: str) -> tuple[list[AttemptSignal], list[CommunicationSignal]]:
        interviews = self._completed_interviews(user_id)
        signals: list[AttemptSignal] = []
        comm_signals: list[CommunicationSignal] = []

        for interview in interviews:
            for attempt in interview.question_attempts:
                section = next((s for s in interview.sections if s.id == attempt.section_id), None)
                interview_type = section.interview_type if section else None
                if interview_type is None or not attempt.exercise_attempt_id:
                    continue

                exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
                if exercise_attempt is None or exercise_attempt.score is None:
                    continue

                exercise_type: str | None = None
                if attempt.interview_question_id:
                    question = self.db.get(InterviewQuestion, attempt.interview_question_id)
                    if question is not None:
                        exercise = self.db.get(Exercise, question.exercise_id)
                        exercise_type = exercise.exercise_type if exercise else None

                is_conceptual = exercise_type in CONCEPTUAL_TYPES
                is_execution = exercise_type in EXECUTION_TYPES
                is_rubric_scored = (
                    exercise_type in RUBRIC_SCORED_TYPES or interview_type in ("CASE_STUDY", "BEHAVIORAL")
                )

                hidden_passed, hidden_total = (
                    self._hidden_test_counts(attempt.exercise_attempt_id) if is_execution else (None, None)
                )

                time_limit = None
                if attempt.interview_question_id:
                    question = self.db.get(InterviewQuestion, attempt.interview_question_id)
                    time_limit = question.time_limit_seconds if question else None

                signals.append(
                    AttemptSignal(
                        interview_type=interview_type,
                        is_conceptual=is_conceptual,
                        is_execution=is_execution,
                        is_rubric_scored=is_rubric_scored,
                        score=exercise_attempt.score,
                        hidden_tests_passed=hidden_passed,
                        hidden_tests_total=hidden_total,
                        time_limit_seconds=time_limit,
                        time_spent_seconds=attempt.time_spent_seconds,
                    )
                )

                if interview_type == "BEHAVIORAL":
                    comm_signals.append(
                        CommunicationSignal(
                            interview_type=interview_type,
                            category_scores={"communication": exercise_attempt.score},
                        )
                    )

        return signals, comm_signals

    def get_weaknesses(self, user_id: str) -> list[WeaknessFindingSchema]:
        signals, comm_signals = self._attempt_signals(user_id)
        findings: list[WeaknessFinding] = detect_weaknesses(signals)
        comm_finding = detect_communication_gap(comm_signals)
        if comm_finding is not None:
            findings.append(comm_finding)
        return [
            WeaknessFindingSchema(
                gap_type=f.gap_type,
                interview_type=f.interview_type,
                occurrences=f.occurrences,
                average_score=f.average_score,
                detail=f.detail,
            )
            for f in findings
        ]

    # --- Plan ------------------------------------------------------------------

    def generate_and_persist_plan(self, user_id: str) -> InterviewPlanSchema:
        signals, comm_signals = self._attempt_signals(user_id)
        weaknesses = detect_weaknesses(signals)
        comm_finding = detect_communication_gap(comm_signals)
        if comm_finding is not None:
            weaknesses.append(comm_finding)
        weaknesses.sort(key=lambda f: f.occurrences, reverse=True)

        readiness_result, _ = self.compute(user_id)
        days: list[PlanDay] = generate_plan(weaknesses, readiness_result)

        plan = InterviewPlan(
            user_id=user_id,
            days=[
                {
                    "day_number": d.day_number,
                    "focus_area": d.focus_area,
                    "title": d.title,
                    "task_type": d.task_type,
                    "task_ref": d.task_ref,
                    "description": d.description,
                }
                for d in days
            ],
            readiness_snapshot={
                "overall_score": readiness_result.overall_score,
                "breakdown": readiness_result.breakdown,
                "computed_at": datetime.now(UTC).isoformat(),
            },
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        return self._plan_to_schema(plan)

    def get_latest_plan(self, user_id: str) -> InterviewPlanSchema | None:
        stmt = (
            select(InterviewPlan)
            .where(InterviewPlan.user_id == user_id)
            .order_by(InterviewPlan.generated_at.desc())
        )
        plan = self.db.execute(stmt).scalars().first()
        return self._plan_to_schema(plan) if plan else None

    def _plan_to_schema(self, plan: InterviewPlan) -> InterviewPlanSchema:
        return InterviewPlanSchema(
            id=plan.id,
            generated_at=plan.generated_at,
            days=[PlanDaySchema(**d) for d in plan.days],
        )
