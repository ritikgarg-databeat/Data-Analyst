from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UpdateUserProfileRequest


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def get_current_user(self) -> User:
        """Return the legacy/first user for local maintenance code.

        Request handlers must use the authenticated ``CurrentUser`` dependency;
        this helper remains only for older offline services and migration tests.
        """
        user = self.repo.get_first()
        if user is None:
            raise AppError("No user account exists yet.")
        return user

    def update_current_user(self, user: User, payload: UpdateUserProfileRequest) -> User:
        if payload.name is not None:
            name = payload.name.strip()
            if not name:
                raise AppError("Name is required.")
            user.name = name
        self.db.commit()
        self.db.refresh(user)
        return user
