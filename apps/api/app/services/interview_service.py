"""Interview Engine (Phase 9) — the live session/attempt lifecycle: DB-aware
orchestration on top of the pure `app/interview_engine/` scoring/selection
logic and the EXISTING Phase 2-4/8 grading services (Exercise/SQL/Python/
Excel/Case). This module never re-implements grading — every answer is
graded by calling straight into the service that already grades that
exercise_type for the platform's regular practice flow; this module only
adds interview-specific bookkeeping (sections, timing, follow-ups, section/
interview advancement) around those real results.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.content.loader import load_exercise_file
from app.content.schema import ExerciseContentFile
from app.core.errors import AppError, NotFoundError
from app.interview_engine.scoring import ScoredQuestion, score_interview
from app.interview_engine.selection import HistoryEntry, QuestionCandidate, select_next_question
from app.models.case import Case, CaseAttempt
from app.models.enums import CaseAttemptStatus, ExerciseAttemptStatus, InterviewMode, InterviewStatus
from app.models.excel_lab import ExcelExerciseTestResult
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import (
    Interview,
    InterviewQuestion,
    InterviewQuestionAttempt,
    InterviewSection,
    InterviewTemplate,
)
from app.models.lesson import Lesson
from app.models.python_lab import PythonExerciseTestResult
from app.models.skill import Skill
from app.models.sql_lab import SqlExerciseTestResult
from app.schemas.excel import ExcelSheetSchema
from app.schemas.exercise import RubricCriterionSchema, SubmitExerciseAttemptRequest
from app.schemas.interview import (
    AnswerInterviewQuestionRequest,
    CreateInterviewRequest,
    InterviewDimensionScoreSchema,
    InterviewQuestionAttemptSchema,
    InterviewQuestionDetail,
    InterviewQuestionReviewSchema,
    InterviewReviewResponse,
    InterviewSchema,
    InterviewScoreSchema,
    InterviewSectionSchema,
    InterviewSectionSpecSchema,
    InterviewTemplateAdminListItemSchema,
    InterviewTemplateSchema,
    InterviewTestOutcomeSchema,
    RetryInterviewRequest,
)
from app.services.case_service import CaseService
from app.services.dbt_exercise_service import DbtExerciseService
from app.services.excel_exercise_service import ExcelExerciseService
from app.services.exercise_service import ExerciseService
from app.services.interview_readiness_service import InterviewReadinessService
from app.services.python_exercise_service import PythonExerciseService
from app.services.sql_exercise_service import SqlExerciseService


def to_template_schema(template: InterviewTemplate) -> InterviewTemplateSchema:
    return InterviewTemplateSchema(
        id=template.id,
        slug=template.slug,
        title=template.title,
        target_profile=template.target_profile,
        description=template.description,
        sections=[InterviewSectionSpecSchema(**s) for s in template.sections],
        rubric_weights=template.rubric_weights,
        tags=template.tags,
        version=template.version,
    )


class InterviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.exercise_service = ExerciseService(db)
        self.sql_service = SqlExerciseService(db)
        self.python_service = PythonExerciseService(db)
        self.excel_service = ExcelExerciseService(db)
        self.case_service = CaseService(db)
        self.dbt_service = DbtExerciseService(db)
        self.readiness_service = InterviewReadinessService(db)

    # --- Templates -----------------------------------------------------------

    def list_templates(self) -> list[InterviewTemplateSchema]:
        stmt = select(InterviewTemplate).where(InterviewTemplate.is_active.is_(True)).order_by(InterviewTemplate.title)
        return [to_template_schema(t) for t in self.db.execute(stmt).scalars().all()]

    def _get_template_by_slug(self, slug: str) -> InterviewTemplate:
        template = self.db.execute(
            select(InterviewTemplate).where(InterviewTemplate.slug == slug)
        ).scalar_one_or_none()
        if template is None or not template.is_active:
            raise NotFoundError(f"Interview template '{slug}' not found.")
        return template

    def get_template(self, slug: str) -> InterviewTemplateSchema:
        return to_template_schema(self._get_template_by_slug(slug))

    # --- Content Admin (spec section 61) --------------------------------------------

    def list_templates_admin(self) -> list[InterviewTemplateAdminListItemSchema]:
        stmt = select(InterviewTemplate).order_by(InterviewTemplate.title)
        return [
            InterviewTemplateAdminListItemSchema(
                id=t.id,
                slug=t.slug,
                title=t.title,
                target_profile=t.target_profile,
                section_count=len(t.sections),
                is_active=t.is_active,
                version=t.version,
            )
            for t in self.db.execute(stmt).scalars().all()
        ]

    def update_template_admin(self, template_id: str, is_active: bool) -> InterviewTemplateAdminListItemSchema:
        template = self.db.get(InterviewTemplate, template_id)
        if template is None:
            raise NotFoundError(f"Interview template '{template_id}' not found.")
        template.is_active = is_active
        self.db.commit()
        self.db.refresh(template)
        return InterviewTemplateAdminListItemSchema(
            id=template.id,
            slug=template.slug,
            title=template.title,
            target_profile=template.target_profile,
            section_count=len(template.sections),
            is_active=template.is_active,
            version=template.version,
        )

    # --- Question detail helper ------------------------------------------------

    def _question_detail(self, question: InterviewQuestion, user_id: str) -> InterviewQuestionDetail:
        exercise: Exercise = question.exercise
        content: ExerciseContentFile = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]

        attempts = list(
            self.db.execute(
                select(ExerciseAttempt).where(
                    ExerciseAttempt.user_id == user_id, ExerciseAttempt.exercise_id == exercise.id
                )
            )
            .scalars()
            .all()
        )
        best_score = max((a.score for a in attempts if a.score is not None), default=None)

        return InterviewQuestionDetail(
            id=question.id,
            slug=question.slug,
            interview_type=question.interview_type,
            difficulty=exercise.difficulty,
            title=exercise.title,
            points=exercise.points,
            time_limit_seconds=question.time_limit_seconds,
            company_archetypes=question.company_archetypes,
            best_score=best_score,
            attempt_count=len(attempts),
            exercise_slug=exercise.slug,
            exercise_type=exercise.exercise_type,
            prompt=content.prompt,
            business_context=content.business_context,
            stakeholder=content.stakeholder,
            constraints=content.constraints,
            expected_deliverables=content.expected_deliverables,
            rubric=[RubricCriterionSchema(criterion=c.criterion, points=c.points) for c in content.rubric],
            choices=content.choices,
            hint_count=len(content.hints),
            follow_up_question_ids=question.follow_up_question_ids,
            dataset=content.dataset,
            sql_starter_query=content.sql_starter_query,
            python_starter_code=content.python_starter_code,
            excel_starter_sheets=[ExcelSheetSchema(name=s.name, cells=s.cells) for s in content.excel_starter_sheets],
            excel_check_cells=content.excel_check_cells,
        )

    def get_question_by_slug(self, slug: str, user_id: str) -> InterviewQuestionDetail:
        question = self.db.execute(
            select(InterviewQuestion).where(InterviewQuestion.slug == slug)
        ).scalar_one_or_none()
        if question is None or not question.is_active:
            raise NotFoundError(f"Interview question '{slug}' not found.")
        return self._question_detail(question, user_id)

    # --- Interview lifecycle ---------------------------------------------------

    def _get_interview(self, user_id: str, interview_id: str) -> Interview:
        stmt = (
            select(Interview)
            .where(Interview.id == interview_id)
            .options(selectinload(Interview.sections), selectinload(Interview.question_attempts))
        )
        interview = self.db.execute(stmt).scalar_one_or_none()
        if interview is None or interview.user_id != user_id:
            raise NotFoundError(f"Interview '{interview_id}' not found.")
        return interview

    def list_interviews(self, user_id: str) -> list[Interview]:
        stmt = select(Interview).where(Interview.user_id == user_id).order_by(Interview.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_interview(self, user_id: str, interview_id: str) -> Interview:
        """Also re-checks/advances state (spec section 33) — this is the only
        signal the interview gets that a Case Study round finished, since
        that happens entirely inside the separate Case Workspace/CaseService
        flow: the frontend returns here afterward and this GET is what
        notices the CaseAttempt is now COMPLETED and moves the interview
        on (or finishes it). It's also where a timed-out interview gets its
        automatic submission (spec section 34) if nothing else already
        triggered it — a learner who just lets the clock run out and never
        clicks anything still has their interview finalized the next time
        anything asks for its state."""
        interview = self._get_interview(user_id, interview_id)
        if interview.status == InterviewStatus.IN_PROGRESS:
            if self._is_over_time_limit(interview):
                return self.submit_interview(user_id, interview_id)
            self._ensure_current_question(interview)
            self.db.commit()
            self.db.refresh(interview)
        return interview

    def _weakest_interview_type(self, user_id: str) -> str | None:
        """What a WEAKNESS_DRILL should drill when the caller doesn't say
        (spec section 5's "auto-targets weak skills"). Prefers a real detected
        weakness; falls back to the readiness breakdown's lowest-scoring
        domain; falls back again to whichever question type the bank actually
        has, so a brand-new user with no history still gets a real drill
        rather than an error."""
        weaknesses = self.readiness_service.get_weaknesses(user_id)
        if weaknesses:
            return weaknesses[0].interview_type

        readiness = self.readiness_service.get_readiness(user_id)
        if readiness.breakdown:
            return min(readiness.breakdown.items(), key=lambda kv: kv[1])[0]

        available = self.db.execute(
            select(InterviewQuestion.interview_type)
            .where(InterviewQuestion.is_active.is_(True))
            .order_by(InterviewQuestion.interview_type)
        ).scalars().first()
        return available.value if hasattr(available, "value") else available

    def create_interview(self, user_id: str, payload: CreateInterviewRequest) -> Interview:
        if payload.question_id:
            question = self.db.get(InterviewQuestion, payload.question_id)
            if question is None:
                raise NotFoundError(f"Interview question '{payload.question_id}' was not found.")
            return self._start_pinned_to_question(user_id, question)
        if payload.template_slug:
            template = self._get_template_by_slug(payload.template_slug)
            interview = Interview(
                user_id=user_id,
                template_id=template.id,
                mode=payload.mode,
                title=template.title,
                total_time_limit_seconds=sum(s["duration_minutes"] for s in template.sections) * 60,
            )
            self.db.add(interview)
            self.db.flush()
            for i, section_spec in enumerate(template.sections):
                self.db.add(
                    InterviewSection(
                        interview_id=interview.id,
                        interview_type=section_spec["interview_type"],
                        title=section_spec["title"],
                        time_limit_seconds=section_spec["duration_minutes"] * 60,
                        target_question_count=section_spec["question_count"],
                        display_order=i,
                    )
                )
        else:
            interview_type = payload.interview_type
            if interview_type is None and payload.mode == InterviewMode.WEAKNESS_DRILL:
                interview_type = self._weakest_interview_type(user_id)
            if not interview_type:
                raise AppError("Either template_slug or interview_type is required.")
            interview = Interview(
                user_id=user_id,
                mode=payload.mode,
                title=f"{interview_type.replace('_', ' ').title()} {payload.mode.value.title()}",
                total_time_limit_seconds=payload.time_limit_seconds,
            )
            self.db.add(interview)
            self.db.flush()
            self.db.add(
                InterviewSection(
                    interview_id=interview.id,
                    interview_type=interview_type,
                    title=interview_type.replace("_", " ").title(),
                    time_limit_seconds=payload.time_limit_seconds,
                    target_question_count=payload.question_count,
                    display_order=0,
                )
            )
        self.db.commit()
        self.db.refresh(interview)
        return self._get_interview(user_id, interview.id)

    def start_interview(self, user_id: str, interview_id: str) -> Interview:
        interview = self._get_interview(user_id, interview_id)
        if interview.status == InterviewStatus.NOT_STARTED:
            now = datetime.now(UTC)
            interview.status = InterviewStatus.IN_PROGRESS
            interview.started_at = now
            self.db.commit()
        self._ensure_current_question(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def pause_interview(self, user_id: str, interview_id: str) -> Interview:
        interview = self._get_interview(user_id, interview_id)
        if interview.status != InterviewStatus.IN_PROGRESS:
            raise AppError("Only an in-progress interview can be paused.")
        self._accumulate_elapsed(interview)
        interview.status = InterviewStatus.PAUSED
        interview.paused_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def resume_interview(self, user_id: str, interview_id: str) -> Interview:
        interview = self._get_interview(user_id, interview_id)
        if interview.status != InterviewStatus.PAUSED:
            raise AppError("Only a paused interview can be resumed.")
        interview.status = InterviewStatus.IN_PROGRESS
        interview.started_at = datetime.now(UTC)  # marks the start of this new "in progress" period
        interview.paused_at = None
        self.db.commit()
        self.db.refresh(interview)
        return interview

    def _accumulate_elapsed(self, interview: Interview) -> int:
        """Server-side elapsed-time accounting (spec sections 34/58 — never
        trust a client-reported duration). `started_at` marks the beginning
        of the *current* IN_PROGRESS period (reset on every resume); this
        adds that period's real elapsed seconds to the running total and
        returns how much was just added."""
        if interview.started_at is None:
            return 0
        now = datetime.now(UTC)
        started_at = interview.started_at if interview.started_at.tzinfo else interview.started_at.replace(tzinfo=UTC)
        elapsed = max(0, int((now - started_at).total_seconds()))
        interview.time_spent_seconds += elapsed
        return elapsed

    def _current_total_elapsed_seconds(self, interview: Interview) -> int:
        """`time_spent_seconds` plus whatever has elapsed in the CURRENT
        in-progress period, without mutating anything — used only to check
        the time limit, never to award/deduct time (that's `_accumulate_elapsed`'s job,
        called on an actual pause/submit)."""
        total = interview.time_spent_seconds
        if interview.status == InterviewStatus.IN_PROGRESS and interview.started_at is not None:
            now = datetime.now(UTC)
            started_at = (
                interview.started_at if interview.started_at.tzinfo else interview.started_at.replace(tzinfo=UTC)
            )
            total += max(0, int((now - started_at).total_seconds()))
        return total

    def _is_over_time_limit(self, interview: Interview) -> bool:
        """Server-side-only timer enforcement (spec sections 34/58): never
        trust the client's clock, and never let the learner keep answering
        past a hard total time limit just because they haven't clicked
        submit — automatic submission means the SERVER cuts it off."""
        if not interview.total_time_limit_seconds:
            return False
        return self._current_total_elapsed_seconds(interview) > interview.total_time_limit_seconds

    # --- Question selection / advancement ---------------------------------------

    def _current_section(self, interview: Interview) -> InterviewSection | None:
        sections = sorted(interview.sections, key=lambda s: s.display_order)
        if interview.current_section_index >= len(sections):
            return None
        return sections[interview.current_section_index]

    def _current_attempt(self, interview: Interview) -> InterviewQuestionAttempt | None:
        attempts = sorted(interview.question_attempts, key=lambda a: a.display_order)
        return attempts[-1] if attempts else None

    def _is_resolved(self, attempt: InterviewQuestionAttempt) -> bool:
        if attempt.exercise_attempt_id:
            exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
            return exercise_attempt is not None and exercise_attempt.status != ExerciseAttemptStatus.PENDING
        if attempt.case_attempt_id:
            case_attempt = self.db.get(CaseAttempt, attempt.case_attempt_id)
            return case_attempt is not None and case_attempt.status == CaseAttemptStatus.COMPLETED
        return False

    def _section_question_count_so_far(self, interview: Interview, section: InterviewSection) -> int:
        return sum(1 for a in interview.question_attempts if a.section_id == section.id and not a.is_follow_up)

    def _pick_candidate(self, interview: Interview, section: InterviewSection) -> InterviewQuestion | None:
        pool = list(
            self.db.execute(
                select(InterviewQuestion)
                .options(selectinload(InterviewQuestion.exercise))
                .where(
                    InterviewQuestion.interview_type == section.interview_type, InterviewQuestion.is_active.is_(True)
                )
            )
            .scalars()
            .all()
        )
        candidates = [QuestionCandidate(id=q.id, interview_type=q.interview_type, difficulty=q.exercise.difficulty) for q in pool]

        # Batch-fetch every ExerciseAttempt/InterviewQuestion this section's
        # history could reference in one query each, instead of a db.get()
        # pair per attempt (this loop runs on every question pick, so an
        # interview with N prior attempts previously issued 2N point
        # queries here plus one lazy-load per question for .exercise).
        exercise_attempt_ids = {
            a.exercise_attempt_id
            for a in interview.question_attempts
            if a.interview_question_id and a.exercise_attempt_id
        }
        question_ids = {
            a.interview_question_id
            for a in interview.question_attempts
            if a.interview_question_id and a.exercise_attempt_id
        }
        exercise_attempts_by_id = (
            {
                ea.id: ea
                for ea in self.db.execute(
                    select(ExerciseAttempt).where(ExerciseAttempt.id.in_(exercise_attempt_ids))
                ).scalars().all()
            }
            if exercise_attempt_ids
            else {}
        )
        questions_by_id = (
            {
                q.id: q
                for q in self.db.execute(
                    select(InterviewQuestion)
                    .options(selectinload(InterviewQuestion.exercise))
                    .where(InterviewQuestion.id.in_(question_ids))
                ).scalars().all()
            }
            if question_ids
            else {}
        )
        history: list[HistoryEntry] = []
        for attempt in interview.question_attempts:
            if not attempt.interview_question_id or not attempt.exercise_attempt_id:
                continue
            exercise_attempt = exercise_attempts_by_id.get(attempt.exercise_attempt_id)
            question = questions_by_id.get(attempt.interview_question_id)
            if exercise_attempt is None or exercise_attempt.score is None or question is None:
                continue
            history.append(
                HistoryEntry(
                    question_id=question.id,
                    interview_type=question.interview_type,
                    difficulty=question.exercise.difficulty,
                    score=exercise_attempt.score,
                    time_limit_seconds=question.time_limit_seconds,
                    time_spent_seconds=attempt.time_spent_seconds,
                    answered_at=attempt.started_at or datetime.now(UTC),
                )
            )
        chosen = select_next_question(candidates, history, section.interview_type)
        if chosen is None:
            return None
        return self.db.get(InterviewQuestion, chosen.id)

    def _pick_interview_case(self, interview: Interview) -> Case | None:
        already_used = {
            a.case_attempt_id for a in interview.question_attempts if a.case_attempt_id
        }
        used_case_ids = set()
        for attempt_id in already_used:
            attempt = self.db.get(CaseAttempt, attempt_id)
            if attempt:
                used_case_ids.add(attempt.case_id)
        stmt = select(Case).where(Case.is_active.is_(True)).order_by(Case.title)
        all_cases = self.db.execute(stmt).scalars().all()
        candidates = [c for c in all_cases if "interview" in c.tags and c.id not in used_case_ids]
        return candidates[0] if candidates else None

    def _ensure_current_question(self, interview: Interview) -> None:
        """Ensures `interview.question_attempts` ends with a live, unresolved
        attempt for the current section — advancing sections (or completing
        the interview) as far as needed first."""
        while True:
            current = self._current_attempt(interview)

            if current is not None and not self._is_resolved(current):
                return  # still waiting on an answer — nothing to advance

            if current is not None and current.is_follow_up is False and current.interview_question_id:
                question = self.db.get(InterviewQuestion, current.interview_question_id)
                if question and question.follow_up_question_ids:
                    already_asked = {
                        a.interview_question_id
                        for a in interview.question_attempts
                        if a.parent_attempt_id == current.id
                    }
                    next_follow_up_id = next(
                        (fid for fid in question.follow_up_question_ids if fid not in already_asked), None
                    )
                    if next_follow_up_id and self._exercise_attempt_passed(current):
                        self._create_question_attempt(
                            interview,
                            interview_question_id=next_follow_up_id,
                            section_id=current.section_id,
                            parent_attempt_id=current.id,
                            is_follow_up=True,
                        )
                        return

            section = self._current_section(interview)
            if section is None:
                self._auto_complete(interview)
                return

            if section.interview_type == "CASE_STUDY":
                if self._section_question_count_so_far(interview, section) >= 1:
                    interview.current_section_index += 1
                    continue
                case = self._pick_interview_case(interview)
                if case is None:
                    interview.current_section_index += 1
                    continue
                case_attempt = self.case_service.start_attempt(interview.user_id, case.slug)
                self._create_question_attempt(interview, section_id=section.id, case_attempt_id=case_attempt.id)
                return

            if self._section_question_count_so_far(interview, section) >= section.target_question_count:
                interview.current_section_index += 1
                continue

            question = self._pick_candidate(interview, section)
            if question is None:
                interview.current_section_index += 1
                continue
            self._create_question_attempt(interview, section_id=section.id, interview_question_id=question.id)
            return

    def _auto_complete(self, interview: Interview) -> None:
        """Every section has run out of questions/cases to offer — finalize
        the interview the same way an explicit `submit_interview` call
        would. Safe to call mid-`_ensure_current_question`: `submit_interview`
        re-fetches by id, but SQLAlchemy's identity map hands back this same
        in-session `interview` instance, so the caller's own reference is
        updated too."""
        self.submit_interview(interview.user_id, interview.id)

    def _exercise_attempt_passed(self, attempt: InterviewQuestionAttempt) -> bool:
        if not attempt.exercise_attempt_id:
            return False
        exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
        return exercise_attempt is not None and (exercise_attempt.score or 0) >= 70.0

    def _create_question_attempt(
        self,
        interview: Interview,
        *,
        section_id: str | None,
        interview_question_id: str | None = None,
        case_attempt_id: str | None = None,
        parent_attempt_id: str | None = None,
        is_follow_up: bool = False,
    ) -> InterviewQuestionAttempt:
        display_order = len(interview.question_attempts)
        attempt = InterviewQuestionAttempt(
            interview_id=interview.id,
            section_id=section_id,
            interview_question_id=interview_question_id,
            case_attempt_id=case_attempt_id,
            parent_attempt_id=parent_attempt_id,
            is_follow_up=is_follow_up,
            display_order=display_order,
            started_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.flush()
        interview.question_attempts.append(attempt)
        section = next((s for s in interview.sections if s.id == section_id), None)
        if section and section.started_at is None:
            section.started_at = datetime.now(UTC)
        return attempt

    # --- Answering ---------------------------------------------------------------

    def answer_question(
        self, user_id: str, interview_id: str, payload: AnswerInterviewQuestionRequest
    ) -> tuple[Interview, float | None, bool, str | None, str | None]:
        interview = self._get_interview(user_id, interview_id)
        if interview.status == InterviewStatus.IN_PROGRESS and self._is_over_time_limit(interview):
            self.submit_interview(user_id, interview_id)
            raise AppError("Time is up — this interview was automatically submitted.")
        if interview.status != InterviewStatus.IN_PROGRESS:
            raise AppError("This interview is not in progress.")

        attempt = self._current_attempt(interview)
        if attempt is None or attempt.interview_question_id is None:
            raise AppError("There is no active question to answer right now.")
        if self._is_resolved(attempt):
            raise AppError("This question has already been answered.")

        question = self.db.get(InterviewQuestion, attempt.interview_question_id)
        exercise = question.exercise
        content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]

        now = datetime.now(UTC)
        started_at = attempt.started_at if attempt.started_at and attempt.started_at.tzinfo else (
            attempt.started_at.replace(tzinfo=UTC) if attempt.started_at else now
        )
        attempt.time_spent_seconds = max(0, int((now - started_at).total_seconds()))

        is_auto_graded = True
        score: float | None = None
        explanation: str | None = None
        correct_answer: str | None = None

        if exercise.exercise_type == "SQL":
            if not payload.submitted_query:
                raise AppError("submitted_query is required for a SQL question.")
            result = self.sql_service.submit(user_id, exercise, content, payload.submitted_query)
            attempt.exercise_attempt_id = result.attempt_id
            score = result.score
            explanation = result.explanation
        elif exercise.exercise_type == "PYTHON":
            if not payload.submitted_code:
                raise AppError("submitted_code is required for a Python question.")
            result = self.python_service.submit(user_id, exercise, content, payload.submitted_code)
            attempt.exercise_attempt_id = result.attempt_id
            score = result.score
            explanation = result.explanation
        elif exercise.exercise_type == "EXCEL":
            if not payload.submitted_sheets:
                raise AppError("submitted_sheets is required for an Excel question.")
            result = self.excel_service.submit(user_id, exercise, content, payload.submitted_sheets)
            attempt.exercise_attempt_id = result.attempt_id
            score = result.score
            explanation = result.explanation
        elif exercise.exercise_type == "DBT":
            if not payload.submitted_query:
                raise AppError("submitted_query is required for a dbt question.")
            result = self.dbt_service.submit(user_id, exercise, content, payload.submitted_query)
            attempt.exercise_attempt_id = result.attempt_id
            score = result.score
            explanation = result.explanation
        else:
            response = self.exercise_service.submit_attempt(
                user_id,
                exercise.slug,
                SubmitExerciseAttemptRequest(
                    submitted_answer=payload.submitted_answer or "",
                    self_reported_score=payload.self_reported_score,
                    rubric_selections=payload.rubric_selections,
                ),
            )
            attempt.exercise_attempt_id = response.attempt.id
            score = response.attempt.score
            is_auto_graded = response.is_auto_graded
            explanation = response.explanation
            correct_answer = response.correct_answer

        self.db.flush()
        self._ensure_current_question(interview)
        self.db.commit()
        self.db.refresh(interview)
        return interview, score, is_auto_graded, explanation, correct_answer

    # --- Submission & scoring ----------------------------------------------------

    def submit_interview(self, user_id: str, interview_id: str) -> Interview:
        interview = self._get_interview(user_id, interview_id)
        if interview.status == InterviewStatus.COMPLETED:
            raise AppError("This interview has already been completed.")

        if interview.status == InterviewStatus.IN_PROGRESS:
            self._accumulate_elapsed(interview)

        scored_questions: list[ScoredQuestion] = []
        for attempt in interview.question_attempts:
            section = next((s for s in interview.sections if s.id == attempt.section_id), None)
            interview_type = section.interview_type if section else "SQL"

            if attempt.exercise_attempt_id:
                exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
                if exercise_attempt and exercise_attempt.score is not None:
                    question = (
                        self.db.get(InterviewQuestion, attempt.interview_question_id)
                        if attempt.interview_question_id
                        else None
                    )
                    scored_questions.append(
                        ScoredQuestion(
                            interview_type=interview_type,
                            score=exercise_attempt.score,
                            time_limit_seconds=question.time_limit_seconds if question else None,
                            time_spent_seconds=attempt.time_spent_seconds,
                        )
                    )
            elif attempt.case_attempt_id:
                case_attempt = self.db.get(CaseAttempt, attempt.case_attempt_id)
                if case_attempt and case_attempt.score:
                    scored_questions.append(
                        ScoredQuestion(interview_type="CASE_STUDY", score=case_attempt.score.get("overall", 0.0))
                    )

        weights = None
        if interview.template_id:
            template = self.db.get(InterviewTemplate, interview.template_id)
            weights = template.rubric_weights if template else None

        result = score_interview(scored_questions, weights)
        interview.score = {
            "overall": result.overall,
            "dimensions": [
                {"dimension": d.dimension, "score": d.score, "question_count": d.question_count}
                for d in result.dimensions
            ],
        }
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(interview)

        # Always snapshot on completion — not just when a learner presses an
        # explicit "submit" button — since most interviews actually finish by
        # naturally running out of questions (`_auto_complete`, which also
        # calls this method), not by an explicit early-submit action.
        self.readiness_service.snapshot_readiness(user_id)
        return interview

    def abandon_interview(self, user_id: str, interview_id: str) -> Interview:
        interview = self._get_interview(user_id, interview_id)
        if interview.status in (InterviewStatus.COMPLETED, InterviewStatus.ABANDONED):
            raise AppError("This interview is already finished.")
        interview.status = InterviewStatus.ABANDONED
        self.db.commit()
        self.db.refresh(interview)
        return interview

    # --- Review (spec section 45) --------------------------------------------------

    def _test_outcomes_for(self, exercise_attempt_id: str) -> list[InterviewTestOutcomeSchema]:
        """The REAL per-check results the grading engine already recorded —
        SQL/Python/Excel each persist their own test-result rows. Hidden tests
        are included here because review only ever runs on a finished
        interview."""
        outcomes: list[InterviewTestOutcomeSchema] = []
        for model in (SqlExerciseTestResult, PythonExerciseTestResult, ExcelExerciseTestResult):
            rows = (
                self.db.execute(
                    select(model).where(model.attempt_id == exercise_attempt_id).order_by(model.display_order)
                )
                .scalars()
                .all()
            )
            outcomes.extend(
                InterviewTestOutcomeSchema(
                    name=r.test_name, passed=r.passed, is_hidden=r.is_hidden, message=r.message or ""
                )
                for r in rows
            )
        return outcomes

    def _review_one(self, attempt: InterviewQuestionAttempt, interview: Interview) -> InterviewQuestionReviewSchema:
        section = next((s for s in interview.sections if s.id == attempt.section_id), None)
        interview_type = section.interview_type if section else "SQL"

        review = InterviewQuestionReviewSchema(
            attempt_id=attempt.id,
            display_order=attempt.display_order,
            interview_type=interview_type,
            is_follow_up=attempt.is_follow_up,
            title="(unanswered)",
            time_spent_seconds=attempt.time_spent_seconds,
        )

        if attempt.case_attempt_id:
            case_attempt = self.db.get(CaseAttempt, attempt.case_attempt_id)
            if case_attempt is not None:
                review.title = case_attempt.case.title
                review.prompt = case_attempt.case.problem_statement
                review.case_attempt_id = case_attempt.id
                review.case_slug = case_attempt.case.slug
                if case_attempt.score:
                    review.score = case_attempt.score.get("overall")
                    review.passed = (review.score or 0) >= 70.0
            return review

        if not attempt.interview_question_id:
            return review

        question = self.db.get(InterviewQuestion, attempt.interview_question_id)
        if question is None:
            return review

        exercise = question.exercise
        content = load_exercise_file(exercise.content_reference)  # type: ignore[arg-type]
        review.question_slug = question.slug
        review.title = exercise.title
        review.prompt = content.prompt
        review.time_limit_seconds = question.time_limit_seconds
        review.correct_answer = content.correct_answer
        review.explanation = content.explanation
        review.solution = content.solution
        if question.time_limit_seconds:
            review.over_time = attempt.time_spent_seconds > question.time_limit_seconds

        if exercise.skill_id:
            skill = self.db.get(Skill, exercise.skill_id)
            if skill is not None:
                review.skill_slug = skill.slug
                review.skill_name = skill.name
        if exercise.lesson_id:
            lesson = self.db.get(Lesson, exercise.lesson_id)
            if lesson is not None:
                review.recommended_lesson_slug = lesson.slug
                review.recommended_lesson_title = lesson.title

        if attempt.exercise_attempt_id:
            exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
            if exercise_attempt is not None:
                review.score = exercise_attempt.score
                review.passed = exercise_attempt.status == ExerciseAttemptStatus.PASSED
                review.submitted_answer = exercise_attempt.submitted_answer
                review.test_outcomes = self._test_outcomes_for(exercise_attempt.id)

        return review

    def review_interview(self, user_id: str, interview_id: str) -> InterviewReviewResponse:
        interview = self._get_interview(user_id, interview_id)
        if interview.status not in (InterviewStatus.COMPLETED, InterviewStatus.ABANDONED):
            raise AppError("Finish this interview before reviewing it.")

        attempts = sorted(interview.question_attempts, key=lambda a: a.display_order)
        return InterviewReviewResponse(
            interview=self.to_schema(interview, user_id),
            questions=[self._review_one(a, interview) for a in attempts],
        )

    # --- Retry (spec section 47) ---------------------------------------------------

    def retry_interview(self, user_id: str, interview_id: str, payload: RetryInterviewRequest) -> Interview:
        """Always builds a NEW interview rather than reopening the old one, so
        the original attempt (and its score/history) survives untouched."""
        original = self._get_interview(user_id, interview_id)
        scope = (payload.scope or "FULL").upper()

        if scope == "FULL":
            if original.template_id:
                template = self.db.get(InterviewTemplate, original.template_id)
                if template is None:
                    raise NotFoundError("The template this interview was built from no longer exists.")
                return self.create_interview(
                    user_id, CreateInterviewRequest(mode=original.mode, template_slug=template.slug)
                )
            section = next(iter(sorted(original.sections, key=lambda s: s.display_order)), None)
            if section is None:
                raise AppError("This interview has no sections to retry.")
            return self.create_interview(
                user_id,
                CreateInterviewRequest(
                    mode=original.mode,
                    interview_type=section.interview_type,
                    time_limit_seconds=section.time_limit_seconds,
                    question_count=section.target_question_count,
                ),
            )

        if scope == "SECTION":
            section = next((s for s in original.sections if s.id == payload.section_id), None)
            if section is None:
                raise NotFoundError(f"Section '{payload.section_id}' is not part of this interview.")
            return self.create_interview(
                user_id,
                CreateInterviewRequest(
                    mode=original.mode,
                    interview_type=section.interview_type,
                    time_limit_seconds=section.time_limit_seconds,
                    question_count=section.target_question_count,
                ),
            )

        if scope == "QUESTION":
            question = (
                self.db.get(InterviewQuestion, payload.interview_question_id)
                if payload.interview_question_id
                else None
            )
            if question is None:
                raise NotFoundError(f"Interview question '{payload.interview_question_id}' was not found.")
            return self._start_pinned_to_question(user_id, question)

        raise AppError(f"Unknown retry scope '{payload.scope}'. Use FULL, SECTION or QUESTION.")

    def _start_pinned_to_question(self, user_id: str, question: InterviewQuestion) -> Interview:
        """A single-question PRACTICE interview pinned to this EXACT question
        (spec section 52 — practicing a specific bookmarked/reviewed question)
        rather than letting adaptive selection choose a different one from
        its pool. Used by both `retry_interview`'s QUESTION scope and
        `create_interview`'s `question_id` shortcut."""
        interview = self.create_interview(
            user_id,
            CreateInterviewRequest(
                mode=InterviewMode.PRACTICE,
                interview_type=question.interview_type.value,
                time_limit_seconds=question.time_limit_seconds,
                question_count=1,
            ),
        )
        interview.status = InterviewStatus.IN_PROGRESS
        interview.started_at = datetime.now(UTC)
        section = interview.sections[0]
        self._create_question_attempt(interview, section_id=section.id, interview_question_id=question.id)
        self.db.commit()
        self.db.refresh(interview)
        return interview

    # --- Serialization -----------------------------------------------------------

    def _attempt_to_schema(self, attempt: InterviewQuestionAttempt, user_id: str) -> InterviewQuestionAttemptSchema:
        question_detail: InterviewQuestionDetail | None = None
        if attempt.interview_question_id:
            question = self.db.get(InterviewQuestion, attempt.interview_question_id)
            if question is not None:
                question_detail = self._question_detail(question, user_id)

        exercise_attempt_score: float | None = None
        if attempt.exercise_attempt_id:
            exercise_attempt = self.db.get(ExerciseAttempt, attempt.exercise_attempt_id)
            exercise_attempt_score = exercise_attempt.score if exercise_attempt else None

        case_attempt_status: str | None = None
        if attempt.case_attempt_id:
            case_attempt = self.db.get(CaseAttempt, attempt.case_attempt_id)
            case_attempt_status = case_attempt.status.value if case_attempt else None

        return InterviewQuestionAttemptSchema(
            id=attempt.id,
            section_id=attempt.section_id,
            interview_question_id=attempt.interview_question_id,
            case_attempt_id=attempt.case_attempt_id,
            exercise_attempt_id=attempt.exercise_attempt_id,
            parent_attempt_id=attempt.parent_attempt_id,
            is_follow_up=attempt.is_follow_up,
            display_order=attempt.display_order,
            started_at=attempt.started_at,
            time_spent_seconds=attempt.time_spent_seconds,
            question=question_detail,
            exercise_attempt_score=exercise_attempt_score,
            case_attempt_status=case_attempt_status,
        )

    def to_schema(self, interview: Interview, user_id: str) -> InterviewSchema:
        sections = sorted(interview.sections, key=lambda s: s.display_order)
        attempts = sorted(interview.question_attempts, key=lambda a: a.display_order)
        attempt_schemas = [self._attempt_to_schema(a, user_id) for a in attempts]

        current_question = None
        if attempts:
            last = attempts[-1]
            if not self._is_resolved(last):
                current_question = attempt_schemas[-1]

        score = None
        if interview.score:
            score = InterviewScoreSchema(
                overall=interview.score["overall"],
                dimensions=[InterviewDimensionScoreSchema(**d) for d in interview.score["dimensions"]],
            )

        return InterviewSchema(
            id=interview.id,
            template_id=interview.template_id,
            mode=interview.mode,
            status=interview.status,
            title=interview.title,
            total_time_limit_seconds=interview.total_time_limit_seconds,
            time_spent_seconds=interview.time_spent_seconds,
            current_section_index=interview.current_section_index,
            started_at=interview.started_at,
            paused_at=interview.paused_at,
            completed_at=interview.completed_at,
            score=score,
            feedback=interview.feedback,
            created_at=interview.created_at,
            sections=[
                InterviewSectionSchema(
                    id=s.id,
                    interview_type=s.interview_type,
                    title=s.title,
                    time_limit_seconds=s.time_limit_seconds,
                    display_order=s.display_order,
                    started_at=s.started_at,
                    completed_at=s.completed_at,
                    time_spent_seconds=s.time_spent_seconds,
                )
                for s in sections
            ],
            question_attempts=attempt_schemas,
            current_question=current_question,
        )
