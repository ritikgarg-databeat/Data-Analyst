from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from app.core.file_extraction import extract_text, read_upload_bounded
from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_resume_service
from app.models.enums import ResumeSource
from app.schemas.resume import (
    CreateResumeRequest,
    CreateResumeVersionRequest,
    ResumeEvidenceSchema,
    ResumeGapAnalysisResponse,
    ResumeReviewSchema,
    ResumeSchema,
    ResumeVersionSchema,
    UpdateResumeRequest,
)
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resume", tags=["resume"])

ResumeServiceDep = Annotated[ResumeService, Depends(get_resume_service)]


@router.get("", response_model=list[ResumeSchema])
def list_resumes(user_id: CurrentUserId, service: ResumeServiceDep) -> list[ResumeSchema]:
    return service.list_resumes(user_id)


@router.post("", response_model=ResumeSchema, status_code=201)
def create_resume(
    payload: CreateResumeRequest, user_id: CurrentUserId, service: ResumeServiceDep
) -> ResumeSchema:
    return service.create_resume(user_id, payload)


@router.patch("/{resume_id}", response_model=ResumeSchema)
def update_resume(
    resume_id: str, payload: UpdateResumeRequest, user_id: CurrentUserId, service: ResumeServiceDep
) -> ResumeSchema:
    return service.update_resume(user_id, resume_id, payload)


@router.delete("/{resume_id}", status_code=204)
def delete_resume(resume_id: str, user_id: CurrentUserId, service: ResumeServiceDep) -> None:
    service.delete_resume(user_id, resume_id)


@router.post("/{resume_id}/versions", response_model=ResumeVersionSchema, status_code=201)
def create_version(
    resume_id: str, payload: CreateResumeVersionRequest, user_id: CurrentUserId, service: ResumeServiceDep
) -> ResumeVersionSchema:
    return service.create_version(user_id, resume_id, payload)


@router.post("/{resume_id}/versions/upload", response_model=ResumeVersionSchema, status_code=201)
async def upload_version(
    resume_id: str, user_id: CurrentUserId, service: ResumeServiceDep, file: UploadFile
) -> ResumeVersionSchema:
    content = await read_upload_bounded(file)
    raw_text = extract_text(file.filename or "upload.txt", content)
    payload = CreateResumeVersionRequest(
        source=ResumeSource.UPLOADED, raw_text=raw_text, file_name=file.filename
    )
    return service.create_version(user_id, resume_id, payload)


@router.get("/versions/{version_id}", response_model=ResumeVersionSchema)
def get_version(version_id: str, user_id: CurrentUserId, service: ResumeServiceDep) -> ResumeVersionSchema:
    return service.get_version(user_id, version_id)


@router.post(
    "/versions/{version_id}/extract-evidence", response_model=list[ResumeEvidenceSchema], status_code=201
)
def extract_evidence(
    version_id: str, user_id: CurrentUserId, service: ResumeServiceDep
) -> list[ResumeEvidenceSchema]:
    evidence = service.extract_evidence(user_id, version_id)
    return [ResumeEvidenceSchema.model_validate(e) for e in evidence]


@router.post("/versions/{version_id}/review", response_model=ResumeReviewSchema, status_code=201)
def review_version(
    version_id: str, user_id: CurrentUserId, service: ResumeServiceDep, target_role_title: str | None = None
) -> ResumeReviewSchema:
    return service.review(user_id, version_id, target_role_title)


@router.get("/versions/{version_id}/gap-analysis", response_model=ResumeGapAnalysisResponse)
def gap_analysis(
    version_id: str, user_id: CurrentUserId, service: ResumeServiceDep, target_role_id: str | None = None
) -> ResumeGapAnalysisResponse:
    return service.gap_analysis(user_id, version_id, target_role_id)
