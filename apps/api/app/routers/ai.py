"""AI Layer (Phase 10) endpoints — thin routers, no business logic, matching
this codebase's convention (see app/routers/interviews.py). Every route
delegates to exactly one AIService/AICoachService method. Grouped into one
file (unlike most Phase 1-9 domains, which get one router per resource)
because every route here shares the same underlying Gateway/settings/usage
plumbing rather than being independent CRUD resources."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_ai_coach_service, get_ai_service
from app.schemas.ai import (
    AIChatResponse,
    AIConversationListItemSchema,
    AIConversationSchema,
    AIExecSummaryResult,
    AIKnowledgeAnswerResult,
    AIMistakeMemorySchema,
    AIPlanExplanationResult,
    AISettingsSchema,
    AISkillDiagnosisResult,
    AISkillDiagnosisSchema,
    AIStructuredResponse,
    AIUsageResponse,
    AskMentorRequest,
    BehavioralInterviewerTurnRequest,
    CaseCoachRequest,
    CaseInterviewerTurnRequest,
    CommunicationReviewRequest,
    DebugSqlRequest,
    DomainCoachRequest,
    EdaAssistRequest,
    ExecSummaryRequest,
    HintLevelRequest,
    NlToPythonRequest,
    NlToSqlRequest,
    OptimizeSqlRequest,
    PlanExplanationRequest,
    ReviewAnalysisRequest,
    ReviewInsightRequest,
    ReviewPythonRequest,
    ReviewSqlRequest,
    SkillDiagnosisRequest,
    StorytellingReviewRequest,
    UpdateAISettingsRequest,
)
from app.services.ai_coach_service import AICoachService
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])

AIServiceDep = Annotated[AIService, Depends(get_ai_service)]
AICoachServiceDep = Annotated[AICoachService, Depends(get_ai_coach_service)]


# --- Settings / usage / conversations --------------------------------------


@router.get("/settings", response_model=AISettingsSchema)
def get_ai_settings(user_id: CurrentUserId, service: AIServiceDep) -> AISettingsSchema:
    return service.get_settings(user_id)


@router.patch("/settings", response_model=AISettingsSchema)
def update_ai_settings(
    payload: UpdateAISettingsRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AISettingsSchema:
    return service.update_settings(user_id, payload)


@router.get("/usage", response_model=AIUsageResponse)
def get_ai_usage(user_id: CurrentUserId, service: AIServiceDep) -> AIUsageResponse:
    return service.get_usage_today(user_id)


@router.get("/conversations", response_model=list[AIConversationListItemSchema])
def list_conversations(user_id: CurrentUserId, service: AIServiceDep) -> list[AIConversationListItemSchema]:
    return service.list_conversations(user_id)


@router.get("/conversations/{conversation_id}", response_model=AIConversationSchema)
def get_conversation(
    conversation_id: str, user_id: CurrentUserId, service: AIServiceDep
) -> AIConversationSchema:
    return service.get_conversation(user_id, conversation_id)


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, user_id: CurrentUserId, service: AIServiceDep) -> None:
    service.delete_conversation(user_id, conversation_id)


# --- Mentor + Socratic hints -------------------------------------------------


@router.post("/mentor", response_model=AIChatResponse)
def ask_mentor(payload: AskMentorRequest, user_id: CurrentUserId, service: AIServiceDep) -> AIChatResponse:
    return service.ask_mentor(
        user_id,
        message=payload.message,
        context_type=payload.context_type,
        context_id=payload.context_id,
        conversation_id=payload.conversation_id,
        mode=payload.mode,
    )


@router.post("/mentor/hint", response_model=AIChatResponse)
def send_hint(payload: HintLevelRequest, user_id: CurrentUserId, service: AIServiceDep) -> AIChatResponse:
    return service.send_hint(
        user_id,
        context_type=payload.context_type,
        context_id=payload.context_id,
        hint_level=payload.hint_level,
        conversation_id=payload.conversation_id,
    )


# --- SQL ---------------------------------------------------------------------


@router.post("/sql/review", response_model=AIStructuredResponse)
def review_sql(
    payload: ReviewSqlRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.review_sql(
        user_id,
        query=payload.query,
        question=payload.question,
        engine=payload.engine,
        database=payload.database,
    )


@router.post("/sql/debug", response_model=AIStructuredResponse)
def debug_sql(
    payload: DebugSqlRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.debug_sql(
        user_id,
        query=payload.query,
        error_message=payload.error_message,
        engine=payload.engine,
        database=payload.database,
    )


@router.post("/sql/optimize", response_model=AIStructuredResponse)
def optimize_sql(
    payload: OptimizeSqlRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.optimize_sql(
        user_id,
        query=payload.query,
        engine=payload.engine,
        database=payload.database,
        execution_time_ms=payload.execution_time_ms,
    )


@router.post("/sql/nl-to-sql", response_model=AIStructuredResponse)
def nl_to_sql(payload: NlToSqlRequest, user_id: CurrentUserId, service: AIServiceDep) -> AIStructuredResponse:
    return service.nl_to_sql(
        user_id, request=payload.request, database=payload.database, engine=payload.engine
    )


# --- Python ------------------------------------------------------------------


@router.post("/python/review", response_model=AIStructuredResponse)
def review_python(
    payload: ReviewPythonRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.review_python(
        user_id,
        code=payload.code,
        question=payload.question,
        error_type=payload.error_type,
        error_message=payload.error_message,
        traceback_text=payload.traceback_text,
    )


@router.post("/python/nl-to-python", response_model=AIStructuredResponse)
def nl_to_python(
    payload: NlToPythonRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.nl_to_python(user_id, request=payload.request, dataset_slugs=payload.dataset_slugs)


# --- Analysis / Insight / EDA -------------------------------------------------


@router.post("/analysis/review", response_model=AIStructuredResponse)
def review_analysis(
    payload: ReviewAnalysisRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.review_analysis(
        user_id,
        business_question=payload.business_question,
        dataset_slug=payload.dataset_slug,
        code=payload.code,
        findings=payload.findings,
    )


@router.post("/insight/review", response_model=AIStructuredResponse)
def review_insight(
    payload: ReviewInsightRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.review_insight(
        user_id,
        observation=payload.observation,
        evidence=payload.evidence,
        impact=payload.impact,
        recommendation=payload.recommendation,
    )


@router.post("/eda/assist", response_model=AIStructuredResponse)
def eda_assist(
    payload: EdaAssistRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.eda_assist(
        user_id, dataset_id=payload.dataset_id, table_name=payload.table_name, explore=False
    )


@router.post("/eda/explore", response_model=AIStructuredResponse)
def explore_with_ai(
    payload: EdaAssistRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.eda_assist(
        user_id,
        dataset_id=payload.dataset_id,
        table_name=payload.table_name,
        explore=True,
        user_goal=payload.user_goal,
    )


# --- Domain coaches (Statistics/Experimentation/Product/Business/DataModeling/dbt) --


@router.post("/coach/domain", response_model=AIStructuredResponse)
def domain_coach(
    payload: DomainCoachRequest, user_id: CurrentUserId, service: AIServiceDep
) -> AIStructuredResponse:
    return service.domain_coach(
        user_id, domain=payload.domain, question=payload.question, result_ref=payload.result_ref
    )


# --- Knowledge search (RAG) ----------------------------------------------------


@router.get("/knowledge/search", response_model=AIKnowledgeAnswerResult)
def search_knowledge(
    q: Annotated[str, Query(min_length=1)], user_id: CurrentUserId, service: AIServiceDep, limit: int = 5
) -> AIKnowledgeAnswerResult:
    return service.search_knowledge(user_id, query=q, limit=limit)


# --- Mistake memory + skill diagnoses (list side) -------------------------------


@router.get("/mistakes", response_model=list[AIMistakeMemorySchema])
def list_mistakes(user_id: CurrentUserId, service: AIServiceDep) -> list[AIMistakeMemorySchema]:
    return service.list_mistakes(user_id)


@router.delete("/mistakes/{mistake_id}", status_code=204)
def delete_mistake(mistake_id: str, user_id: CurrentUserId, service: AIServiceDep) -> None:
    service.delete_mistake(user_id, mistake_id)


@router.get("/skill-diagnoses", response_model=list[AISkillDiagnosisSchema])
def list_skill_diagnoses(
    user_id: CurrentUserId, service: AIServiceDep, skill_slug: str | None = None
) -> list[AISkillDiagnosisSchema]:
    return service.list_skill_diagnoses(user_id, skill_slug=skill_slug)


@router.post("/skill-diagnosis", response_model=AISkillDiagnosisResult)
def diagnose_skill(
    payload: SkillDiagnosisRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AISkillDiagnosisResult:
    return service.diagnose_skill(user_id, exercise_attempt_id=payload.exercise_attempt_id)


# --- Case Coach / Case Interviewer -----------------------------------------------


@router.post("/cases/{attempt_id}/coach", response_model=AIChatResponse)
def case_coach(
    attempt_id: str, payload: CaseCoachRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIChatResponse:
    return service.case_coach(
        user_id,
        attempt_id=attempt_id,
        message=payload.message,
        coaching_mode=payload.coaching_mode,
        conversation_id=payload.conversation_id,
    )


@router.post("/cases/{attempt_id}/interviewer", response_model=AIChatResponse)
def case_interviewer_turn(
    attempt_id: str, payload: CaseInterviewerTurnRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIChatResponse:
    return service.case_interviewer_turn(
        user_id, attempt_id=attempt_id, message=payload.message, conversation_id=payload.conversation_id
    )


# --- Behavioral Interviewer / Interview Debrief -------------------------------------


@router.post("/interviews/behavioral-turn", response_model=AIChatResponse)
def behavioral_interviewer_turn(
    payload: BehavioralInterviewerTurnRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIChatResponse:
    return service.behavioral_interviewer_turn(
        user_id,
        interview_question_attempt_id=payload.interview_question_attempt_id,
        message=payload.message,
        conversation_id=payload.conversation_id,
    )


@router.post("/interviews/{interview_id}/debrief", response_model=AIStructuredResponse)
def interview_debrief(
    interview_id: str, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIStructuredResponse:
    return service.interview_debrief(user_id, interview_id=interview_id)


# --- Communication / Storytelling / Executive Summary --------------------------------


@router.post("/communication/review", response_model=AIStructuredResponse)
def communication_review(
    payload: CommunicationReviewRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIStructuredResponse:
    return service.communication_review(user_id, text=payload.text, audience=payload.audience)


@router.post("/storytelling/review", response_model=AIStructuredResponse)
def storytelling_review(
    payload: StorytellingReviewRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIStructuredResponse:
    return service.storytelling_review(
        user_id, findings_text=payload.findings_text, chart_description=payload.chart_description
    )


@router.post("/communication/exec-summary", response_model=AIExecSummaryResult)
def exec_summary(
    payload: ExecSummaryRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIExecSummaryResult:
    return service.exec_summary(user_id, analysis_text=payload.analysis_text)


# --- Learning Planner explanation ------------------------------------------------------


@router.post("/plan/explain", response_model=AIPlanExplanationResult)
def explain_plan(
    payload: PlanExplanationRequest, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIPlanExplanationResult:
    return service.explain_plan(user_id, plan_id=payload.plan_id)


# --- Project Review -----------------------------------------------------------------------


@router.post("/projects/{project_id}/review", response_model=AIStructuredResponse)
def project_review(
    project_id: str, user_id: CurrentUserId, service: AICoachServiceDep
) -> AIStructuredResponse:
    return service.project_review(user_id, project_id=project_id)
