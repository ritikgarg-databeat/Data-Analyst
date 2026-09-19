from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core.security import normalize_email
from app.models.enums import AccountStatus, UserRole
from app.schemas.common import ORMSchema


class AdminPasswordConfirmation(ORMSchema):
    current_password: str


class AdminProfileUpdate(ORMSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    current_password: str | None = None

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: EmailStr | None) -> str | None:
        return normalize_email(str(value)) if value is not None else None


class AdminAIUpdate(ORMSchema):
    enabled: bool
    daily_quota: int = Field(ge=1, le=200)


class AdminRoleUpdate(AdminPasswordConfirmation):
    role: UserRole


class AdminDeleteRequest(AdminPasswordConfirmation):
    confirmation_email: EmailStr


class AdminUserSummary(ORMSchema):
    id: str
    name: str
    email: str
    role: UserRole
    status: AccountStatus
    must_change_password: bool
    is_locked: bool
    ai_grant_enabled: bool
    ai_daily_quota: int
    ai_requests_today: int
    created_at: datetime
    last_login_at: datetime | None


class AdminUserDetail(AdminUserSummary):
    failed_login_count: int
    locked_until: datetime | None
    temporary_password_expires_at: datetime | None
    ai_preference_enabled: bool
    effective_ai_access_enabled: bool


class TemporaryPasswordResponse(ORMSchema):
    temporary_password: str
    expires_at: datetime
