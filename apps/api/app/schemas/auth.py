from datetime import datetime

from pydantic import EmailStr, Field, field_validator, model_validator

from app.core.security import normalize_email, validate_password
from app.models.enums import AccountStatus, UserRole
from app.schemas.common import ORMSchema


class PublicUserProfile(ORMSchema):
    id: str
    name: str
    email: str
    role: UserRole
    status: AccountStatus
    must_change_password: bool
    ai_access_enabled: bool = False
    ai_daily_quota: int = 0
    ai_requests_today: int = 0
    created_at: datetime
    updated_at: datetime


class SignupRequest(ORMSchema):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))

    @model_validator(mode="after")
    def valid_password(self) -> "SignupRequest":
        validate_password(self.password, str(self.email))
        return self


class LoginRequest(ORMSchema):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalized_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))


class ChangePasswordRequest(ORMSchema):
    current_password: str
    new_password: str


class ChangeEmailRequest(ORMSchema):
    current_password: str
    new_email: EmailStr

    @field_validator("new_email")
    @classmethod
    def normalized_email(cls, value: EmailStr) -> str:
        return normalize_email(str(value))


class AuthResponse(ORMSchema):
    user: PublicUserProfile


class MessageResponse(ORMSchema):
    message: str
