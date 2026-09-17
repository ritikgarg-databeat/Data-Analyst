from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import ResumeSource
from app.schemas.common import ORMSchema


class ResumeEvidenceSchema(ORMSchema):
    id: str
    skill_slug: str
    evidence_text: str
    project_id: str | None
    confidence: float | None


class ResumeReviewSchema(ORMSchema):
    id: str
    quality_score: float
    clarity_score: float | None
    impact_score: float | None
    issues: list[str]
    suggestions: list[str]
    ai_generated: bool
    created_at: datetime


class ResumeVersionSchema(ORMSchema):
    id: str
    version_number: int
    source: ResumeSource
    raw_text: str
    file_name: str | None
    is_current: bool
    created_at: datetime
    evidence: list[ResumeEvidenceSchema] = Field(default_factory=list)
    reviews: list[ResumeReviewSchema] = Field(default_factory=list)


class ResumeVersionListItemSchema(ORMSchema):
    """Lighter row for version-history lists — omits raw_text/evidence/reviews."""

    id: str
    version_number: int
    source: ResumeSource
    file_name: str | None
    is_current: bool
    created_at: datetime


class ResumeSchema(ORMSchema):
    id: str
    title: str
    is_primary: bool
    created_at: datetime
    updated_at: datetime
    versions: list[ResumeVersionListItemSchema] = Field(default_factory=list)


class CreateResumeRequest(BaseModel):
    title: str
    is_primary: bool = False


class UpdateResumeRequest(BaseModel):
    title: str | None = None
    is_primary: bool | None = None


class CreateResumeVersionRequest(BaseModel):
    source: ResumeSource
    raw_text: str
    file_name: str | None = None


class ResumeGapEntrySchema(BaseModel):
    """Resume Gap Analysis row (spec section 13) — a target-role/JD-required
    skill with no supporting ResumeEvidence on the current resume version."""

    skill_slug: str
    has_evidence: bool


class ResumeGapAnalysisResponse(BaseModel):
    resume_version_id: str
    target_role_id: str | None
    gaps: list[ResumeGapEntrySchema]
