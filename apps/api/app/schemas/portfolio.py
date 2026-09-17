from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import PortfolioItemType, PrivacyLevel
from app.schemas.common import ORMSchema


class PortfolioItemSchema(ORMSchema):
    id: str
    item_type: PortfolioItemType
    ref_id: str | None
    title: str
    description: str | None
    privacy: PrivacyLevel
    display_order: int
    created_at: datetime
    updated_at: datetime


class PortfolioSchema(ORMSchema):
    id: str
    headline: str | None
    about: str | None
    is_public_ready: bool
    created_at: datetime
    updated_at: datetime
    items: list[PortfolioItemSchema] = Field(default_factory=list)


class UpdatePortfolioRequest(BaseModel):
    headline: str | None = None
    about: str | None = None
    is_public_ready: bool | None = None


class CreatePortfolioItemRequest(BaseModel):
    item_type: PortfolioItemType
    ref_id: str | None = None
    title: str
    description: str | None = None
    privacy: PrivacyLevel = PrivacyLevel.PRIVATE


class UpdatePortfolioItemRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    privacy: PrivacyLevel | None = None
    display_order: int | None = None


class PortfolioQualityScoreResponse(BaseModel):
    """A deterministic heuristic score (spec section 21) — completeness/
    description quality/privacy readiness — never an AI-generated number.
    AI (PORTFOLIO_REVIEW) only narrates around this, never replaces it."""

    score: float
    item_count: int
    items_with_description: int
    portfolio_ready_item_count: int
    suggestions: list[str] = Field(default_factory=list)


class PortfolioGapSuggestionSchema(BaseModel):
    """Portfolio Gap Detection (spec section 36) — a target-role-required
    skill with no PROJECT/CASE_STUDY portfolio item evidencing it."""

    skill_slug: str
    recommended_project_template_slugs: list[str] = Field(default_factory=list)
