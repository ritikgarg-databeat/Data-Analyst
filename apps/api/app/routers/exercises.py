from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import AdminUser, CurrentUserId
from app.dependencies.services import get_exercise_service
from app.schemas.exercise import (
    Exercise,
    ExerciseContent,
    RevealHintResponse,
    RevealSolutionResponse,
    SubmitExerciseAttemptRequest,
    SubmitExerciseAttemptResponse,
    UpdateExerciseAdminRequest,
)
from app.services.exercise_service import ExerciseService

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("", response_model=list[Exercise])
def list_exercises(service: Annotated[ExerciseService, Depends(get_exercise_service)]) -> list[Exercise]:
    return service.list_exercises()


@router.get("/{slug}", response_model=Exercise)
def get_exercise(slug: str, service: Annotated[ExerciseService, Depends(get_exercise_service)]) -> Exercise:
    return service.get_by_slug(slug)


@router.get("/{slug}/content", response_model=ExerciseContent)
def get_exercise_content(
    slug: str, user_id: CurrentUserId, service: Annotated[ExerciseService, Depends(get_exercise_service)]
) -> ExerciseContent:
    return service.get_content(slug, user_id)


@router.post("/{slug}/attempts", response_model=SubmitExerciseAttemptResponse)
def submit_exercise_attempt(
    slug: str,
    payload: SubmitExerciseAttemptRequest,
    user_id: CurrentUserId,
    service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> SubmitExerciseAttemptResponse:
    return service.submit_attempt(user_id, slug, payload)


@router.post("/{slug}/hint", response_model=RevealHintResponse)
def reveal_exercise_hint(
    slug: str, user_id: CurrentUserId, service: Annotated[ExerciseService, Depends(get_exercise_service)]
) -> RevealHintResponse:
    return service.reveal_hint(user_id, slug)


@router.post("/{slug}/solution", response_model=RevealSolutionResponse)
def reveal_exercise_solution(
    slug: str, user_id: CurrentUserId, service: Annotated[ExerciseService, Depends(get_exercise_service)]
) -> RevealSolutionResponse:
    return service.reveal_solution(user_id, slug)


@router.patch("/{exercise_id}", response_model=Exercise)
def update_exercise_admin(
    exercise_id: str,
    payload: UpdateExerciseAdminRequest,
    admin: AdminUser,
    service: Annotated[ExerciseService, Depends(get_exercise_service)],
) -> Exercise:
    return service.update_admin(exercise_id, payload)
