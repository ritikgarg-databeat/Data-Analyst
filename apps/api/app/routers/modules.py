from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import AdminUser, CurrentUserId
from app.dependencies.services import get_assessment_service, get_lesson_service, get_module_service
from app.schemas.assessment import Assessment
from app.schemas.lesson import Lesson
from app.schemas.module import CreateModuleRequest, Module, UpdateModuleRequest
from app.services.assessment_service import AssessmentService
from app.services.lesson_service import LessonService
from app.services.module_service import ModuleService

router = APIRouter(prefix="/modules", tags=["modules"])


@router.post("", response_model=Module, status_code=201)
def create_module(
    payload: CreateModuleRequest,
    admin: AdminUser,
    service: Annotated[ModuleService, Depends(get_module_service)],
) -> Module:
    return service.create(payload)


@router.get("/{slug}", response_model=Module)
def get_module(
    slug: str, user_id: CurrentUserId, service: Annotated[ModuleService, Depends(get_module_service)]
) -> Module:
    return service.get_by_slug(slug, user_id)


@router.patch("/{module_id}", response_model=Module)
def update_module(
    module_id: str,
    payload: UpdateModuleRequest,
    admin: AdminUser,
    service: Annotated[ModuleService, Depends(get_module_service)],
) -> Module:
    return service.update(module_id, payload)


@router.get("/{slug}/lessons", response_model=list[Lesson])
def list_module_lessons(
    slug: str, service: Annotated[LessonService, Depends(get_lesson_service)]
) -> list[Lesson]:
    return service.list_by_module_slug(slug)


@router.get("/{slug}/assessment", response_model=Assessment)
def get_module_assessment(
    slug: str, service: Annotated[AssessmentService, Depends(get_assessment_service)]
) -> Assessment:
    return service.get_by_module_slug(slug)
