import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, AuthenticationError, ConflictError, ForbiddenError, RateLimitError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    hash_password,
    normalize_email,
    opaque_hash,
    utc_now,
    validate_password,
    verify_password,
)
from app.models.ai import AISettings, AIUsageCounter
from app.models.auth import AuthSession
from app.models.enums import AccountStatus, UserRole
from app.models.user import User


def _aware(value):
    if value is not None and value.tzinfo is None:
        return value.replace(tzinfo=utc_now().tzinfo)
    return value


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()

    @staticmethod
    def _validate_password(password: str, email: str) -> None:
        try:
            validate_password(password, email)
        except ValueError as exc:
            raise AppError(str(exc)) from exc

    def signup(self, name: str, email: str, password: str) -> User:
        if not self.settings.auth_signup_enabled:
            raise ForbiddenError("Signup is currently disabled.")
        normalized = normalize_email(email)
        self._validate_password(password, normalized)
        if self.db.scalar(select(User).where(User.email == normalized)):
            raise ConflictError("An account with this email already exists.")
        normalized_name = name.strip()
        if not normalized_name:
            raise AppError("Name is required.")
        user = User(name=normalized_name, email=normalized, password_hash=hash_password(password))
        self.db.add(user)
        self.db.flush()
        self.db.add(
            AISettings(
                user_id=user.id,
                enabled=True,
                admin_access_enabled=False,
                admin_daily_request_limit=self.settings.auth_default_ai_quota,
            )
        )
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError("An account with this email already exists.") from exc
        self.db.refresh(user)
        return user

    def authenticate(self, email: str, password: str, *, admin_only: bool = False) -> User:
        normalized = normalize_email(email)
        user = self.db.scalar(select(User).where(User.email == normalized))
        now = utc_now()
        if user and _aware(user.locked_until) and _aware(user.locked_until) > now:
            raise RateLimitError("Too many login attempts. Try again later.")
        password_ok = verify_password(password, user.password_hash if user else DUMMY_PASSWORD_HASH)
        if not user or not password_ok:
            if user:
                user.failed_login_count += 1
                if user.failed_login_count >= self.settings.auth_lockout_attempts:
                    user.failed_login_count = 0
                    user.locked_until = now + timedelta(minutes=self.settings.auth_lockout_minutes)
                self.db.commit()
            raise AuthenticationError("Invalid email or password.")
        if user.status != AccountStatus.ACTIVE:
            raise ForbiddenError("This account is suspended.")
        if admin_only and user.role != UserRole.ADMIN:
            raise AuthenticationError("Invalid email or password.")
        if user.temporary_password_expires_at and _aware(user.temporary_password_expires_at) < now:
            raise AuthenticationError("The temporary password has expired. Contact an administrator.")
        user.failed_login_count = 0
        user.locked_until = None
        user.last_login_at = now
        self.db.commit()
        self.db.refresh(user)
        return user

    def create_session(self, user: User, user_agent: str | None) -> tuple[str, str, str]:
        session = AuthSession(
            user_id=user.id,
            refresh_token_hash="pending-" + secrets.token_hex(28),
            expires_at=utc_now() + timedelta(days=self.settings.auth_refresh_token_days),
            user_agent=(user_agent or "")[:500] or None,
        )
        self.db.add(session)
        self.db.flush()
        refresh = create_refresh_token(user.id, session.id)
        session.refresh_token_hash = opaque_hash(refresh)
        self.db.commit()
        return create_access_token(user.id, session.id), refresh, secrets.token_urlsafe(32)

    def rotate(self, raw_token: str) -> tuple[User, str, str, str]:
        from app.core.security import decode_token

        claims = decode_token(raw_token, "refresh")
        session = self.db.scalar(select(AuthSession).where(AuthSession.id == claims["sid"]).with_for_update())
        if not session or session.user_id != claims["sub"]:
            raise AuthenticationError("The refresh session is invalid.")
        if session.revoked_at or _aware(session.expires_at) <= utc_now():
            raise AuthenticationError("The refresh session has expired.")
        if not secrets.compare_digest(session.refresh_token_hash, opaque_hash(raw_token)):
            self.revoke_all(session.user_id)
            raise AuthenticationError("Refresh token reuse was detected. All sessions were revoked.")
        user = self.db.get(User, session.user_id)
        if not user or user.status != AccountStatus.ACTIVE:
            session.revoked_at = utc_now()
            self.db.commit()
            raise ForbiddenError("This account is unavailable.")
        refresh = create_refresh_token(user.id, session.id)
        session.refresh_token_hash = opaque_hash(refresh)
        session.last_used_at = utc_now()
        session.expires_at = utc_now() + timedelta(days=self.settings.auth_refresh_token_days)
        self.db.commit()
        return user, create_access_token(user.id, session.id), refresh, secrets.token_urlsafe(32)

    def revoke_session(self, session_id: str) -> None:
        session = self.db.get(AuthSession, session_id)
        if session and not session.revoked_at:
            session.revoked_at = utc_now()
            self.db.commit()

    def revoke_all(self, user_id: str, *, commit: bool = True) -> None:
        self.db.execute(
            update(AuthSession)
            .where(AuthSession.user_id == user_id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=utc_now())
        )
        if commit:
            self.db.commit()

    def change_password(self, user: User, current: str, new: str) -> None:
        if not verify_password(current, user.password_hash):
            raise AuthenticationError("The current password is incorrect.")
        self._validate_password(new, user.email)
        user.password_hash = hash_password(new)
        user.must_change_password = False
        user.temporary_password_expires_at = None
        self.db.flush()
        self.revoke_all(user.id)

    def change_email(self, user: User, current: str, new_email: str) -> None:
        if not verify_password(current, user.password_hash):
            raise AuthenticationError("The current password is incorrect.")
        normalized = normalize_email(new_email)
        self._validate_password(current, normalized)
        if self.db.scalar(select(User).where(User.email == normalized, User.id != user.id)):
            raise ConflictError("An account with this email already exists.")
        user.email = normalized
        self.db.flush()
        self.revoke_all(user.id)

    def profile(self, user: User) -> dict:
        settings = self.db.scalar(select(AISettings).where(AISettings.user_id == user.id))
        today = utc_now().date()
        usage = self.db.scalar(
            select(AIUsageCounter).where(
                AIUsageCounter.user_id == user.id, AIUsageCounter.usage_date == today
            )
        )
        granted = bool(settings and settings.admin_access_enabled)
        preferred = bool(settings and settings.enabled)
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "must_change_password": user.must_change_password,
            "ai_access_enabled": granted and preferred,
            "ai_daily_quota": settings.admin_daily_request_limit if granted and settings else 0,
            "ai_requests_today": usage.request_count if usage else 0,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
