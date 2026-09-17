"""Dataset-scoped EDA convenience endpoints (section 44 of the Phase 5
spec: `/api/v1/eda/{dataset_id}`, `/api/v1/eda/{dataset_id}/questions`) —
compute the automatic overview / question list directly from a dataset's
latest profile, no saved workspace required. See app/routers/eda_workspaces.py
for the persisted-workspace CRUD (kept on a separate prefix to avoid any
path ambiguity with `{dataset_id}`)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.services import get_eda_service
from app.schemas.eda import EdaOverview, EdaQuestion
from app.services.eda_service import EdaService

router = APIRouter(prefix="/eda", tags=["eda"])


@router.get("/{dataset_id}", response_model=EdaOverview)
def get_overview(
    dataset_id: str,
    service: Annotated[EdaService, Depends(get_eda_service)],
    table: str | None = Query(default=None),
) -> EdaOverview:
    return service.dataset_overview(dataset_id, table)


@router.get("/{dataset_id}/questions", response_model=list[EdaQuestion])
def get_questions(
    dataset_id: str,
    service: Annotated[EdaService, Depends(get_eda_service)],
    table: str | None = Query(default=None),
) -> list[EdaQuestion]:
    return service.dataset_questions(dataset_id, table)
