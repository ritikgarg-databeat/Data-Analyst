from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import AdminUser, CurrentUserId
from app.dependencies.services import get_interview_service
from app.schemas.interview import (
    AnswerInterviewQuestionRequest,
    AnswerInterviewQuestionResponse,
    CreateInterviewRequest,
    InterviewReviewResponse,
    InterviewSchema,
    InterviewTemplateAdminListItemSchema,
    InterviewTemplateSchema,
    RetryInterviewRequest,
    UpdateInterviewTemplateAdminRequest,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


# Registered before GET /templates/{slug} so "admin" isn't swallowed by the slug route.
@router.get("/templates/admin", response_model=list[InterviewTemplateAdminListItemSchema])
def list_templates_admin(
    admin: AdminUser,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> list[InterviewTemplateAdminListItemSchema]:
    return service.list_templates_admin()


@router.patch("/templates/admin/{template_id}", response_model=InterviewTemplateAdminListItemSchema)
def update_template_admin(
    template_id: str,
    payload: UpdateInterviewTemplateAdminRequest,
    admin: AdminUser,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewTemplateAdminListItemSchema:
    return service.update_template_admin(template_id, payload.is_active)


@router.get("/templates", response_model=list[InterviewTemplateSchema])
def list_templates(
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> list[InterviewTemplateSchema]:
    return service.list_templates()


@router.get("/templates/{slug}", response_model=InterviewTemplateSchema)
def get_template(
    slug: str, service: Annotated[InterviewService, Depends(get_interview_service)]
) -> InterviewTemplateSchema:
    return service.get_template(slug)


@router.get("", response_model=list[InterviewSchema])
def list_interviews(
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> list[InterviewSchema]:
    return [service.to_schema(i, user_id) for i in service.list_interviews(user_id)]


@router.post("", response_model=InterviewSchema, status_code=201)
def create_interview(
    payload: CreateInterviewRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.create_interview(user_id, payload)
    return service.to_schema(interview, user_id)


@router.get("/{interview_id}", response_model=InterviewSchema)
def get_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    return service.to_schema(service.get_interview(user_id, interview_id), user_id)


@router.post("/{interview_id}/start", response_model=InterviewSchema)
def start_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.start_interview(user_id, interview_id)
    return service.to_schema(interview, user_id)


@router.post("/{interview_id}/pause", response_model=InterviewSchema)
def pause_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.pause_interview(user_id, interview_id)
    return service.to_schema(interview, user_id)


@router.post("/{interview_id}/resume", response_model=InterviewSchema)
def resume_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.resume_interview(user_id, interview_id)
    return service.to_schema(interview, user_id)


@router.post("/{interview_id}/answer", response_model=AnswerInterviewQuestionResponse)
def answer_question(
    interview_id: str,
    payload: AnswerInterviewQuestionRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> AnswerInterviewQuestionResponse:
    interview, score, is_auto_graded, explanation, correct_answer = service.answer_question(
        user_id, interview_id, payload
    )
    return AnswerInterviewQuestionResponse(
        interview=service.to_schema(interview, user_id),
        is_auto_graded=is_auto_graded,
        score=score,
        explanation=explanation,
        correct_answer=correct_answer,
    )


@router.post("/{interview_id}/submit", response_model=InterviewSchema)
def submit_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.submit_interview(user_id, interview_id)
    return service.to_schema(interview, user_id)


@router.get("/{interview_id}/review", response_model=InterviewReviewResponse)
def review_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewReviewResponse:
    return service.review_interview(user_id, interview_id)


@router.post("/{interview_id}/retry", response_model=InterviewSchema, status_code=201)
def retry_interview(
    interview_id: str,
    payload: RetryInterviewRequest,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.retry_interview(user_id, interview_id, payload)
    return service.to_schema(interview, user_id)


@router.post("/{interview_id}/abandon", response_model=InterviewSchema)
def abandon_interview(
    interview_id: str,
    user_id: CurrentUserId,
    service: Annotated[InterviewService, Depends(get_interview_service)],
) -> InterviewSchema:
    interview = service.abandon_interview(user_id, interview_id)
    return service.to_schema(interview, user_id)
