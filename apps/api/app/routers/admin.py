from fastapi import APIRouter, Query, Response
from fastapi.responses import FileResponse

from app.dependencies.current_user import AdminUser
from app.dependencies.services import DbSession
from app.models.auth import AdminAuditLog
from app.models.enums import AccountStatus, UserRole
from app.schemas.admin import (
    AdminAIUpdate,
    AdminDeleteRequest,
    AdminPasswordConfirmation,
    AdminProfileUpdate,
    AdminRoleUpdate,
    AdminUserDetail,
    AdminUserSummary,
    TemporaryPasswordResponse,
)
from app.schemas.auth import MessageResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["administration"])


@router.get("/dashboard")
def dashboard(admin: AdminUser, db: DbSession) -> dict:
    return AdminService(db, admin).dashboard()


@router.get("/users")
def list_users(
    admin: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: str | None = None,
    role: UserRole | None = None,
    status: AccountStatus | None = None,
    ai_enabled: bool | None = None,
) -> dict:
    return AdminService(db, admin).list_users(page, page_size, search, role, status, ai_enabled)


@router.get("/users/{user_id}", response_model=AdminUserDetail)
def user_detail(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserDetail:
    service = AdminService(db, admin)
    return AdminUserDetail.model_validate(service.user_detail(service._user(user_id)))


@router.get("/users/{user_id}/data/{section}")
def user_data(
    user_id: str,
    section: str,
    admin: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
) -> dict:
    return AdminService(db, admin).user_data(user_id, section, page, page_size)


@router.get("/users/{user_id}/datasets/{dataset_id}/download")
def download_private_dataset(user_id: str, dataset_id: str, admin: AdminUser, db: DbSession) -> FileResponse:
    path, filename = AdminService(db, admin).private_dataset_path(user_id, dataset_id)
    return FileResponse(path, filename=filename)


@router.patch("/users/{user_id}", response_model=AdminUserSummary)
def update_user(
    user_id: str, payload: AdminProfileUpdate, admin: AdminUser, db: DbSession
) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.update_profile(
        user_id, payload.name, str(payload.email) if payload.email else None, payload.current_password
    )
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.post("/users/{user_id}/suspend", response_model=AdminUserSummary)
def suspend(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.set_status(user_id, AccountStatus.SUSPENDED)
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.post("/users/{user_id}/reactivate", response_model=AdminUserSummary)
def reactivate(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.set_status(user_id, AccountStatus.ACTIVE)
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.post("/users/{user_id}/unlock", response_model=AdminUserSummary)
def unlock(user_id: str, admin: AdminUser, db: DbSession) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.unlock(user_id)
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.post("/users/{user_id}/revoke-sessions", response_model=MessageResponse)
def revoke_sessions(user_id: str, admin: AdminUser, db: DbSession) -> MessageResponse:
    AdminService(db, admin).revoke_sessions(user_id)
    return MessageResponse(message="All user sessions were revoked.")


@router.post("/users/{user_id}/reset-password", response_model=TemporaryPasswordResponse)
def reset_password(
    user_id: str, payload: AdminPasswordConfirmation, response: Response, admin: AdminUser, db: DbSession
) -> TemporaryPasswordResponse:
    temporary, expires = AdminService(db, admin).reset_password(user_id, payload.current_password)
    response.headers["Cache-Control"] = "no-store"
    return TemporaryPasswordResponse(temporary_password=temporary, expires_at=expires)


@router.put("/users/{user_id}/ai", response_model=AdminUserSummary)
def set_ai(user_id: str, payload: AdminAIUpdate, admin: AdminUser, db: DbSession) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.set_ai(user_id, payload.enabled, payload.daily_quota)
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.put("/users/{user_id}/role", response_model=AdminUserSummary)
def set_role(user_id: str, payload: AdminRoleUpdate, admin: AdminUser, db: DbSession) -> AdminUserSummary:
    service = AdminService(db, admin)
    user = service.set_role(user_id, payload.role, payload.current_password)
    return AdminUserSummary.model_validate(service.user_summary(user))


@router.delete("/users/{user_id}", response_model=MessageResponse)
def delete_user(
    user_id: str, payload: AdminDeleteRequest, admin: AdminUser, db: DbSession
) -> MessageResponse:
    AdminService(db, admin).delete_user(user_id, str(payload.confirmation_email), payload.current_password)
    return MessageResponse(message="The user and private data were permanently deleted.")


@router.get("/audit")
def audit(
    admin: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    action: str | None = None,
) -> dict:
    from sqlalchemy import func, select

    stmt = select(AdminAuditLog)
    if action:
        stmt = stmt.where(AdminAuditLog.action.ilike(f"%{action}%"))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(AdminAuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    items = [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "target_user_id": row.target_user_id,
            "action": row.action,
            "details": row.details,
            "created_at": row.created_at,
        }
        for row in rows
    ]
    return {"items": items, "page": page, "page_size": page_size, "total": total}


@router.get("/content")
def content_summary(admin: AdminUser, db: DbSession) -> dict:
    from sqlalchemy import func, select

    from app.models.case import Case
    from app.models.domain import Domain
    from app.models.exercise import Exercise
    from app.models.interview import InterviewQuestion
    from app.models.lesson import Lesson
    from app.models.module import Module
    from app.models.project import ProjectTemplate

    models = (Domain, Module, Lesson, Exercise, Case, ProjectTemplate, InterviewQuestion)
    return {model.__tablename__: db.scalar(select(func.count()).select_from(model)) or 0 for model in models}
