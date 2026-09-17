from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_finding_service
from app.schemas.finding import (
    AddEvidenceRequest,
    CreateFindingRequest,
    CreateHypothesisRequest,
    EvidenceSchema,
    FindingSchema,
    HypothesisSchema,
    UpdateFindingRequest,
    UpdateHypothesisRequest,
)
from app.services.finding_service import FindingService

router = APIRouter(tags=["findings"])


@router.get("/findings", response_model=list[FindingSchema])
def list_findings(
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
    case_attempt_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
) -> list[FindingSchema]:
    return service.list_findings(user_id, case_attempt_id=case_attempt_id, project_id=project_id)


@router.post("/findings", response_model=FindingSchema, status_code=201)
def create_finding(
    payload: CreateFindingRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> FindingSchema:
    return service.create_finding(user_id, **payload.model_dump())


@router.patch("/findings/{finding_id}", response_model=FindingSchema)
def update_finding(
    finding_id: str,
    payload: UpdateFindingRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> FindingSchema:
    return service.update_finding(user_id, finding_id, **payload.model_dump(exclude_unset=True))


@router.delete("/findings/{finding_id}", status_code=204)
def delete_finding(
    finding_id: str,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> None:
    service.delete_finding(user_id, finding_id)


@router.post("/findings/{finding_id}/evidence", response_model=EvidenceSchema, status_code=201)
def add_finding_evidence(
    finding_id: str,
    payload: AddEvidenceRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> EvidenceSchema:
    return service.add_finding_evidence(user_id, finding_id, **payload.model_dump())


@router.get("/hypotheses", response_model=list[HypothesisSchema])
def list_hypotheses(
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
    case_attempt_id: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
) -> list[HypothesisSchema]:
    return service.list_hypotheses(user_id, case_attempt_id=case_attempt_id, project_id=project_id)


@router.post("/hypotheses", response_model=HypothesisSchema, status_code=201)
def create_hypothesis(
    payload: CreateHypothesisRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> HypothesisSchema:
    return service.create_hypothesis(user_id, **payload.model_dump())


@router.patch("/hypotheses/{hypothesis_id}", response_model=HypothesisSchema)
def update_hypothesis(
    hypothesis_id: str,
    payload: UpdateHypothesisRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> HypothesisSchema:
    return service.update_hypothesis(user_id, hypothesis_id, **payload.model_dump(exclude_unset=True))


@router.delete("/hypotheses/{hypothesis_id}", status_code=204)
def delete_hypothesis(
    hypothesis_id: str,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> None:
    service.delete_hypothesis(user_id, hypothesis_id)


@router.post("/hypotheses/{hypothesis_id}/evidence", response_model=EvidenceSchema, status_code=201)
def add_hypothesis_evidence(
    hypothesis_id: str,
    payload: AddEvidenceRequest,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> EvidenceSchema:
    return service.add_hypothesis_evidence(user_id, hypothesis_id, **payload.model_dump())


@router.delete("/evidence/{evidence_id}", status_code=204)
def delete_evidence(
    evidence_id: str,
    user_id: CurrentUserId,
    service: Annotated[FindingService, Depends(get_finding_service)],
) -> None:
    service.delete_evidence(user_id, evidence_id)
