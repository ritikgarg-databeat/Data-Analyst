from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_assessment_service
from app.schemas.assessment import StartAssessmentResponse, SubmitAssessmentRequest, SubmitAssessmentResponse
from app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("/{slug}/attempts", response_model=StartAssessmentResponse, status_code=201)
def start_assessment_attempt(
    slug: str, user_id: CurrentUserId, service: Annotated[AssessmentService, Depends(get_assessment_service)]
) -> StartAssessmentResponse:
    return service.start_attempt(user_id, slug)


@router.post("/{slug}/attempts/{attempt_id}/submit", response_model=SubmitAssessmentResponse)
def submit_assessment_attempt(
    slug: str,
    attempt_id: str,
    payload: SubmitAssessmentRequest,
    user_id: CurrentUserId,
    service: Annotated[AssessmentService, Depends(get_assessment_service)],
) -> SubmitAssessmentResponse:
    return service.submit_attempt(user_id, slug, attempt_id, payload)
