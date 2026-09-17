from datetime import datetime

from app.schemas.common import ORMSchema


class UserProfile(ORMSchema):
    id: str
    name: str
    # Plain str, not EmailStr: this is a single-user local app (see
    # app.models.user.User) where email is never used for auth/notifications,
    # and the field is left blank by default (see app.db.seed.SEED_USER_EMAIL)
    # rather than populated with a real address.
    email: str
    created_at: datetime
    updated_at: datetime


class UpdateUserProfileRequest(ORMSchema):
    name: str | None = None
