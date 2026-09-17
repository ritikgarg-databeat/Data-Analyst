"""Cross-cutting Phase 12 schemas — Next Best Action, System Health/
Diagnostics, and Backup/Restore. These don't belong to any single domain
(SQL/Python/Career/...), so they get their own module rather than being
bolted onto an unrelated schema file."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# --- Next Best Action ---------------------------------------------------------

NextBestActionSource = Literal["lesson", "interview", "job_description", "portfolio", "goal"]


class NextBestActionItemSchema(BaseModel):
    title: str
    why: str
    source: NextBestActionSource
    url_path: str


class NextBestActionResponse(BaseModel):
    actions: list[NextBestActionItemSchema] = Field(default_factory=list)


# --- System Health / Diagnostics ----------------------------------------------

ServiceStatusLevel = Literal["ok", "degraded", "unavailable", "not_configured"]


class ServiceStatusSchema(BaseModel):
    """One row of the System Health panel. `detail` is always plain,
    actionable text (e.g. "Docker not reachable" / "Set AI_PROVIDER and a
    matching key") — never a raw stack trace."""

    name: str
    status: ServiceStatusLevel
    detail: str | None = None


class SystemHealthResponse(BaseModel):
    checked_at: datetime
    services: list[ServiceStatusSchema]


# --- Backup / Restore ----------------------------------------------------------


class BackupManifest(BaseModel):
    """Metadata describing a backup bundle — checked by restore before
    touching any real data (spec section 21's "validate backup version,
    schema compatibility, file integrity")."""

    created_at: datetime
    app_version: str
    schema_version: str  # the Alembic head revision the backup was taken against
    user_email: str
    counts: dict[str, int] = Field(default_factory=dict)


class BackupBundle(BaseModel):
    """The full exportable/importable bundle (spec section 20) — deliberately
    only ever contains the CURRENT user's own rows from the tables listed in
    `counts`, and NEVER secrets (API keys, database credentials) — those stay
    in `.env`/environment variables, never in a backup file."""

    manifest: BackupManifest
    data: dict[str, list[dict]] = Field(default_factory=dict)


class RestorePreviewResponse(BaseModel):
    """What `POST /platform/restore/preview` reports before any write
    happens — the user must see this and explicitly confirm (spec section
    21's "require explicit confirmation") before `POST /platform/restore`
    actually applies it."""

    manifest: BackupManifest
    compatible: bool
    issues: list[str] = Field(default_factory=list)


class RestoreRequest(BaseModel):
    bundle: BackupBundle
    confirm: bool = False


# --- Data Integrity Audit -----------------------------------------------------


class IntegrityCheckResultSchema(BaseModel):
    name: str
    orphaned_count: int
    detail: str


class DataIntegrityResponse(BaseModel):
    checks: list[IntegrityCheckResultSchema]
    all_ok: bool


# --- Job-Ready Checklist ------------------------------------------------------


class ChecklistItem(BaseModel):
    label: str
    ready: bool


class ChecklistGroup(BaseModel):
    group: str
    items: list[ChecklistItem]


class JobReadyChecklistResponse(BaseModel):
    groups: list[ChecklistGroup]
    ready_count: int
    total_count: int
