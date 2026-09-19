from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUser
from app.dependencies.services import DbSession, get_user_service
from app.schemas.auth import PublicUserProfile
from app.schemas.user import UpdateUserProfileRequest, UserProfile
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=PublicUserProfile)
def get_current_user(user: CurrentUser, db: DbSession) -> PublicUserProfile:
    return PublicUserProfile.model_validate(AuthService(db).profile(user))


@router.patch("/me", response_model=UserProfile)
def update_current_user(
    payload: UpdateUserProfileRequest,
    user: CurrentUser,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserProfile:
    return UserProfile.model_validate(service.update_current_user(user, payload))
