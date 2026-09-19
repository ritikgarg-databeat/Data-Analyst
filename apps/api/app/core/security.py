import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings
from app.core.errors import AuthenticationError

password_hasher = PasswordHash.recommended()
# A real Argon2id hash used whenever an email is unknown, keeping the expensive
# password verification path indistinguishable from a known account.
DUMMY_PASSWORD_HASH = password_hasher.hash("dummy-password-that-is-never-valid")


def utc_now() -> datetime:
    return datetime.now(UTC)


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_password(password: str, email: str) -> None:
    if not 12 <= len(password) <= 128:
        raise ValueError("Password must be between 12 and 128 characters.")
    if password.casefold() == normalize_email(email).casefold():
        raise ValueError("Password cannot be the same as the email address.")


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password, password_hash)
    except Exception:
        return False


def opaque_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def _encode(claims: dict[str, Any]) -> str:
    return jwt.encode(claims, get_settings().auth_jwt_secret, algorithm="HS256")


def create_access_token(user_id: str, session_id: str) -> str:
    now = utc_now()
    return _encode(
        {
            "sub": user_id,
            "sid": session_id,
            "typ": "access",
            "iat": now,
            "exp": now + timedelta(minutes=get_settings().auth_access_token_minutes),
        }
    )


def create_refresh_token(user_id: str, session_id: str) -> str:
    now = utc_now()
    return _encode(
        {
            "sub": user_id,
            "sid": session_id,
            "jti": secrets.token_urlsafe(32),
            "typ": "refresh",
            "iat": now,
            "exp": now + timedelta(days=get_settings().auth_refresh_token_days),
        }
    )


def decode_token(token: str, token_type: str) -> dict[str, Any]:
    try:
        claims = jwt.decode(token, get_settings().auth_jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthenticationError("Authentication is required.") from exc
    if claims.get("typ") != token_type or not claims.get("sub") or not claims.get("sid"):
        raise AuthenticationError("Authentication is required.")
    return claims
