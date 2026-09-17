from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.services import get_user_service
from app.schemas.user import UpdateUserProfileRequest, UserProfile
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_current_user(service: Annotated[UserService, Depends(get_user_service)]) -> UserProfile:
    return UserProfile.model_validate(service.get_current_user())


@router.patch("/me", response_model=UserProfile)
def update_current_user(
    payload: UpdateUserProfileRequest, service: Annotated[UserService, Depends(get_user_service)]
) -> UserProfile:
    return UserProfile.model_validate(service.update_current_user(payload))
