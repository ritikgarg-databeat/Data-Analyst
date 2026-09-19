from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.current_user import AdminUser, CurrentUserId
from app.dependencies.services import get_project_service
from app.schemas.project import (
    AddProjectDatasetRequest,
    CreateProjectArtifactRequest,
    CreateProjectFromDatasetRequest,
    CreateProjectRequest,
    LinkProjectDataModelRequest,
    Project,
    ProjectArtifactSchema,
    ProjectDatasetSchema,
    ProjectTemplateAdminSchema,
    ProjectTemplateSchema,
    SaveProjectReflectionRequest,
    StartProjectFromTemplateRequest,
    SubmitProjectRequest,
    UpdateMilestoneRequest,
    UpdateProjectDbtRefsRequest,
    UpdateProjectDocumentationRequest,
    UpdateProjectPresentationRequest,
    UpdateProjectRequest,
    UpdateProjectTemplateAdminRequest,
)
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]


# --- Templates — registered before the /{project_id} catch-all routes ------


# Registered before GET /templates/{slug} so "admin" isn't swallowed by the slug route.
@router.get("/templates/admin", response_model=list[ProjectTemplateAdminSchema])
def list_project_templates_admin(
    admin: AdminUser, service: ProjectServiceDep
) -> list[ProjectTemplateAdminSchema]:
    return [ProjectTemplateAdminSchema.model_validate(t) for t in service.list_templates_admin()]


@router.patch("/templates/admin/{template_id}", response_model=ProjectTemplateAdminSchema)
def update_project_template_admin(
    template_id: str, payload: UpdateProjectTemplateAdminRequest, admin: AdminUser, service: ProjectServiceDep
) -> ProjectTemplateAdminSchema:
    return ProjectTemplateAdminSchema.model_validate(
        service.update_template_admin(template_id, payload.is_active)
    )


@router.get("/templates", response_model=list[ProjectTemplateSchema])
def list_project_templates(service: ProjectServiceDep) -> list[ProjectTemplateSchema]:
    return service.list_templates()


@router.get("/templates/{slug}", response_model=ProjectTemplateSchema)
def get_project_template(slug: str, service: ProjectServiceDep) -> ProjectTemplateSchema:
    return service.get_template(slug)


@router.post("/from-template", response_model=Project, status_code=201)
def create_project_from_template(
    payload: StartProjectFromTemplateRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.create_from_template(user_id, payload.template_slug)


# --- Phase 5: free-form project shell ---------------------------------------


@router.get("", response_model=list[Project])
def list_projects(user_id: CurrentUserId, service: ProjectServiceDep) -> list[Project]:
    return service.list_projects(user_id)


@router.post("", response_model=Project, status_code=201)
def create_project(
    payload: CreateProjectRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.create(user_id, payload)


@router.post("/from-dataset/{dataset_id}", response_model=Project, status_code=201)
def create_project_from_dataset(
    dataset_id: str,
    payload: CreateProjectFromDatasetRequest,
    user_id: CurrentUserId,
    service: ProjectServiceDep,
) -> Project:
    return service.create_from_dataset(user_id, dataset_id, payload)


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: str, user_id: CurrentUserId, service: ProjectServiceDep) -> Project:
    return service.get(user_id, project_id)


@router.patch("/{project_id}", response_model=Project)
def update_project(
    project_id: str, payload: UpdateProjectRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.update(user_id, project_id, payload)


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, user_id: CurrentUserId, service: ProjectServiceDep) -> None:
    service.delete(user_id, project_id)


# --- Phase 8: milestones / artifacts / datasets / documentation / etc. ------


@router.patch("/{project_id}/milestones/{milestone_id}", response_model=Project)
def update_milestone(
    project_id: str,
    milestone_id: str,
    payload: UpdateMilestoneRequest,
    user_id: CurrentUserId,
    service: ProjectServiceDep,
) -> Project:
    return service.update_milestone(user_id, project_id, milestone_id, payload.is_completed)


@router.post("/{project_id}/artifacts", response_model=ProjectArtifactSchema, status_code=201)
def add_artifact(
    project_id: str, payload: CreateProjectArtifactRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> ProjectArtifactSchema:
    return service.add_artifact(user_id, project_id, **payload.model_dump())


@router.delete("/{project_id}/artifacts/{artifact_id}", status_code=204)
def delete_artifact(
    project_id: str, artifact_id: str, user_id: CurrentUserId, service: ProjectServiceDep
) -> None:
    service.delete_artifact(user_id, project_id, artifact_id)


@router.post("/{project_id}/datasets", response_model=ProjectDatasetSchema, status_code=201)
def add_project_dataset(
    project_id: str, payload: AddProjectDatasetRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> ProjectDatasetSchema:
    return service.add_dataset(user_id, project_id, payload.dataset_id, payload.reason)


@router.delete("/{project_id}/datasets/{project_dataset_id}", status_code=204)
def remove_project_dataset(
    project_id: str, project_dataset_id: str, user_id: CurrentUserId, service: ProjectServiceDep
) -> None:
    service.remove_dataset(user_id, project_id, project_dataset_id)


@router.patch("/{project_id}/documentation", response_model=Project)
def update_documentation(
    project_id: str,
    payload: UpdateProjectDocumentationRequest,
    user_id: CurrentUserId,
    service: ProjectServiceDep,
) -> Project:
    return service.update_documentation(user_id, project_id, payload.documentation)


@router.patch("/{project_id}/presentation", response_model=Project)
def update_presentation(
    project_id: str,
    payload: UpdateProjectPresentationRequest,
    user_id: CurrentUserId,
    service: ProjectServiceDep,
) -> Project:
    return service.update_presentation(user_id, project_id, payload.presentation)


@router.patch("/{project_id}/data-model", response_model=Project)
def link_data_model(
    project_id: str, payload: LinkProjectDataModelRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.link_data_model(user_id, project_id, payload.data_model_id)


@router.patch("/{project_id}/dbt-refs", response_model=Project)
def update_dbt_refs(
    project_id: str, payload: UpdateProjectDbtRefsRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.update_dbt_refs(user_id, project_id, payload.dbt_model_refs)


@router.post("/{project_id}/submit", response_model=Project)
def submit_project(
    project_id: str, payload: SubmitProjectRequest, user_id: CurrentUserId, service: ProjectServiceDep
) -> Project:
    return service.submit_project(user_id, project_id, payload.rubric_selections)


@router.patch("/{project_id}/reflection", response_model=Project)
def save_reflection(
    project_id: str,
    payload: SaveProjectReflectionRequest,
    user_id: CurrentUserId,
    service: ProjectServiceDep,
) -> Project:
    return service.save_reflection(user_id, project_id, payload.reflection.model_dump())
