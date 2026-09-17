"""Backup / Restore (Phase 12, spec sections 20-21) — exports/imports the
CURRENT user's own rows across every table that holds personal data
(progress, attempts, projects, cases, notes, bookmarks, career profile,
JDs, resume versions, portfolio, AI preferences/conversations). Never
includes secrets (API keys, database credentials) — those live only in
`.env`/environment variables and are never touched here. Never includes
imported dataset FILES or generated warehouse artifacts (out of scope for
a personal-progress backup — see docs/backup-restore.md's documented
limitation); a restored `Project.dataset_id` may reference a dataset the
target environment hasn't re-imported, which is safe (no DB-level FK
enforcement is enabled for SQLite in this app) but won't resolve to real
data until the dataset is re-imported by hand.

Restore is idempotent by primary key: a row whose `id` already exists in
the target database is left untouched, never overwritten — re-running a
restore (e.g. after a partial failure) is always safe. The exception is the
three singleton-per-user tables (AISettings/CareerProfile/Portfolio, each
`unique_per_user=True` below) — those are matched by `user_id` instead,
since they're lazily auto-created under a fresh id the first time a feature
is used, and are updated in place from the backup rather than skipped, so a
restore actually recovers their real content instead of leaving whatever
placeholder default was auto-created."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, select, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models.ai import AIConversation, AIMessage, AIMistakeMemory, AISettings, AISkillDiagnosis
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
from app.models.case import CaseAttempt
from app.models.exercise_attempt import ExerciseAttempt
from app.models.interview import InterviewBookmark, InterviewNote
from app.models.lesson_progress import LessonProgress
from app.models.project import Project, ProjectArtifact, ProjectDataset, ProjectMilestone
from app.models.user import User
from app.schemas.platform import BackupBundle, BackupManifest, RestorePreviewResponse

APP_SCHEMA_VERSION = "phase-12"  # bumped whenever a backed-up table's shape changes incompatibly


@dataclass
class _Entity:
    name: str
    model: type
    filter_field: str
    parent: str | None = None  # another _Entity.name whose exported ids feed filter_field
    remap_user_id: bool = False  # True for direct user-owned tables; restore rebinds to the CURRENT user
    # True for a table with a real DB `UniqueConstraint("user_id", ...)` —
    # AISettings/CareerProfile/Portfolio are all lazily auto-created (with a
    # brand-new id) the first time a feature is used, so by the time a
    # restore runs the user may already have one of these under a DIFFERENT
    # id than the backup's. Matching by id alone would insert a second row
    # and crash on that unique constraint; restore instead matches by
    # user_id and updates the existing row's fields in place.
    unique_per_user: bool = False


ENTITIES: list[_Entity] = [
    _Entity("lesson_progress", LessonProgress, "user_id", remap_user_id=True),
    _Entity("exercise_attempts", ExerciseAttempt, "user_id", remap_user_id=True),
    _Entity("assessment_attempts", AssessmentAttempt, "user_id", remap_user_id=True),
    _Entity("assessment_answers", AssessmentAnswer, "attempt_id", parent="assessment_attempts"),
    _Entity("interview_notes", InterviewNote, "user_id", remap_user_id=True),
    _Entity("interview_bookmarks", InterviewBookmark, "user_id", remap_user_id=True),
    _Entity("career_notes", CareerNote, "user_id", remap_user_id=True),
    _Entity("target_roles", TargetRole, "user_id", remap_user_id=True),
    _Entity("career_profiles", CareerProfile, "user_id", remap_user_id=True, unique_per_user=True),
    _Entity("career_goals", CareerGoal, "user_id", remap_user_id=True),
    _Entity("career_milestones", CareerMilestone, "user_id", remap_user_id=True),
    _Entity("career_assessments", CareerAssessment, "user_id", remap_user_id=True),
    _Entity("behavioral_stories", BehavioralStory, "user_id", remap_user_id=True),
    _Entity("user_achievements", UserAchievement, "user_id", remap_user_id=True),
    _Entity("job_descriptions", JobDescription, "user_id", remap_user_id=True),
    _Entity("jd_requirements", JDRequirement, "job_description_id", parent="job_descriptions"),
    _Entity("jd_analyses", JDAnalysis, "job_description_id", parent="job_descriptions"),
    _Entity("skill_gaps", SkillGap, "user_id", remap_user_id=True),
    _Entity("job_preparation_workspaces", JobPreparationWorkspace, "user_id", remap_user_id=True),
    _Entity("resumes", Resume, "user_id", remap_user_id=True),
    _Entity("resume_versions", ResumeVersion, "resume_id", parent="resumes"),
    _Entity("resume_evidence", ResumeEvidence, "resume_version_id", parent="resume_versions"),
    _Entity("resume_reviews", ResumeReview, "resume_version_id", parent="resume_versions"),
    _Entity("portfolios", Portfolio, "user_id", remap_user_id=True, unique_per_user=True),
    _Entity("portfolio_items", PortfolioItem, "portfolio_id", parent="portfolios"),
    _Entity("projects", Project, "user_id", remap_user_id=True),
    _Entity("project_milestones", ProjectMilestone, "project_id", parent="projects"),
    _Entity("project_artifacts", ProjectArtifact, "project_id", parent="projects"),
    _Entity("project_datasets", ProjectDataset, "project_id", parent="projects"),
    _Entity("case_attempts", CaseAttempt, "user_id", remap_user_id=True),
    _Entity("ai_settings", AISettings, "user_id", remap_user_id=True, unique_per_user=True),
    _Entity("ai_conversations", AIConversation, "user_id", remap_user_id=True),
    _Entity("ai_messages", AIMessage, "conversation_id", parent="ai_conversations"),
    _Entity("ai_mistake_memory", AIMistakeMemory, "user_id", remap_user_id=True),
    _Entity("ai_skill_diagnoses", AISkillDiagnosis, "user_id", remap_user_id=True),
]
_ENTITY_NAMES = {e.name for e in ENTITIES}


def _serialize_row(obj: object) -> dict:
    row: dict = {}
    for attr in sa_inspect(obj).mapper.column_attrs:
        value = getattr(obj, attr.key)
        if isinstance(value, datetime | date):
            value = value.isoformat()
        elif isinstance(value, Enum):
            value = value.value
        row[attr.key] = value
    return row


def _coerce_value(col, value: object) -> object:
    if value is not None:
        if isinstance(col.type, DateTime):
            value = datetime.fromisoformat(value)
        elif isinstance(col.type, Date):
            value = date.fromisoformat(value)
        elif isinstance(col.type, SAEnum) and col.type.enum_class is not None:
            value = col.type.enum_class(value)
    return value


def _deserialize_row(model: type, row: dict) -> object:
    kwargs: dict = {}
    for col in model.__table__.columns:
        if col.name not in row:
            continue
        kwargs[col.name] = _coerce_value(col, row[col.name])
    return model(**kwargs)


def _single_id_column(model: type) -> str | None:
    """Returns "id" if `model` has that one-column synthetic primary key (true
    of every current backup entity except LessonProgress/UserSkill, which use
    a composite (user_id, x_id) key instead) — None otherwise."""
    pk_cols = list(sa_inspect(model).primary_key)
    if len(pk_cols) == 1 and pk_cols[0].name == "id":
        return "id"
    return None


def _row_identity(model: type, row: dict) -> object:
    """A value suitable for `Session.get(model, ...)` built from a
    (possibly composite) primary key — a scalar for a single-column key, a
    tuple (in column order) for a composite one, matching what `Session.get`
    itself expects either way."""
    pk_cols = list(sa_inspect(model).primary_key)
    values = tuple(row[col.name] for col in pk_cols)
    return values[0] if len(values) == 1 else values


class BackupService:
    def __init__(self, db: Session, settings: Settings | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()

    def _alembic_head(self) -> str:
        try:
            result = self.db.execute(text("SELECT version_num FROM alembic_version")).first()
        except Exception:  # noqa: BLE001 — a missing/unreadable alembic_version table is non-fatal
            return "unknown"
        return result[0] if result else "unknown"

    def export_bundle(self, user_id: str) -> BackupBundle:
        user = self.db.get(User, user_id)
        exported_ids: dict[str, set[str]] = {}
        data: dict[str, list[dict]] = {}
        counts: dict[str, int] = {}

        for entity in ENTITIES:
            if entity.parent is None:
                stmt = select(entity.model).where(getattr(entity.model, entity.filter_field) == user_id)
            else:
                parent_ids = exported_ids.get(entity.parent, set())
                if not parent_ids:
                    data[entity.name] = []
                    counts[entity.name] = 0
                    exported_ids[entity.name] = set()
                    continue
                stmt = select(entity.model).where(getattr(entity.model, entity.filter_field).in_(parent_ids))
            rows = self.db.execute(stmt).scalars().all()
            data[entity.name] = [_serialize_row(r) for r in rows]
            counts[entity.name] = len(rows)
            # Only single-`id`-column entities are ever referenced as a
            # `parent=` elsewhere, but a composite-key entity (LessonProgress)
            # has no `.id` attribute at all — tracking stays empty for those
            # rather than crashing on an AttributeError.
            id_col = _single_id_column(entity.model)
            exported_ids[entity.name] = {getattr(r, id_col) for r in rows} if id_col else set()

        manifest = BackupManifest(
            created_at=datetime.now(UTC),
            app_version=self.settings.app_version,
            schema_version=self._alembic_head(),
            user_email=user.email if user else "unknown",
            counts=counts,
        )
        return BackupBundle(manifest=manifest, data=data)

    def preview_restore(self, bundle: BackupBundle) -> RestorePreviewResponse:
        issues: list[str] = []
        current_head = self._alembic_head()
        if bundle.manifest.schema_version != current_head:
            issues.append(
                f"Backup was taken at schema '{bundle.manifest.schema_version}', current schema is "
                f"'{current_head}'. Restore will still attempt to apply it, but some rows may not match."
            )
        unknown_entities = set(bundle.data.keys()) - _ENTITY_NAMES
        if unknown_entities:
            issues.append(
                f"Backup contains unrecognized tables (ignored on restore): {sorted(unknown_entities)}"
            )
        for entity in ENTITIES:
            rows = bundle.data.get(entity.name, [])
            id_col = _single_id_column(entity.model)
            if id_col is None:
                continue  # a composite-key entity (LessonProgress) never carries an "id" field at all
            for row in rows:
                if id_col not in row:
                    issues.append(f"'{entity.name}' has a row with no id — file may be corrupted.")
                    break
        return RestorePreviewResponse(manifest=bundle.manifest, compatible=not issues, issues=issues)

    def restore_bundle(self, user_id: str, bundle: BackupBundle) -> dict[str, int]:
        restored_counts: dict[str, int] = {}
        for entity in ENTITIES:
            rows = bundle.data.get(entity.name, [])
            restored = 0
            for row in rows:
                payload = dict(row)
                if entity.remap_user_id:
                    payload["user_id"] = user_id

                if entity.unique_per_user:
                    # A singleton-per-user row (AISettings/CareerProfile/Portfolio) may
                    # already exist under a DIFFERENT id than the backup's — e.g.
                    # lazily auto-created the first time the feature was used, before
                    # this restore ever ran. Matching by id alone would insert a
                    # second row and crash the whole restore on that table's real
                    # `UniqueConstraint("user_id", ...)`. Match by user_id instead and
                    # update the existing row's real fields in place.
                    existing = self.db.execute(
                        select(entity.model).where(entity.model.user_id == user_id)
                    ).scalar_one_or_none()
                    if existing is not None:
                        # Only count (and write) this as "restored" if some field
                        # genuinely differs — restoring a bundle that's already
                        # identical to the current state must stay a true no-op,
                        # not report a phantom restored row every time.
                        changed = False
                        for col in entity.model.__table__.columns:
                            if col.name in ("id", "user_id") or col.name not in payload:
                                continue
                            new_value = _coerce_value(col, payload[col.name])
                            if getattr(existing, col.name) != new_value:
                                setattr(existing, col.name, new_value)
                                changed = True
                        if changed:
                            restored += 1
                        continue

                if self.db.get(entity.model, _row_identity(entity.model, payload)) is not None:
                    continue  # idempotent — never overwrite an existing row
                obj = _deserialize_row(entity.model, payload)
                self.db.add(obj)
                restored += 1
            self.db.flush()
            restored_counts[entity.name] = restored
        self.db.commit()
        return restored_counts
