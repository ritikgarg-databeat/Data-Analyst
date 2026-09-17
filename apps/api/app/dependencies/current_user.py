from typing import Annotated

from fastapi import Depends

from app.dependencies.services import get_user_service
from app.services.user_service import UserService


def get_current_user_id(user_service: Annotated[UserService, Depends(get_user_service)]) -> str:
    """Resolves the single local user's id (see app.models.user.User) for use in path/query-free routes."""
    return user_service.get_current_user().id


CurrentUserId = Annotated[str, Depends(get_current_user_id)]
