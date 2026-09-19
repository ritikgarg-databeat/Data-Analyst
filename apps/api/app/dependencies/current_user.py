import secrets
from datetime import UTC
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ForbiddenError
from app.core.security import decode_token, utc_now
from app.dependencies.db import get_db
from app.models.auth import AuthSession
from app.models.enums import AccountStatus, UserRole
from app.models.user import User

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def check_trusted_origin(request: Request) -> None:
    """Reject browser mutations originating outside the configured local UI."""
    origin = request.headers.get("origin")
    trusted = get_settings().auth_trusted_origin
    if origin and origin.rstrip("/") != trusted.rstrip("/"):
        raise ForbiddenError("The request origin is not trusted.")


def _check_csrf(request: Request) -> None:
    if request.method in SAFE_METHODS:
        return
    check_trusted_origin(request)
    cookie = request.cookies.get("dal_csrf_token")
    header = request.headers.get("X-CSRF-Token")
    if not cookie or not header or not secrets.compare_digest(cookie, header):
        raise ForbiddenError("The CSRF token is missing or invalid.")


def get_authenticated_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get("dal_access_token")
    if not token:
        raise AuthenticationError("Authentication is required.")
    claims = decode_token(token, "access")
    session = db.get(AuthSession, claims["sid"])
    user = db.get(User, claims["sub"])
    session_expires_at = session.expires_at if session else None
    if session_expires_at is not None and session_expires_at.tzinfo is None:
        session_expires_at = session_expires_at.replace(tzinfo=UTC)
    if (
        not session
        or session.user_id != claims["sub"]
        or session.revoked_at
        or session_expires_at is None
        or session_expires_at <= utc_now()
        or not user
    ):
        raise AuthenticationError("Authentication is required.")
    if user.status != AccountStatus.ACTIVE:
        raise ForbiddenError("This account is suspended.")
    _check_csrf(request)
    return user


def get_current_user(request: Request, user: Annotated[User, Depends(get_authenticated_user)]) -> User:
    allowed_while_forced = {
        "/api/v1/users/me",
        "/api/v1/auth/change-password",
        "/api/v1/auth/logout",
        "/api/v1/auth/logout-all",
    }
    if user.must_change_password and request.url.path not in allowed_while_forced:
        raise ForbiddenError(
            "You must change your temporary password before using the application.",
            details={"code": "password_change_required"},
        )
    return user


def get_admin_user(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise ForbiddenError("Administrator access is required.")
    return user


def get_current_user_id(user: Annotated[User, Depends(get_current_user)]) -> str:
    return user.id


AuthenticatedUser = Annotated[User, Depends(get_authenticated_user)]
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(get_admin_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
