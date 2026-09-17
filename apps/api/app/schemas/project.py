from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CaseAttemptStatus, CaseCategory, ProjectArtifactType
from app.schemas.case import RubricCategorySchema
from app.schemas.common import ORMSchema


class ProjectMilestoneSchema(ORMSchema):
    id: str
    title: str
    description: str | None
    display_order: int
    is_completed: bool
    completed_at: datetime | None


class ProjectArtifactSchema(ORMSchema):
    id: str
    artifact_type: ProjectArtifactType
    ref_id: str | None
    label: str
    snapshot: str | None
    notes: str | None
    created_at: datetime


class ProjectDatasetSchema(ORMSchema):
    id: str
    dataset_id: str
    reason: str | None


class Project(ORMSchema):
    id: str
    dataset_id: str | None = None
    template_id: str | None = None
    data_model_id: str | None = None
    name: str
    description: str | None = None
    notes: str | None = None
    status: CaseAttemptStatus
    objective: str | None = None
    business_context: str | None = None
    requirements: list[str] = []
    dbt_model_refs: list[str] = []
    documentation: dict = {}
    presentation: list[dict] = []
    rubric_selections: dict = {}
    score: dict | None = None
    reflection: dict | None = None
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    milestones: list[ProjectMilestoneSchema] = []
    artifacts: list[ProjectArtifactSchema] = []
    project_datasets: list[ProjectDatasetSchema] = []


class CreateProjectRequest(BaseModel):
    name: str
    dataset_id: str | None = None
    description: str | None = None


class CreateProjectFromDatasetRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    notes: str | None = None
    status: CaseAttemptStatus | None = None


# --- Phase 8: project templates + the richer project engine ---------------


class ProjectTemplateSchema(ORMSchema):
    id: str
    slug: str
    title: str
    category: CaseCategory
    business_context: str | None
    objective: str
    requirements: list[str]
    suggested_datasets: list[str]
    milestones: list[dict]  # [{title, description}]
    required_skills: list[str]
    rubric: list[RubricCategorySchema]
    learning_objectives: list[str]
    estimated_hours: float | None
    tags: list[str]
    version: int


class ProjectTemplateAdminSchema(ORMSchema):
    """The admin-facing project-template row (Content Admin) — templates are
    content-authored in `content/projects/*.yaml`, so admin only lists/
    activates/deactivates, matching the Case/Lesson/Exercise admin panels."""

    id: str
    slug: str
    title: str
    category: CaseCategory
    is_active: bool
    version: int


class UpdateProjectTemplateAdminRequest(BaseModel):
    is_active: bool


class StartProjectFromTemplateRequest(BaseModel):
    template_slug: str


class UpdateMilestoneRequest(BaseModel):
    is_completed: bool


class CreateProjectArtifactRequest(BaseModel):
    artifact_type: ProjectArtifactType
    ref_id: str | None = None
    label: str
    snapshot: str | None = None
    notes: str | None = None


class UpdateProjectDocumentationRequest(BaseModel):
    documentation: dict


class UpdateProjectPresentationRequest(BaseModel):
    presentation: list[dict]


class AddProjectDatasetRequest(BaseModel):
    dataset_id: str
    reason: str | None = None


class LinkProjectDataModelRequest(BaseModel):
    data_model_id: str | None = None


class UpdateProjectDbtRefsRequest(BaseModel):
    dbt_model_refs: list[str]


class SubmitProjectRequest(BaseModel):
    rubric_selections: dict[str, list[str]]


class ProjectReflectionPayload(BaseModel):
    what_learned: str
    what_difficult: str
    what_differently: str
    skill_improved: str
    what_review: str


class SaveProjectReflectionRequest(BaseModel):
    reflection: ProjectReflectionPayload
