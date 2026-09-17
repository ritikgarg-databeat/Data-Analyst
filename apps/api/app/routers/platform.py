from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.errors import AppError
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import (
    get_backup_service,
    get_data_integrity_service,
    get_job_ready_checklist_service,
    get_next_best_action_service,
    get_system_health_service,
)
from app.schemas.platform import (
    BackupBundle,
    ChecklistGroup,
    ChecklistItem,
    DataIntegrityResponse,
    IntegrityCheckResultSchema,
    JobReadyChecklistResponse,
    NextBestActionItemSchema,
    NextBestActionResponse,
    RestorePreviewResponse,
    RestoreRequest,
    SystemHealthResponse,
)
from app.services.backup_service import BackupService
from app.services.data_integrity_service import DataIntegrityService
from app.services.job_ready_checklist_service import JobReadyChecklistService
from app.services.next_best_action_service import NextBestActionService
from app.services.system_health_service import SystemHealthService

router = APIRouter(prefix="/platform", tags=["platform"])

NextBestActionServiceDep = Annotated[NextBestActionService, Depends(get_next_best_action_service)]
SystemHealthServiceDep = Annotated[SystemHealthService, Depends(get_system_health_service)]
BackupServiceDep = Annotated[BackupService, Depends(get_backup_service)]
DataIntegrityServiceDep = Annotated[DataIntegrityService, Depends(get_data_integrity_service)]
JobReadyChecklistServiceDep = Annotated[JobReadyChecklistService, Depends(get_job_ready_checklist_service)]


@router.get("/next-best-actions", response_model=NextBestActionResponse)
def get_next_best_actions(
    user_id: CurrentUserId, service: NextBestActionServiceDep, limit: int = 3
) -> NextBestActionResponse:
    actions = service.get_actions(user_id, limit=limit)
    return NextBestActionResponse(
        actions=[
            NextBestActionItemSchema(title=a.title, why=a.why, source=a.source, url_path=a.url_path)
            for a in actions
        ]
    )


@router.get("/health", response_model=SystemHealthResponse)
def get_system_health(service: SystemHealthServiceDep) -> SystemHealthResponse:
    return service.check_all()


@router.get("/data-integrity", response_model=DataIntegrityResponse)
def get_data_integrity(service: DataIntegrityServiceDep) -> DataIntegrityResponse:
    checks = service.check_all()
    return DataIntegrityResponse(
        checks=[
            IntegrityCheckResultSchema(name=c.name, orphaned_count=c.orphaned_count, detail=c.detail)
            for c in checks
        ],
        all_ok=all(c.orphaned_count == 0 for c in checks),
    )


@router.get("/job-ready-checklist", response_model=JobReadyChecklistResponse)
def get_job_ready_checklist(
    user_id: CurrentUserId, service: JobReadyChecklistServiceDep
) -> JobReadyChecklistResponse:
    groups_raw = service.get_checklist(user_id)
    groups = [
        ChecklistGroup(group=g["group"], items=[ChecklistItem(**item) for item in g["items"]])
        for g in groups_raw
    ]
    all_items = [item for g in groups for item in g.items]
    return JobReadyChecklistResponse(
        groups=groups,
        ready_count=sum(1 for i in all_items if i.ready),
        total_count=len(all_items),
    )


@router.get("/backup", response_model=BackupBundle)
def create_backup(user_id: CurrentUserId, service: BackupServiceDep) -> BackupBundle:
    return service.export_bundle(user_id)


@router.post("/restore/preview", response_model=RestorePreviewResponse)
def preview_restore(payload: BackupBundle, service: BackupServiceDep) -> RestorePreviewResponse:
    return service.preview_restore(payload)


@router.post("/restore")
def restore_backup(payload: RestoreRequest, user_id: CurrentUserId, service: BackupServiceDep) -> dict:
    if not payload.confirm:
        raise AppError("Restore requires explicit confirmation (confirm=true).")
    restored_counts = service.restore_bundle(user_id, payload.bundle)
    return {"restored": restored_counts}
