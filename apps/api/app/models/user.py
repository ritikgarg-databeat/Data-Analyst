from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The local application user.

    This is a single-user local application, so there is no auth/session
    machinery here — the app operates against one seeded user row. The model
    is still shaped like a normal `users` table (distinct id, email, audit
    timestamps) so multi-user support can be layered on later without a
    schema rewrite.
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
