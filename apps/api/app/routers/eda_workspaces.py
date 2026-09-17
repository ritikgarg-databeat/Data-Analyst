from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_eda_service
from app.schemas.eda import (
    CreateEdaWorkspaceRequest,
    CreateFindingRequest,
    EdaFindingSchema,
    EdaOverview,
    EdaQuestion,
    EdaWorkspaceSchema,
    UpdateEdaWorkspaceRequest,
)
from app.services.eda_service import EdaService

router = APIRouter(prefix="/eda-workspaces", tags=["eda"])


@router.get("", response_model=list[EdaWorkspaceSchema])
def list_workspaces(
    user_id: CurrentUserId, service: Annotated[EdaService, Depends(get_eda_service)]
) -> list[EdaWorkspaceSchema]:
    return service.list_workspaces(user_id)


@router.post("", response_model=EdaWorkspaceSchema, status_code=201)
def create_workspace(
    payload: CreateEdaWorkspaceRequest,
    user_id: CurrentUserId,
    service: Annotated[EdaService, Depends(get_eda_service)],
) -> EdaWorkspaceSchema:
    return service.create_workspace(user_id, payload)


@router.get("/{workspace_id}", response_model=EdaWorkspaceSchema)
def get_workspace(
    workspace_id: str, user_id: CurrentUserId, service: Annotated[EdaService, Depends(get_eda_service)]
) -> EdaWorkspaceSchema:
    return service.get_workspace(user_id, workspace_id)


@router.patch("/{workspace_id}", response_model=EdaWorkspaceSchema)
def update_workspace(
    workspace_id: str,
    payload: UpdateEdaWorkspaceRequest,
    user_id: CurrentUserId,
    service: Annotated[EdaService, Depends(get_eda_service)],
) -> EdaWorkspaceSchema:
    return service.update_workspace(user_id, workspace_id, payload)


@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(
    workspace_id: str, user_id: CurrentUserId, service: Annotated[EdaService, Depends(get_eda_service)]
) -> None:
    service.delete_workspace(user_id, workspace_id)


@router.post("/{workspace_id}/overview", response_model=EdaOverview)
def generate_overview(
    workspace_id: str, user_id: CurrentUserId, service: Annotated[EdaService, Depends(get_eda_service)]
) -> EdaOverview:
    return service.generate_workspace_overview(user_id, workspace_id)


@router.get("/{workspace_id}/questions", response_model=list[EdaQuestion])
def get_questions(
    workspace_id: str, user_id: CurrentUserId, service: Annotated[EdaService, Depends(get_eda_service)]
) -> list[EdaQuestion]:
    return service.workspace_questions(user_id, workspace_id)


@router.post("/{workspace_id}/findings", response_model=EdaFindingSchema, status_code=201)
def add_finding(
    workspace_id: str,
    payload: CreateFindingRequest,
    user_id: CurrentUserId,
    service: Annotated[EdaService, Depends(get_eda_service)],
) -> EdaFindingSchema:
    return service.add_finding(user_id, workspace_id, payload)


@router.delete("/{workspace_id}/findings/{finding_id}", status_code=204)
def delete_finding(
    workspace_id: str,
    finding_id: str,
    user_id: CurrentUserId,
    service: Annotated[EdaService, Depends(get_eda_service)],
) -> None:
    service.delete_finding(user_id, workspace_id, finding_id)
