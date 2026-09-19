import secrets
import shutil
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError, AuthenticationError, ConflictError, ForbiddenError, NotFoundError
from app.core.middleware import get_current_request_id
from app.core.security import hash_password, normalize_email, utc_now, validate_password, verify_password
from app.models.ai import AISettings, AIUsageCounter
from app.models.auth import AdminAuditLog
from app.models.dataset import Dataset
from app.models.enums import AccountStatus, UserRole
from app.models.python_lab import PythonRuntime
from app.models.sql_lab import SqlTable
from app.models.user import User
from app.services.auth_service import AuthService, _aware

REPO_ROOT = Path(__file__).resolve().parents[4]


class AdminService:
    def __init__(self, db: Session, actor: User) -> None:
        self.db = db
        self.actor = actor

    def _user(self, user_id: str) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found.")
        return user

    def _confirm(self, password: str | None) -> None:
        if not password or not verify_password(password, self.actor.password_hash):
            raise AuthenticationError("The administrator password is incorrect.")

    def _audit(self, action: str, target: User | None, details: dict | None = None) -> None:
        self.db.add(
            AdminAuditLog(
                actor_user_id=self.actor.id,
                target_user_id=target.id if target else None,
                action=action,
                details=details,
                request_id=get_current_request_id(),
            )
        )

    def _settings(self, user: User) -> AISettings:
        settings = self.db.scalar(select(AISettings).where(AISettings.user_id == user.id))
        if not settings:
            settings = AISettings(
                user_id=user.id,
                enabled=True,
                admin_access_enabled=False,
                admin_daily_request_limit=get_settings().auth_default_ai_quota,
            )
            self.db.add(settings)
            self.db.flush()
        return settings

    def user_summary(self, user: User) -> dict:
        settings = self._settings(user)
        usage = self.db.scalar(
            select(AIUsageCounter).where(
                AIUsageCounter.user_id == user.id,
                AIUsageCounter.usage_date == utc_now().date(),
            )
        )
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status,
            "must_change_password": user.must_change_password,
            "is_locked": bool(_aware(user.locked_until) and _aware(user.locked_until) > utc_now()),
            "ai_grant_enabled": settings.admin_access_enabled,
            "ai_daily_quota": settings.admin_daily_request_limit,
            "ai_requests_today": usage.request_count if usage else 0,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
        }

    def user_detail(self, user: User) -> dict:
        result = self.user_summary(user)
        settings = self._settings(user)
        result.update(
            {
                "failed_login_count": user.failed_login_count,
                "locked_until": user.locked_until,
                "temporary_password_expires_at": user.temporary_password_expires_at,
                "ai_preference_enabled": settings.enabled,
                "effective_ai_access_enabled": settings.admin_access_enabled and settings.enabled,
            }
        )
        return result

    def dashboard(self) -> dict:
        total = self.db.scalar(select(func.count()).select_from(User)) or 0
        active = (
            self.db.scalar(select(func.count()).select_from(User).where(User.status == AccountStatus.ACTIVE))
            or 0
        )
        suspended = total - active
        locked = (
            self.db.scalar(select(func.count()).select_from(User).where(User.locked_until > utc_now())) or 0
        )
        signups_today = (
            self.db.scalar(
                select(func.count()).select_from(User).where(func.date(User.created_at) == utc_now().date())
            )
            or 0
        )
        ai_today = (
            self.db.scalar(
                select(func.coalesce(func.sum(AIUsageCounter.request_count), 0)).where(
                    AIUsageCounter.usage_date == utc_now().date()
                )
            )
            or 0
        )
        return {
            "users": total,
            "active_users": active,
            "suspended_users": suspended,
            "locked_users": locked,
            "signups_today": signups_today,
            "ai_requests_today": ai_today,
        }

    def list_users(
        self,
        page: int,
        page_size: int,
        search: str | None,
        role: UserRole | None,
        status: AccountStatus | None,
        ai_enabled: bool | None,
    ) -> dict:
        stmt = select(User)
        if search:
            term = f"%{search.strip().lower()}%"
            stmt = stmt.where(or_(func.lower(User.email).like(term), func.lower(User.name).like(term)))
        if role:
            stmt = stmt.where(User.role == role)
        if status:
            stmt = stmt.where(User.status == status)
        if ai_enabled is not None:
            stmt = stmt.join(AISettings).where(AISettings.admin_access_enabled == ai_enabled)
        total = self.db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        users = self.db.scalars(
            stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return {
            "items": [self.user_summary(user) for user in users],
            "page": page,
            "page_size": page_size,
            "total": total,
        }

    def user_data(self, user_id: str, section: str, page: int, page_size: int) -> dict:
        """Read-only administrative view. Child resources are reached through
        user-owned roots, never by accepting an unverified child owner id."""
        from app.models.ai import AIAuditLog, AIConversation, AIMessage, AIMistakeMemory, AISkillDiagnosis
        from app.models.assessment import AssessmentAnswer, AssessmentAttempt
        from app.models.career import (
            BehavioralStory,
            CareerAssessment,
            CareerGoal,
            CareerMilestone,
            CareerNote,
            CareerProfile,
            JDAnalysis,
            JDRequirement,
            JobDescription,
            JobPreparationWorkspace,
            Portfolio,
            PortfolioItem,
            Resume,
            ResumeEvidence,
            ResumeReview,
            ResumeVersion,
            SkillGap,
            TargetRole,
            UserAchievement,
        )
        from app.models.chart import Chart
        from app.models.data_quality import DataQualityRule, DataQualityRun
        from app.models.dataset import DatasetNote, DatasetTable
        from app.models.dbt import DbtRun
        from app.models.eda import EdaFinding, EdaWorkspace
        from app.models.exercise_attempt import ExerciseAttempt
        from app.models.interview import (
            Interview,
            InterviewBookmark,
            InterviewNote,
            InterviewPlan,
            InterviewQuestionAttempt,
            InterviewSection,
            ReadinessSnapshot,
        )
        from app.models.lesson_progress import LessonProgress
        from app.models.project import Project, ProjectArtifact, ProjectDataset, ProjectMilestone
        from app.models.python_lab import PythonCell, PythonExecution, PythonRuntime, PythonWorkspace
        from app.models.sql_lab import SqlQueryHistory, SqlSavedQuery, SqlWorkspace
        from app.models.user_skill import UserSkill

        self._user(user_id)
        groups = {
            "learning": [LessonProgress, ExerciseAttempt, AssessmentAttempt, UserSkill],
            "labs": [
                SqlQueryHistory,
                SqlSavedQuery,
                SqlWorkspace,
                PythonExecution,
                PythonRuntime,
                PythonWorkspace,
                DbtRun,
                EdaWorkspace,
                DataQualityRule,
            ],
            "projects": [Project, Chart],
            "career": [
                CareerProfile,
                CareerGoal,
                CareerMilestone,
                CareerAssessment,
                CareerNote,
                TargetRole,
                JobDescription,
                JobPreparationWorkspace,
                Resume,
                Portfolio,
                BehavioralStory,
                SkillGap,
                UserAchievement,
            ],
            "interviews": [
                Interview,
                InterviewBookmark,
                InterviewNote,
                InterviewPlan,
                ReadinessSnapshot,
            ],
            "ai": [AIConversation, AIAuditLog, AIMistakeMemory, AISkillDiagnosis, AIUsageCounter],
            "datasets": [Dataset, DatasetNote],
        }
        models = groups.get(section)
        if models is None:
            raise NotFoundError("Administrative data section not found.")
        rows: list[dict] = []

        def append_rows(model, records) -> None:
            for row in records:
                values = {}
                for column in row.__table__.columns:
                    if column.name in {"password_hash", "refresh_token_hash"}:
                        continue
                    value = getattr(row, column.name)
                    if hasattr(value, "value"):
                        value = value.value
                    values[column.name] = value
                rows.append({"type": model.__tablename__, "data": values})

        for model in models:
            owner_column = Dataset.owner_user_id if model is Dataset else getattr(model, "user_id", None)
            if owner_column is None:
                continue
            append_rows(model, self.db.scalars(select(model).where(owner_column == user_id)).all())

        child_queries: dict[str, list[tuple[Any, Any]]] = {
            "learning": [
                (
                    AssessmentAnswer,
                    select(AssessmentAnswer)
                    .join(AssessmentAttempt)
                    .where(AssessmentAttempt.user_id == user_id),
                ),
            ],
            "labs": [
                (
                    PythonCell,
                    select(PythonCell).join(PythonWorkspace).where(PythonWorkspace.user_id == user_id),
                ),
                (
                    EdaFinding,
                    select(EdaFinding).join(EdaWorkspace).where(EdaWorkspace.user_id == user_id),
                ),
                (
                    DataQualityRun,
                    select(DataQualityRun).join(DataQualityRule).where(DataQualityRule.user_id == user_id),
                ),
            ],
            "projects": [
                (
                    ProjectMilestone,
                    select(ProjectMilestone).join(Project).where(Project.user_id == user_id),
                ),
                (
                    ProjectArtifact,
                    select(ProjectArtifact).join(Project).where(Project.user_id == user_id),
                ),
                (
                    ProjectDataset,
                    select(ProjectDataset).join(Project).where(Project.user_id == user_id),
                ),
            ],
            "datasets": [
                (
                    DatasetTable,
                    select(DatasetTable).join(Dataset).where(Dataset.owner_user_id == user_id),
                ),
                (
                    SqlTable,
                    select(SqlTable).join(Dataset).where(Dataset.owner_user_id == user_id),
                ),
            ],
            "career": [
                (
                    JDRequirement,
                    select(JDRequirement).join(JobDescription).where(JobDescription.user_id == user_id),
                ),
                (
                    JDAnalysis,
                    select(JDAnalysis).join(JobDescription).where(JobDescription.user_id == user_id),
                ),
                (
                    ResumeVersion,
                    select(ResumeVersion).join(Resume).where(Resume.user_id == user_id),
                ),
                (
                    ResumeEvidence,
                    select(ResumeEvidence).join(ResumeVersion).join(Resume).where(Resume.user_id == user_id),
                ),
                (
                    ResumeReview,
                    select(ResumeReview).join(ResumeVersion).join(Resume).where(Resume.user_id == user_id),
                ),
                (
                    PortfolioItem,
                    select(PortfolioItem).join(Portfolio).where(Portfolio.user_id == user_id),
                ),
            ],
            "interviews": [
                (
                    InterviewSection,
                    select(InterviewSection).join(Interview).where(Interview.user_id == user_id),
                ),
                (
                    InterviewQuestionAttempt,
                    select(InterviewQuestionAttempt).join(Interview).where(Interview.user_id == user_id),
                ),
            ],
            "ai": [
                (
                    AIMessage,
                    select(AIMessage).join(AIConversation).where(AIConversation.user_id == user_id),
                ),
            ],
        }
        for model, stmt in child_queries.get(section, []):
            append_rows(model, self.db.scalars(stmt).all())
        rows.sort(key=lambda item: str(item["data"].get("created_at", "")), reverse=True)
        start = (page - 1) * page_size
        return {
            "items": rows[start : start + page_size],
            "page": page,
            "page_size": page_size,
            "total": len(rows),
        }

    def private_dataset_path(self, user_id: str, dataset_id: str) -> tuple[Path, str]:
        user = self._user(user_id)
        dataset = self.db.scalar(
            select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_user_id == user.id)
        )
        if not dataset:
            raise NotFoundError("Private dataset file not found.")
        file_path = dataset.file_path
        if not file_path and dataset.tables:
            file_path = dataset.tables[0].file_path
        if not file_path:
            table = self.db.scalar(
                select(SqlTable).where(SqlTable.dataset_id == dataset.id).order_by(SqlTable.display_order)
            )
            file_path = table.file_path if table else None
        if not file_path:
            raise NotFoundError("Private dataset file not found.")
        private_root = (REPO_ROOT / "data" / "users" / user.id).resolve()
        path = (REPO_ROOT / file_path).resolve()
        if private_root not in path.parents or not path.is_file():
            raise ForbiddenError("The private dataset path is invalid.")
        self._audit("dataset.private_file_downloaded", user, {"dataset_id": dataset.id})
        self.db.commit()
        return path, path.name

    def update_profile(
        self, user_id: str, name: str | None, email: str | None, current_password: str | None
    ) -> User:
        user = self._user(user_id)
        changes = {}
        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise AppError("Name is required.")
            user.name = normalized_name
            changes["name"] = True
        if email is not None:
            self._confirm(current_password)
            normalized = normalize_email(email)
            if self.db.scalar(select(User).where(User.email == normalized, User.id != user.id)):
                raise ConflictError("An account with this email already exists.")
            user.email = normalized
            AuthService(self.db).revoke_all(user.id, commit=False)
            changes["email"] = True
        self._audit("user.profile_updated", user, changes)
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_status(self, user_id: str, status: AccountStatus) -> User:
        user = self._user(user_id)
        if user.id == self.actor.id and status == AccountStatus.SUSPENDED:
            raise ForbiddenError("Administrators cannot suspend themselves.")
        user.status = status
        if status == AccountStatus.SUSPENDED:
            AuthService(self.db).revoke_all(user.id, commit=False)
        self._audit(f"user.{status.value.lower()}", user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def unlock(self, user_id: str) -> User:
        user = self._user(user_id)
        user.failed_login_count = 0
        user.locked_until = None
        self._audit("user.unlocked", user)
        self.db.commit()
        return user

    def revoke_sessions(self, user_id: str) -> None:
        user = self._user(user_id)
        AuthService(self.db).revoke_all(user.id, commit=False)
        self._audit("user.sessions_revoked", user)
        self.db.commit()

    def reset_password(self, user_id: str, admin_password: str) -> tuple[str, datetime]:
        self._confirm(admin_password)
        user = self._user(user_id)
        temporary = secrets.token_urlsafe(18)
        validate_password(temporary, user.email)
        expires = utc_now() + timedelta(hours=24)
        user.password_hash = hash_password(temporary)
        user.must_change_password = True
        user.temporary_password_expires_at = expires
        AuthService(self.db).revoke_all(user.id, commit=False)
        self._audit("user.password_reset", user)
        self.db.commit()
        return temporary, expires

    def set_ai(self, user_id: str, enabled: bool, quota: int) -> User:
        if quota > get_settings().ai_daily_request_limit:
            raise ConflictError("The user quota cannot exceed the global AI limit.")
        user = self._user(user_id)
        settings = self._settings(user)
        settings.admin_access_enabled = enabled
        settings.admin_daily_request_limit = quota
        self._audit("user.ai_access_updated", user, {"enabled": enabled, "daily_quota": quota})
        self.db.commit()
        return user

    def set_role(self, user_id: str, role: UserRole, admin_password: str) -> User:
        self._confirm(admin_password)
        user = self._user(user_id)
        if user.id == self.actor.id and role != UserRole.ADMIN:
            raise ForbiddenError("Administrators cannot demote themselves.")
        if user.role == UserRole.ADMIN and role != UserRole.ADMIN:
            remaining = (
                self.db.scalar(
                    select(func.count())
                    .select_from(User)
                    .where(
                        User.role == UserRole.ADMIN, User.status == AccountStatus.ACTIVE, User.id != user.id
                    )
                )
                or 0
            )
            if not remaining:
                raise ForbiddenError("The final active administrator cannot be demoted.")
        user.role = role
        AuthService(self.db).revoke_all(user.id, commit=False)
        self._audit("user.role_updated", user, {"role": role.value})
        self.db.commit()
        return user

    def delete_user(self, user_id: str, confirmation_email: str, admin_password: str) -> None:
        self._confirm(admin_password)
        user = self._user(user_id)
        if user.id == self.actor.id:
            raise ForbiddenError("Administrators cannot delete themselves.")
        if normalize_email(confirmation_email) != user.email:
            raise ConflictError("The confirmation email does not match.")
        if user.role == UserRole.ADMIN:
            remaining = (
                self.db.scalar(
                    select(func.count())
                    .select_from(User)
                    .where(
                        User.role == UserRole.ADMIN, User.status == AccountStatus.ACTIVE, User.id != user.id
                    )
                )
                or 0
            )
            if not remaining:
                raise ForbiddenError("The final active administrator cannot be deleted.")
        # Stop live sandboxes before their database rows and private mounts
        # disappear. Docker cleanup is best-effort so an unavailable local
        # daemon cannot prevent account deletion.
        runtimes = self.db.scalars(
            select(PythonRuntime).where(
                PythonRuntime.user_id == user.id, PythonRuntime.container_id.is_not(None)
            )
        ).all()
        if runtimes:
            from app.python_lab.service import PythonExecutionService

            backend = PythonExecutionService(self.db, user_id=user.id).backend
            for runtime in runtimes:
                if runtime.container_id:
                    with suppress(Exception):
                        backend.destroy(runtime.container_id)
        private_root = (REPO_ROOT / "data" / "users").resolve()
        target = (private_root / user.id).resolve()
        if target.parent != private_root:
            raise ForbiddenError("Invalid private data path.")
        self._audit("user.permanently_deleted", user, {"email": user.email})
        self.db.flush()
        self.db.delete(user)
        self.db.commit()
        if target.exists():
            shutil.rmtree(target)
