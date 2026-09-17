from datetime import datetime

from pydantic import BaseModel

from app.models.enums import EvidenceType, FindingConfidence, HypothesisStatus
from app.schemas.common import ORMSchema


class EvidenceSchema(ORMSchema):
    id: str
    evidence_type: EvidenceType
    ref_id: str | None
    label: str
    snapshot: str | None
    created_at: datetime


class AddEvidenceRequest(BaseModel):
    evidence_type: EvidenceType
    ref_id: str | None = None
    label: str
    snapshot: str | None = None


class FindingSchema(ORMSchema):
    id: str
    case_attempt_id: str | None
    project_id: str | None
    observation: str
    evidence_text: str | None
    impact: str | None
    confidence: FindingConfidence | None
    related_analysis: str | None
    display_order: int
    created_at: datetime
    evidence: list[EvidenceSchema] = []


class CreateFindingRequest(BaseModel):
    case_attempt_id: str | None = None
    project_id: str | None = None
    observation: str
    evidence_text: str | None = None
    impact: str | None = None
    confidence: FindingConfidence | None = None
    related_analysis: str | None = None


class UpdateFindingRequest(BaseModel):
    observation: str | None = None
    evidence_text: str | None = None
    impact: str | None = None
    confidence: FindingConfidence | None = None
    related_analysis: str | None = None


class HypothesisSchema(ORMSchema):
    id: str
    case_attempt_id: str | None
    project_id: str | None
    statement: str
    status: HypothesisStatus
    evidence_text: str | None
    display_order: int
    created_at: datetime
    evidence: list[EvidenceSchema] = []


class CreateHypothesisRequest(BaseModel):
    case_attempt_id: str | None = None
    project_id: str | None = None
    statement: str


class UpdateHypothesisRequest(BaseModel):
    statement: str | None = None
    status: HypothesisStatus | None = None
    evidence_text: str | None = None
