from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_progress_service
from app.schemas.progress import LessonProgress, ProgressSummary, UpsertLessonProgressRequest
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/summary", response_model=ProgressSummary)
def get_progress_summary(
    user_id: CurrentUserId, service: Annotated[ProgressService, Depends(get_progress_service)]
) -> ProgressSummary:
    return service.get_summary(user_id)


@router.get("/lessons", response_model=list[LessonProgress])
def list_lesson_progress(
    user_id: CurrentUserId, service: Annotated[ProgressService, Depends(get_progress_service)]
) -> list[LessonProgress]:
    return service.list_lesson_progress(user_id)


@router.post("/lessons/{lesson_id}", response_model=LessonProgress)
def upsert_lesson_progress(
    lesson_id: str,
    payload: UpsertLessonProgressRequest,
    user_id: CurrentUserId,
    service: Annotated[ProgressService, Depends(get_progress_service)],
) -> LessonProgress:
    return service.upsert_lesson_progress(user_id, lesson_id, payload)
