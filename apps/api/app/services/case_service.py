"""Case Study Engine (Phase 8) — the multi-stage ambiguous-business-problem
workspace: DB-aware orchestration on top of the pure `app/case_engine/`
scoring logic. Mirrors this codebase's established service shape (thin
router, real logic here) — see e.g. app/dbt_lab/service.py."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.case_engine.feedback import Feedback, build_feedback
from app.case_engine.grading import ScoreResult, score_rubric
from app.core.errors import AppError, NotFoundError
from app.models.case import Case, CaseAttempt
from app.models.enums import CaseAttemptStatus, CaseCategory
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt, ExerciseAttemptStatus
from app.models.finding import Finding
from app.schemas.case import CaseSchema, RubricCategorySchema


def to_case_schema(case: Case) -> CaseSchema:
    """Converts a Case ORM row to its public schema — never includes
    `clarification_guidance`/`hints` (only a count)/`reference_solution`."""
    return CaseSchema(
        id=case.id,
        slug=case.slug,
        title=case.title,
        category=case.category,
        difficulty=case.difficulty,
        estimated_minutes=case.estimated_minutes,
        company_context=case.company_context,
        stakeholder_name=case.stakeholder_name,
        stakeholder_role=case.stakeholder_role,
        problem_statement=case.problem_statement,
        business_context=case.business_context,
        objective=case.objective,
        initial_information=case.initial_information,
        constraints=case.constraints,
        available_datasets=case.available_datasets,
        expected_deliverables=case.expected_deliverables,
        learning_objectives=case.learning_objectives,
        stages=case.stages,
        tags=case.tags,
        skills=case.skills,
        rubric=[RubricCategorySchema(**r) for r in case.rubric],
        hint_count=len(case.hints),
        version=case.version,
    )


class CaseService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # --- Case catalog ------------------------------------------------------

    def list_cases(
        self,
        user_id: str,
        *,
        category: CaseCategory | None = None,
        difficulty: str | None = None,
        search: str | None = None,
    ) -> list[tuple[Case, CaseAttempt | None]]:
        stmt = select(Case).where(Case.is_active.is_(True))
        if category:
            stmt = stmt.where(Case.category == category)
        if difficulty:
            stmt = stmt.where(Case.difficulty == difficulty)
        cases = list(self.db.execute(stmt.order_by(Case.title)).scalars().all())

        if search:
            needle = search.strip().lower()
            cases = [
                c
                for c in cases
                if needle in c.title.lower()
                or needle in (c.business_context or "").lower()
                or any(needle in tag.lower() for tag in c.tags)
            ]

        results: list[tuple[Case, CaseAttempt | None]] = []
        for case in cases:
            latest = self._latest_attempt(user_id, case.id)
            results.append((case, latest))
        return results

    def _latest_attempt(self, user_id: str, case_id: str) -> CaseAttempt | None:
        stmt = (
            select(CaseAttempt)
            .where(CaseAttempt.user_id == user_id, CaseAttempt.case_id == case_id)
            .order_by(CaseAttempt.attempt_number.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def list_cases_admin(self) -> list[Case]:
        """All cases, active and inactive — for the Content Admin panel
        (spec section 61). Cases are content-authored, so admin only
        lists/activates/deactivates (see UpdateCaseAdminRequest)."""
        return list(self.db.execute(select(Case).order_by(Case.title)).scalars().all())

    def update_case_admin(self, case_id: str, is_active: bool) -> Case:
        case = self.db.get(Case, case_id)
        if case is None:
            raise NotFoundError(f"Case '{case_id}' not found.")
        case.is_active = is_active
        self.db.commit()
        self.db.refresh(case)
        return case

    def get_case_by_slug(self, slug: str) -> Case:
        case = self.db.execute(select(Case).where(Case.slug == slug)).scalar_one_or_none()
        if case is None or not case.is_active:
            raise NotFoundError(f"Case '{slug}' not found.")
        return case

    # --- Attempt lifecycle ---------------------------------------------------

    def start_attempt(self, user_id: str, case_slug: str) -> CaseAttempt:
        case = self.get_case_by_slug(case_slug)
        existing = self._latest_attempt(user_id, case.id)
        if existing is not None and existing.status != CaseAttemptStatus.COMPLETED:
            return existing  # resume the in-progress attempt rather than starting a second one

        attempt = CaseAttempt(
            user_id=user_id,
            case_id=case.id,
            case_version_snapshot=case.version,
            attempt_number=(existing.attempt_number + 1) if existing else 1,
            status=CaseAttemptStatus.IN_PROGRESS,
            current_stage=case.stages[0] if case.stages else None,
            started_at=datetime.now(UTC),
            last_activity_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def get_attempt(self, user_id: str, attempt_id: str) -> CaseAttempt:
        stmt = (
            select(CaseAttempt)
            .where(CaseAttempt.id == attempt_id)
            .options(selectinload(CaseAttempt.case))
        )
        attempt = self.db.execute(stmt).scalar_one_or_none()
        if attempt is None or attempt.user_id != user_id:
            raise NotFoundError(f"Case attempt '{attempt_id}' not found.")
        return attempt

    def list_attempts(self, user_id: str) -> list[CaseAttempt]:
        stmt = (
            select(CaseAttempt)
            .where(CaseAttempt.user_id == user_id)
            .options(selectinload(CaseAttempt.case))
            .order_by(CaseAttempt.last_activity_at.desc())
        )
        return list(self.db.execute(stmt).scalars().all())

    def _touch(self, attempt: CaseAttempt) -> None:
        attempt.last_activity_at = datetime.now(UTC)

    def update_stage(self, user_id: str, attempt_id: str, stage: str) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.current_stage = stage  # type: ignore[assignment]
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_clarification(self, user_id: str, attempt_id: str, questions: str) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.clarification_questions = questions
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_framing(self, user_id: str, attempt_id: str, framing: dict) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.problem_framing = framing
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_dataset_selection(self, user_id: str, attempt_id: str, dataset_slugs: list[str]) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.selected_dataset_slugs = dataset_slugs
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_recommendation(self, user_id: str, attempt_id: str, recommendation: dict) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.recommendation = recommendation
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_executive_summary(self, user_id: str, attempt_id: str, summary: dict) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.executive_summary = summary
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def record_stage_time(self, user_id: str, attempt_id: str, stage: str, seconds: float) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        times = dict(attempt.time_per_stage_seconds or {})
        times[stage] = times.get(stage, 0) + seconds
        attempt.time_per_stage_seconds = times
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def reveal_hint(self, user_id: str, attempt_id: str) -> tuple[CaseAttempt, str]:
        attempt = self.get_attempt(user_id, attempt_id)
        case = attempt.case
        if attempt.hints_used >= len(case.hints):
            raise AppError("No more hints available for this case.")
        hint = case.hints[attempt.hints_used]
        attempt.hints_used += 1
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt, hint

    # --- Submission & grading ---------------------------------------------

    def _technical_pct(self, user_id: str, case: Case) -> float | None:
        if not case.required_exercise_slugs:
            return None
        stmt = (
            select(Exercise.slug, ExerciseAttempt.status)
            .join(ExerciseAttempt, ExerciseAttempt.exercise_id == Exercise.id)
            .where(Exercise.slug.in_(case.required_exercise_slugs), ExerciseAttempt.user_id == user_id)
        )
        passed_slugs = {
            slug for slug, status in self.db.execute(stmt).all() if status == ExerciseAttemptStatus.PASSED
        }
        return round(100 * len(passed_slugs) / len(case.required_exercise_slugs), 1)

    def submission_readiness(self, attempt: CaseAttempt) -> dict[str, bool]:
        """The submission checklist (spec section 53) — computed on read, not stored."""
        has_findings = (
            self.db.execute(select(Finding.id).where(Finding.case_attempt_id == attempt.id).limit(1)).first()
            is not None
        )
        return {
            "problem_framed": bool(attempt.problem_framing),
            "data_understood": bool(attempt.selected_dataset_slugs),
            "findings_documented": has_findings,
            "recommendation_written": bool(attempt.recommendation),
            "executive_summary_written": bool(attempt.executive_summary),
        }

    def submit_attempt(
        self, user_id: str, attempt_id: str, rubric_selections: dict[str, list[str]]
    ) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        if attempt.status == CaseAttemptStatus.COMPLETED:
            raise AppError("This case attempt has already been completed.")

        case = attempt.case
        now = datetime.now(UTC)
        attempt.status = CaseAttemptStatus.SUBMITTED
        attempt.submitted_at = now
        attempt.rubric_selections = rubric_selections

        technical_pct = self._technical_pct(user_id, case)
        score_result: ScoreResult = score_rubric(case.rubric, rubric_selections, technical_pct=technical_pct)
        feedback: Feedback = build_feedback(score_result)

        attempt.score = {
            "overall": score_result.overall,
            "categories": [
                {
                    "category": c.category,
                    "weight": c.weight,
                    "earned_points": c.earned_points,
                    "total_points": c.total_points,
                    "pct": c.pct,
                    "is_technical": c.is_technical,
                }
                for c in score_result.categories
            ],
        }
        attempt.feedback = {
            "what_went_well": feedback.what_went_well,
            "what_missed": feedback.what_missed,
            "technical_issues": feedback.technical_issues,
            "business_reasoning_issues": feedback.business_reasoning_issues,
            "communication_issues": feedback.communication_issues,
        }
        # Grading is fully deterministic and instant in this phase (no AI
        # reviewer yet — see spec section 54) — SUBMITTED and COMPLETED
        # happen together rather than waiting in UNDER_REVIEW.
        attempt.status = CaseAttemptStatus.COMPLETED
        attempt.completed_at = now
        self._touch(attempt)
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def reveal_solution(self, user_id: str, attempt_id: str) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        if attempt.status != CaseAttemptStatus.COMPLETED:
            raise AppError("Complete and submit this case before revealing the reference solution.")
        attempt.solution_revealed = True
        self.db.commit()
        self.db.refresh(attempt)
        return attempt

    def save_reflection(self, user_id: str, attempt_id: str, reflection: dict) -> CaseAttempt:
        attempt = self.get_attempt(user_id, attempt_id)
        attempt.reflection = reflection
        self.db.commit()
        self.db.refresh(attempt)
        return attempt
