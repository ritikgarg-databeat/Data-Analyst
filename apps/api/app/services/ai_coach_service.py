"""AI Layer (Phase 10) — case/interview/project coaching. Companion to
`app/services/ai_service.py` (which holds the shared `_dispatch` plumbing
this file reuses by composing an `AIService` instance, matching how other
services in this codebase compose sibling services directly). Covers: Case
Study Coach + 4 coaching modes, the AI Case Interviewer, the AI Behavioral
Interviewer, the AI Interview Debrief, Communication/Storytelling/Executive-
Summary coaching, the Learning Planner's explanation layer, AI Skill
Diagnosis, and AI Project Review."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.ai import context as ai_context
from app.ai.prompts.case_interviewer import render_case_coach_system_prompt
from app.core.config import Settings
from app.core.errors import NotFoundError
from app.models.enums import AIFeature
from app.models.exercise import Exercise
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import Interview, InterviewQuestion, InterviewQuestionAttempt
from app.schemas.ai import (
    AIChatResponse,
    AIExecSummaryResult,
    AIPlanDayExplanation,
    AIPlanExplanationResult,
    AISkillDiagnosisResult,
    AIStructuredResponse,
)
from app.services.ai_service import AIService
from app.services.case_service import CaseService
from app.services.exercise_service import ExerciseService
from app.services.interview_readiness_service import InterviewReadinessService
from app.services.interview_service import InterviewService
from app.services.project_service import ProjectService
from app.services.skill_service import SkillService


class AICoachService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.ai = AIService(db, settings)
        self.cases = CaseService(db)
        self.interviews = InterviewService(db)
        self.readiness = InterviewReadinessService(db)
        self.exercises = ExerciseService(db)
        self.skills = SkillService(db)
        self.projects = ProjectService(db)

    # --- Case Coach --------------------------------------------------------

    def case_coach(
        self, user_id: str, *, attempt_id: str, message: str, coaching_mode: str, conversation_id: str | None
    ) -> AIChatResponse:
        attempt = self.cases.get_attempt(user_id, attempt_id)
        context_payload = {
            "case": ai_context.build_case_public_context(attempt.case),
            "attempt": ai_context.build_case_attempt_context(attempt),
            "coaching_mode": coaching_mode,
        }
        system_prompt = render_case_coach_system_prompt(coaching_mode)
        return self.ai._chat_dispatch(  # noqa: SLF001 — intra-package reuse of the shared dispatch plumbing
            user_id=user_id,
            feature=AIFeature.CASE_COACH,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="case",
            context_id=attempt_id,
            mode="COACH",
            system_prompt_override=system_prompt,
        )

    # --- AI Case Interviewer ------------------------------------------------

    def case_interviewer_turn(
        self, user_id: str, *, attempt_id: str, message: str, conversation_id: str | None
    ) -> AIChatResponse:
        attempt = self.cases.get_attempt(user_id, attempt_id)
        conversation = None
        covered: set[int] = set()
        transcript: list[dict] = []
        if conversation_id:
            conversation = self.ai._get_conversation(user_id, conversation_id)  # noqa: SLF001
            for m in conversation.messages:
                transcript.append(
                    {"role": m.role.value if hasattr(m.role, "value") else m.role, "content": m.content}
                )
                if m.structured_output and m.structured_output.get("revealed_info_keys"):
                    covered.update(
                        int(k) for k in m.structured_output["revealed_info_keys"] if str(k).isdigit()
                    )

        context_payload = ai_context.build_case_interviewer_context(
            case=attempt.case,
            clarification_guidance=attempt.case.clarification_guidance or [],
            covered_topic_indexes=sorted(covered),
            transcript=transcript,
        )
        return self.ai._chat_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.CASE_INTERVIEWER,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="case",
            context_id=attempt_id,
            mode="INTERVIEWER",
        )

    # --- AI Behavioral Interviewer -------------------------------------------

    def behavioral_interviewer_turn(
        self, user_id: str, *, interview_question_attempt_id: str, message: str, conversation_id: str | None
    ) -> AIChatResponse:
        attempt = self.db.get(InterviewQuestionAttempt, interview_question_attempt_id)
        interview = self.db.get(Interview, attempt.interview_id) if attempt else None
        if attempt is None or interview is None or interview.user_id != user_id:
            raise NotFoundError(
                f"Interview question attempt '{interview_question_attempt_id}' was not found."
            )
        question = (
            self.db.get(InterviewQuestion, attempt.interview_question_id)
            if attempt.interview_question_id
            else None
        )
        prompt_text = "(no prompt available)"
        if question is not None:
            exercise_row = self.db.get(Exercise, question.exercise_id)
            if exercise_row is not None:
                prompt_text = self.exercises.get_content(exercise_row.slug, user_id).prompt

        conversation = None
        transcript: list[dict] = []
        if conversation_id:
            conversation = self.ai._get_conversation(user_id, conversation_id)  # noqa: SLF001
            transcript = [
                {"role": m.role.value if hasattr(m.role, "value") else m.role, "content": m.content}
                for m in conversation.messages
            ]

        context_payload = {"prompt": prompt_text, "transcript_so_far": transcript}
        return self.ai._chat_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.BEHAVIORAL_INTERVIEWER,
            context_payload=context_payload,
            user_message=message,
            conversation_id=conversation_id,
            context_type="interview",
            context_id=interview_question_attempt_id,
            mode="INTERVIEWER",
        )

    # --- AI Interview Debrief ------------------------------------------------

    def interview_debrief(self, user_id: str, *, interview_id: str) -> AIStructuredResponse:
        interview = self.interviews.get_interview(user_id, interview_id)
        if interview.score is None:
            from app.core.errors import AppError

            raise AppError(
                "This interview hasn't been completed yet — finish it before requesting a debrief."
            )
        review = self.interviews.review_interview(user_id, interview_id)
        context_payload = ai_context.build_interview_debrief_context(
            score=interview.score, question_reviews=review.questions
        )
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.INTERVIEW_DEBRIEF,
            context_payload=context_payload,
            user_message="Debrief this completed interview.",
            context_type="interview",
        )

    # --- Communication / Storytelling / Executive Summary -------------------

    def communication_review(self, user_id: str, *, text: str, audience: str | None) -> AIStructuredResponse:
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.COMMUNICATION_COACH,
            context_payload={"text": text, "audience": audience},
            user_message="Review this for communication quality.",
            context_type="communication",
        )

    def storytelling_review(
        self, user_id: str, *, findings_text: str, chart_description: str | None
    ) -> AIStructuredResponse:
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.STORYTELLING_COACH,
            context_payload={"findings_text": findings_text, "chart_description": chart_description},
            user_message="Coach my data storytelling.",
            context_type="communication",
        )

    def exec_summary(self, user_id: str, *, analysis_text: str) -> AIExecSummaryResult:
        response = self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.EXEC_SUMMARY,
            context_payload={"analysis_text": analysis_text},
            user_message="Turn this into a 5-line executive summary.",
            context_type="communication",
        )
        if response.structured and response.structured_valid:
            return AIExecSummaryResult.model_validate(response.structured)
        return AIExecSummaryResult(
            what_happened=response.raw_text, why="", impact="", recommendation="", next_step=""
        )

    # --- Learning Planner explanation ---------------------------------------

    def explain_plan(self, user_id: str, *, plan_id: str) -> AIPlanExplanationResult:
        plan = self.readiness.get_latest_plan(user_id)
        if plan is None or plan.id != plan_id:
            raise NotFoundError(f"Plan '{plan_id}' was not found.")
        weaknesses = self.readiness.get_weaknesses(user_id)
        readiness = self.readiness.get_readiness(user_id)
        context_payload = {
            "plan_days": [d.model_dump(mode="json") for d in plan.days],
            "weaknesses": [w.model_dump(mode="json") for w in weaknesses],
            "readiness": readiness.model_dump(mode="json"),
        }
        response = self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.LEARNING_PLANNER,
            context_payload=context_payload,
            user_message="Explain why each day of this plan was chosen.",
            context_type="plan",
        )
        if response.structured and response.structured_valid:
            return AIPlanExplanationResult.model_validate(response.structured)
        # Degrade to the provider's raw text applied to every real day rather
        # than an empty list — with AI_PROVIDER=local (this platform's
        # zero-configuration default) no provider ever returns valid
        # structured JSON, and an empty result would make this feature
        # produce nothing useful out of the box.
        return AIPlanExplanationResult(
            day_explanations=[
                AIPlanDayExplanation(day_number=day.day_number, why=response.raw_text) for day in plan.days
            ]
        )

    # --- AI Skill Diagnosis --------------------------------------------------

    def diagnose_skill(self, user_id: str, *, exercise_attempt_id: str) -> AISkillDiagnosisResult:
        attempt = self.db.get(ExerciseAttempt, exercise_attempt_id)
        if attempt is None or attempt.user_id != user_id:
            raise NotFoundError(f"Exercise attempt '{exercise_attempt_id}' was not found.")
        exercise_row = self.db.get(Exercise, attempt.exercise_id)
        if exercise_row is None:
            raise NotFoundError(f"Exercise for attempt '{exercise_attempt_id}' was not found.")
        content = self.exercises.get_content(exercise_row.slug, user_id)
        skill_slug = content.skill_slug
        mastery_score = None
        if skill_slug:
            for user_skill in self.skills.list_user_skills(user_id):
                if user_skill.skill.slug == skill_slug:
                    mastery_score = user_skill.mastery_score
                    break

        context_payload = {
            "exercise": {
                "prompt": content.prompt,
                "difficulty": content.difficulty,
                "skill_slug": skill_slug,
            },
            "attempt": {
                "score": attempt.score,
                "submitted_answer": attempt.submitted_answer,
                "hints_used": attempt.hints_used,
            },
            "current_mastery_score": mastery_score,
        }
        response = self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.SKILL_DIAGNOSIS,
            context_payload=context_payload,
            user_message="Diagnose this attempt.",
            context_type="exercise",
        )
        result = (
            AISkillDiagnosisResult.model_validate(response.structured)
            if response.structured and response.structured_valid
            else AISkillDiagnosisResult(diagnosis_summary=response.raw_text)
        )
        from app.models.ai import AISkillDiagnosis

        self.db.add(
            AISkillDiagnosis(
                user_id=user_id,
                skill_slug=skill_slug,
                exercise_attempt_id=exercise_attempt_id,
                diagnosis=result.diagnosis_summary,
                strength_areas=[
                    o.skill for o in result.skill_observations if "strong" in o.assessment.lower()
                ],
                improvement_areas=[
                    o.skill for o in result.skill_observations if "strong" not in o.assessment.lower()
                ],
                recommended_exercise_slugs=[],
            )
        )
        self.db.commit()
        return result

    # --- AI Project Review ----------------------------------------------------

    def project_review(self, user_id: str, *, project_id: str) -> AIStructuredResponse:
        project = self.projects.get(user_id, project_id)
        context_payload = project.model_dump(mode="json")
        return self.ai._structured_dispatch(  # noqa: SLF001
            user_id=user_id,
            feature=AIFeature.PROJECT_REVIEW,
            context_payload=context_payload,
            user_message="Review this completed project.",
            context_type="project",
        )
