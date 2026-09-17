from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.content.loader import load_exercise_file
from app.core.errors import AppError, NotFoundError
from app.models.assessment import Assessment, AssessmentAnswer, AssessmentAttempt, AssessmentQuestion
from app.models.enums import AssessmentAttemptStatus, AssessmentRetryPolicy
from app.models.exercise import Exercise
from app.repositories.assessment import AssessmentAttemptRepository, AssessmentRepository
from app.repositories.module import ModuleRepository
from app.schemas.assessment import (
    Assessment as AssessmentSchema,
)
from app.schemas.assessment import (
    AssessmentAnswerResult,
    StartAssessmentResponse,
    SubmitAssessmentRequest,
    SubmitAssessmentResponse,
)
from app.schemas.assessment import (
    AssessmentAttempt as AssessmentAttemptSchema,
)
from app.schemas.exercise import ExerciseContent as ExerciseContentSchema
from app.services.exercise_service import ExerciseService
from app.services.grading import grade
from app.services.mastery import MasteryService


class AssessmentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AssessmentRepository(db)
        self.attempt_repo = AssessmentAttemptRepository(db)
        self.module_repo = ModuleRepository(db)
        self.exercise_service = ExerciseService(db)
        self.mastery_service = MasteryService(db)

    def _question_count(self, assessment_id: str) -> int:
        return self.db.execute(
            select(func.count())
            .select_from(AssessmentQuestion)
            .where(AssessmentQuestion.assessment_id == assessment_id)
        ).scalar_one()

    def to_schema(self, assessment: Assessment) -> AssessmentSchema:
        return AssessmentSchema(
            id=assessment.id,
            module_id=assessment.module_id,
            module_slug=assessment.module.slug,
            slug=assessment.slug,
            title=assessment.title,
            description=assessment.description,
            time_limit_minutes=assessment.time_limit_minutes,
            passing_score=assessment.passing_score,
            retry_policy=assessment.retry_policy,
            max_attempts=assessment.max_attempts,
            question_count=self._question_count(assessment.id),
            is_active=assessment.is_active,
        )

    def get_by_module_slug(self, module_slug: str) -> AssessmentSchema:
        module = self.module_repo.get_by_slug(module_slug)
        if module is None:
            raise NotFoundError(f"Module '{module_slug}' was not found.")
        assessment = self.repo.get_by_module_id(module.id)
        if assessment is None:
            raise NotFoundError(f"Module '{module_slug}' has no assessment.")
        return self.to_schema(assessment)

    def _get_model_by_slug(self, slug: str) -> Assessment:
        assessment = self.repo.get_by_slug(slug)
        if assessment is None:
            raise NotFoundError(f"Assessment '{slug}' was not found.", details={"slug": slug})
        return assessment

    def start_attempt(self, user_id: str, slug: str) -> StartAssessmentResponse:
        assessment = self._get_model_by_slug(slug)

        if assessment.retry_policy == AssessmentRetryPolicy.LIMITED and assessment.max_attempts:
            existing = self.attempt_repo.list_for_user_and_assessment(user_id, assessment.id)
            if len(existing) >= assessment.max_attempts:
                raise AppError(
                    f"Maximum attempts ({assessment.max_attempts}) reached for this assessment.",
                    details={"assessment": slug},
                )

        attempt = AssessmentAttempt(
            user_id=user_id,
            assessment_id=assessment.id,
            status=AssessmentAttemptStatus.IN_PROGRESS,
            started_at=datetime.now(UTC),
        )
        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        questions = (
            self.db.execute(
                select(Exercise)
                .join(AssessmentQuestion, AssessmentQuestion.exercise_id == Exercise.id)
                .where(AssessmentQuestion.assessment_id == assessment.id)
                .order_by(AssessmentQuestion.display_order)
            )
            .scalars()
            .all()
        )
        question_schemas: list[ExerciseContentSchema] = []
        for exercise in questions:
            content = load_exercise_file(exercise.content_reference) if exercise.content_reference else None
            base = self.exercise_service.to_schema(exercise)
            question_schemas.append(
                ExerciseContentSchema(
                    **base.model_dump(),
                    prompt=content.prompt if content else "",
                    choices=content.choices if content else None,
                    hint_count=0,  # hints are not offered during a timed assessment
                    best_attempt=None,
                    attempt_count=0,
                )
            )

        return StartAssessmentResponse(
            attempt=AssessmentAttemptSchema.model_validate(attempt), questions=question_schemas
        )

    def submit_attempt(
        self, user_id: str, slug: str, attempt_id: str, payload: SubmitAssessmentRequest
    ) -> SubmitAssessmentResponse:
        assessment = self._get_model_by_slug(slug)
        attempt = self.db.get(AssessmentAttempt, attempt_id)
        if attempt is None or attempt.assessment_id != assessment.id or attempt.user_id != user_id:
            raise NotFoundError("Assessment attempt was not found.", details={"attempt_id": attempt_id})
        if attempt.status != AssessmentAttemptStatus.IN_PROGRESS:
            raise AppError("This attempt has already been submitted.", details={"attempt_id": attempt_id})

        aq_rows = (
            self.db.execute(
                select(AssessmentQuestion).where(AssessmentQuestion.assessment_id == assessment.id)
            )
            .scalars()
            .all()
        )
        points_by_exercise = {aq.exercise_id: aq.points for aq in aq_rows}
        total_points = sum(points_by_exercise.values()) or 1

        answers_by_exercise = {a.exercise_id: a.submitted_answer for a in payload.answers}
        results: list[AssessmentAnswerResult] = []
        earned_points = 0.0
        touched_skills: set[str] = set()

        for exercise_id, points in points_by_exercise.items():
            exercise = self.db.get(Exercise, exercise_id)
            if exercise is None or not exercise.content_reference:
                continue
            content = load_exercise_file(exercise.content_reference)
            submitted = answers_by_exercise.get(exercise_id, "")
            grade_result = grade(content, submitted)

            score = grade_result.score if grade_result.is_auto_graded else None
            is_correct = grade_result.is_correct
            if score is not None:
                earned_points += (score / 100.0) * points

            answer = AssessmentAnswer(
                attempt_id=attempt.id,
                exercise_id=exercise_id,
                submitted_answer=submitted,
                is_correct=is_correct,
                score=score,
            )
            self.db.add(answer)

            if exercise.skill_id:
                touched_skills.add(exercise.skill_id)

            results.append(
                AssessmentAnswerResult(
                    exercise_id=exercise_id,
                    is_correct=is_correct,
                    score=score,
                    correct_answer=content.correct_answer,
                    explanation=content.explanation,
                )
            )

        final_score = round(100 * earned_points / total_points, 1)
        passed = final_score >= assessment.passing_score

        attempt.status = AssessmentAttemptStatus.PASSED if passed else AssessmentAttemptStatus.FAILED
        attempt.score = final_score
        attempt.time_spent_seconds = payload.time_spent_seconds
        attempt.completed_at = datetime.now(UTC)
        self.db.flush()

        for skill_id in touched_skills:
            self.mastery_service.recalculate(user_id, skill_id)

        self.db.commit()
        self.db.refresh(attempt)

        return SubmitAssessmentResponse(
            attempt=AssessmentAttemptSchema.model_validate(attempt), passed=passed, answers=results
        )
