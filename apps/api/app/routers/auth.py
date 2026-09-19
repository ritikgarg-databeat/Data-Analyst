from fastapi import APIRouter, Request, Response

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ForbiddenError
from app.core.security import decode_token
from app.dependencies.current_user import AuthenticatedUser, check_trusted_origin
from app.dependencies.services import DbSession
from app.schemas.auth import (
    AuthResponse,
    ChangeEmailRequest,
    ChangePasswordRequest,
    LoginRequest,
    MessageResponse,
    PublicUserProfile,
    SignupRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


def _set_auth_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    settings = get_settings()
    response.set_cookie(
        "dal_access_token",
        access,
        httponly=True,
        max_age=settings.auth_access_token_minutes * 60,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "dal_refresh_token",
        refresh,
        httponly=True,
        max_age=settings.auth_refresh_token_days * 86400,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        "dal_csrf_token",
        csrf,
        httponly=False,
        max_age=settings.auth_refresh_token_days * 86400,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in ("dal_access_token", "dal_refresh_token", "dal_csrf_token"):
        response.delete_cookie(name, path="/")


def _response(service: AuthService, user) -> AuthResponse:
    return AuthResponse(user=PublicUserProfile.model_validate(service.profile(user)))


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(payload: SignupRequest, request: Request, response: Response, db: DbSession) -> AuthResponse:
    check_trusted_origin(request)
    service = AuthService(db)
    user = service.signup(payload.name, str(payload.email), payload.password)
    access, refresh, csrf = service.create_session(user, request.headers.get("user-agent"))
    _set_auth_cookies(response, access, refresh, csrf)
    return _response(service, user)


def _login(
    payload: LoginRequest, request: Request, response: Response, db: DbSession, *, admin_only: bool
) -> AuthResponse:
    check_trusted_origin(request)
    service = AuthService(db)
    user = service.authenticate(str(payload.email), payload.password, admin_only=admin_only)
    access, refresh, csrf = service.create_session(user, request.headers.get("user-agent"))
    _set_auth_cookies(response, access, refresh, csrf)
    return _response(service, user)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, request: Request, response: Response, db: DbSession) -> AuthResponse:
    return _login(payload, request, response, db, admin_only=False)


@router.post("/admin/login", response_model=AuthResponse)
def admin_login(payload: LoginRequest, request: Request, response: Response, db: DbSession) -> AuthResponse:
    return _login(payload, request, response, db, admin_only=True)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: DbSession) -> AuthResponse:
    check_trusted_origin(request)
    cookie_csrf = request.cookies.get("dal_csrf_token")
    if not cookie_csrf or cookie_csrf != request.headers.get("X-CSRF-Token"):
        raise ForbiddenError("The CSRF token is missing or invalid.")
    raw_refresh = request.cookies.get("dal_refresh_token")
    if not raw_refresh:
        raise AuthenticationError("A refresh session is required.")
    service = AuthService(db)
    user, access, new_refresh, csrf = service.rotate(raw_refresh)
    _set_auth_cookies(response, access, new_refresh, csrf)
    return _response(service, user)


@router.post("/logout", response_model=MessageResponse)
def logout(request: Request, response: Response, user: AuthenticatedUser, db: DbSession) -> MessageResponse:
    token = request.cookies.get("dal_access_token")
    if token:
        AuthService(db).revoke_session(decode_token(token, "access")["sid"])
    _clear_auth_cookies(response)
    return MessageResponse(message="Logged out.")


@router.post("/logout-all", response_model=MessageResponse)
def logout_all(response: Response, user: AuthenticatedUser, db: DbSession) -> MessageResponse:
    AuthService(db).revoke_all(user.id)
    _clear_auth_cookies(response)
    return MessageResponse(message="All sessions were revoked.")


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest, response: Response, user: AuthenticatedUser, db: DbSession
) -> MessageResponse:
    AuthService(db).change_password(user, payload.current_password, payload.new_password)
    _clear_auth_cookies(response)
    return MessageResponse(message="Password changed. Please sign in again.")


@router.post("/change-email", response_model=MessageResponse)
def change_email(
    payload: ChangeEmailRequest, response: Response, user: AuthenticatedUser, db: DbSession
) -> MessageResponse:
    AuthService(db).change_email(user, payload.current_password, str(payload.new_email))
    _clear_auth_cookies(response)
    return MessageResponse(message="Email changed. Please sign in again.")
