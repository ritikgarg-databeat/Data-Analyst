from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_interview_readiness_service
from app.schemas.interview import (
    InterviewPlanSchema,
    ReadinessResponse,
    ReadinessSnapshotSchema,
    WeaknessFindingSchema,
)
from app.services.interview_readiness_service import InterviewReadinessService

router = APIRouter(prefix="/interview", tags=["interview-readiness"])


@router.get("/readiness", response_model=ReadinessResponse)
def get_readiness(
    user_id: CurrentUserId,
    service: Annotated[InterviewReadinessService, Depends(get_interview_readiness_service)],
) -> ReadinessResponse:
    return service.get_readiness(user_id)


@router.get("/readiness/history", response_model=list[ReadinessSnapshotSchema])
def get_readiness_history(
    user_id: CurrentUserId,
    service: Annotated[InterviewReadinessService, Depends(get_interview_readiness_service)],
) -> list[ReadinessSnapshotSchema]:
    return service.get_history(user_id)


@router.get("/recommendations/weaknesses", response_model=list[WeaknessFindingSchema])
def get_weaknesses(
    user_id: CurrentUserId,
    service: Annotated[InterviewReadinessService, Depends(get_interview_readiness_service)],
) -> list[WeaknessFindingSchema]:
    return service.get_weaknesses(user_id)


@router.get("/recommendations/plan", response_model=InterviewPlanSchema | None)
def get_latest_plan(
    user_id: CurrentUserId,
    service: Annotated[InterviewReadinessService, Depends(get_interview_readiness_service)],
) -> InterviewPlanSchema | None:
    return service.get_latest_plan(user_id)


@router.post("/recommendations/plan", response_model=InterviewPlanSchema, status_code=201)
def generate_plan(
    user_id: CurrentUserId,
    service: Annotated[InterviewReadinessService, Depends(get_interview_readiness_service)],
) -> InterviewPlanSchema:
    return service.generate_and_persist_plan(user_id)
