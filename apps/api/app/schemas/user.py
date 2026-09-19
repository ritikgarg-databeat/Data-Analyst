from datetime import datetime

from app.models.enums import AccountStatus, UserRole
from app.schemas.common import ORMSchema


class UserProfile(ORMSchema):
    id: str
    name: str
    email: str
    role: UserRole
    status: AccountStatus
    must_change_password: bool
    created_at: datetime
    updated_at: datetime


class UpdateUserProfileRequest(ORMSchema):
    name: str | None = None
