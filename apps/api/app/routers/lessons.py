from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_lesson_service, get_progress_service
from app.schemas.content import LessonContentResponse
from app.schemas.lesson import Lesson, UpdateLessonAdminRequest
from app.schemas.progress import LessonProgress, UpdateLessonPositionRequest
from app.services.lesson_service import LessonService
from app.services.progress_service import ProgressService

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/{slug}", response_model=Lesson)
def get_lesson(slug: str, service: Annotated[LessonService, Depends(get_lesson_service)]) -> Lesson:
    return service.get_by_slug(slug)


@router.get("/{slug}/content", response_model=LessonContentResponse)
def get_lesson_content(
    slug: str, user_id: CurrentUserId, service: Annotated[LessonService, Depends(get_lesson_service)]
) -> LessonContentResponse:
    return service.get_content(slug, user_id)


@router.patch("/{lesson_id}", response_model=Lesson)
def update_lesson_admin(
    lesson_id: str,
    payload: UpdateLessonAdminRequest,
    service: Annotated[LessonService, Depends(get_lesson_service)],
) -> Lesson:
    return service.update_admin(lesson_id, payload)


@router.post("/{slug}/position", response_model=LessonProgress)
def update_lesson_position(
    slug: str,
    payload: UpdateLessonPositionRequest,
    user_id: CurrentUserId,
    lesson_service: Annotated[LessonService, Depends(get_lesson_service)],
    progress_service: Annotated[ProgressService, Depends(get_progress_service)],
) -> LessonProgress:
    lesson = lesson_service.get_model_by_slug(slug)
    return progress_service.update_position(user_id, lesson.id, payload)
