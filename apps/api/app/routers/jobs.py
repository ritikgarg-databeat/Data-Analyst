from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile

from app.core.file_extraction import extract_text, read_upload_bounded
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_jd_service
from app.models.enums import JDSource
from app.schemas.jobs import (
    AnalyzeJobDescriptionRequest,
    CreateJobDescriptionRequest,
    CreateJobPrepWorkspaceRequest,
    JDAnalysisSchema,
    JDComparisonResponse,
    JDInterviewPlanResponse,
    JDRequirementSchema,
    JobDescriptionSchema,
    JobPreparationWorkspaceSchema,
    PreparationPlanResponse,
    SkillGapTableResponse,
    UpdateJobDescriptionRequest,
    UpdateJobPrepWorkspaceRequest,
)
from app.services.jd_service import JDService

router = APIRouter(prefix="/jobs", tags=["jobs"])

JDServiceDep = Annotated[JDService, Depends(get_jd_service)]


@router.get("/descriptions", response_model=list[JobDescriptionSchema])
def list_job_descriptions(user_id: CurrentUserId, service: JDServiceDep) -> list[JobDescriptionSchema]:
    return service.list_job_descriptions(user_id)


@router.post("/descriptions", response_model=JobDescriptionSchema, status_code=201)
def create_job_description(
    payload: CreateJobDescriptionRequest, user_id: CurrentUserId, service: JDServiceDep
) -> JobDescriptionSchema:
    return service.create_job_description(user_id, payload)


@router.post("/descriptions/upload", response_model=JobDescriptionSchema, status_code=201)
async def upload_job_description(
    user_id: CurrentUserId,
    service: JDServiceDep,
    file: UploadFile,
    title: str = Form(...),
    company: str | None = Form(default=None),
    location: str | None = Form(default=None),
    notes: str | None = Form(default=None),
) -> JobDescriptionSchema:
    content = await read_upload_bounded(file)
    raw_text = extract_text(file.filename or "upload.txt", content)
    payload = CreateJobDescriptionRequest(
        company=company,
        title=title,
        source=JDSource.UPLOADED,
        raw_text=raw_text,
        location=location,
        notes=notes,
    )
    return service.create_job_description(user_id, payload)


@router.get("/descriptions/compare", response_model=JDComparisonResponse)
def compare_job_descriptions(
    user_id: CurrentUserId, service: JDServiceDep, jd_ids: str | None = None
) -> JDComparisonResponse:
    """`jd_ids` is a comma-separated list of JobDescription ids to compare;
    omit to compare every saved JD."""
    ids = jd_ids.split(",") if jd_ids else None
    return service.compare(user_id, ids)


@router.get("/descriptions/{jd_id}", response_model=JobDescriptionSchema)
def get_job_description(jd_id: str, user_id: CurrentUserId, service: JDServiceDep) -> JobDescriptionSchema:
    return service.get_job_description(user_id, jd_id)


@router.patch("/descriptions/{jd_id}", response_model=JobDescriptionSchema)
def update_job_description(
    jd_id: str, payload: UpdateJobDescriptionRequest, user_id: CurrentUserId, service: JDServiceDep
) -> JobDescriptionSchema:
    return service.update_job_description(user_id, jd_id, payload)


@router.delete("/descriptions/{jd_id}", status_code=204)
def delete_job_description(jd_id: str, user_id: CurrentUserId, service: JDServiceDep) -> None:
    service.delete_job_description(user_id, jd_id)


@router.post("/descriptions/{jd_id}/extract", response_model=list[JDRequirementSchema], status_code=201)
def extract_requirements(
    jd_id: str, user_id: CurrentUserId, service: JDServiceDep
) -> list[JDRequirementSchema]:
    requirements = service.extract_requirements(user_id, jd_id)
    return [JDRequirementSchema.model_validate(r) for r in requirements]


@router.get("/descriptions/{jd_id}/skill-gaps", response_model=SkillGapTableResponse)
def get_skill_gaps(jd_id: str, user_id: CurrentUserId, service: JDServiceDep) -> SkillGapTableResponse:
    # Recomputed on every read (not just after /analyze) so the gap table
    # always reflects current mastery, immediately after extraction.
    return service.compute_skill_gaps(user_id, jd_id)


@router.post("/descriptions/{jd_id}/analyze", response_model=JDAnalysisSchema, status_code=201)
def analyze_job_description(
    jd_id: str, payload: AnalyzeJobDescriptionRequest, user_id: CurrentUserId, service: JDServiceDep
) -> JDAnalysisSchema:
    return service.analyze(user_id, jd_id, payload)


@router.get("/descriptions/{jd_id}/analysis", response_model=JDAnalysisSchema | None)
def get_latest_analysis(jd_id: str, user_id: CurrentUserId, service: JDServiceDep) -> JDAnalysisSchema | None:
    return service.get_latest_analysis(user_id, jd_id)


@router.get("/descriptions/{jd_id}/preparation-plan", response_model=PreparationPlanResponse)
def get_preparation_plan(
    jd_id: str, user_id: CurrentUserId, service: JDServiceDep
) -> PreparationPlanResponse:
    return service.generate_preparation_plan(user_id, jd_id)


@router.get("/descriptions/{jd_id}/interview-plan", response_model=JDInterviewPlanResponse)
def get_interview_plan(jd_id: str, user_id: CurrentUserId, service: JDServiceDep) -> JDInterviewPlanResponse:
    return service.generate_interview_plan(user_id, jd_id)


# --- Job Preparation Workspace ("Prepare for This Job") --------------------------------


@router.get("/workspaces", response_model=list[JobPreparationWorkspaceSchema])
def list_workspaces(user_id: CurrentUserId, service: JDServiceDep) -> list[JobPreparationWorkspaceSchema]:
    return service.list_workspaces(user_id)


@router.post("/workspaces", response_model=JobPreparationWorkspaceSchema, status_code=201)
def create_workspace(
    payload: CreateJobPrepWorkspaceRequest, user_id: CurrentUserId, service: JDServiceDep
) -> JobPreparationWorkspaceSchema:
    return service.create_workspace(user_id, payload)


@router.patch("/workspaces/{workspace_id}", response_model=JobPreparationWorkspaceSchema)
def update_workspace(
    workspace_id: str, payload: UpdateJobPrepWorkspaceRequest, user_id: CurrentUserId, service: JDServiceDep
) -> JobPreparationWorkspaceSchema:
    return service.update_workspace(user_id, workspace_id, payload)
