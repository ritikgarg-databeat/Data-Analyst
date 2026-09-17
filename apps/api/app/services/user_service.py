from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UpdateUserProfileRequest


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = UserRepository(db)

    def get_current_user(self) -> User:
        """Returns the single local user.

        This is a single-user local application (see app.models.user.User), so
        "current user" simply means the one seeded row rather than anything
        derived from a request/session/token.
        """
        user = self.repo.get_first()
        if user is None:
            raise NotFoundError(
                "No local user found. Run the seed script to create one.", details={"entity": "User"}
            )
        return user

    def update_current_user(self, payload: UpdateUserProfileRequest) -> User:
        user = self.get_current_user()
        if payload.name is not None:
            user.name = payload.name
        self.db.commit()
        self.db.refresh(user)
        return user
