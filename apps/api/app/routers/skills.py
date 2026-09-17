from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_skill_service
from app.schemas.skill import CreateSkillRequest, Skill, UpdateSkillRequest, UserSkill
from app.services.skill_service import SkillService

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=list[Skill])
def list_skills(service: Annotated[SkillService, Depends(get_skill_service)]) -> list[Skill]:
    return service.list_skills()


@router.post("", response_model=Skill, status_code=201)
def create_skill(
    payload: CreateSkillRequest, service: Annotated[SkillService, Depends(get_skill_service)]
) -> Skill:
    return service.create(payload)


@router.get("/mastery", response_model=list[UserSkill])
def list_skill_mastery(
    user_id: CurrentUserId, service: Annotated[SkillService, Depends(get_skill_service)]
) -> list[UserSkill]:
    return service.list_user_skills(user_id)


@router.get("/{slug}", response_model=Skill)
def get_skill(slug: str, service: Annotated[SkillService, Depends(get_skill_service)]) -> Skill:
    return service.get_by_slug(slug)


@router.patch("/{skill_id}", response_model=Skill)
def update_skill(
    skill_id: str, payload: UpdateSkillRequest, service: Annotated[SkillService, Depends(get_skill_service)]
) -> Skill:
    return service.update(skill_id, payload)
