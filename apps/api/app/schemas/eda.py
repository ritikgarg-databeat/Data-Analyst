from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ORMSchema


class EdaFindingSchema(ORMSchema):
    id: str
    observation: str
    evidence: str | None = None
    business_implication: str | None = None
    recommended_action: str | None = None
    created_at: datetime


class CreateFindingRequest(BaseModel):
    observation: str
    evidence: str | None = None
    business_implication: str | None = None
    recommended_action: str | None = None


class EdaWorkspaceSchema(ORMSchema):
    id: str
    dataset_id: str
    name: str
    table_name: str | None = None
    state: dict[str, Any] | None = None
    overview: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
    findings: list[EdaFindingSchema] = Field(default_factory=list)


class CreateEdaWorkspaceRequest(BaseModel):
    dataset_id: str
    name: str
    table_name: str | None = None


class UpdateEdaWorkspaceRequest(BaseModel):
    name: str | None = None
    table_name: str | None = None
    state: dict[str, Any] | None = None


# --- Automatic EDA overview ------------------------------------------------


class MissingnessEntry(BaseModel):
    column: str
    null_percentage: float


class DistributionSummary(BaseModel):
    column: str
    mean: float | None
    median: float | None
    std_dev: float | None
    quantiles: dict[str, float] | None


class CategoricalSummary(BaseModel):
    column: str
    top_values: list[dict[str, Any]]


class CorrelationPair(BaseModel):
    column_a: str
    column_b: str
    correlation: float


class DateTrendSummary(BaseModel):
    column: str
    min_date: str | None
    max_date: str | None
    missing_calendar_days: int | None


class OutlierSummary(BaseModel):
    column: str
    outlier_count: int
    method: str


class EdaOverview(BaseModel):
    table_name: str
    row_count: int
    column_count: int
    duplicate_row_count: int
    missingness: list[MissingnessEntry]
    distributions: list[DistributionSummary]
    categorical_summaries: list[CategoricalSummary]
    correlations: list[CorrelationPair]
    date_trends: list[DateTrendSummary]
    outliers: list[OutlierSummary]
    generated_at: datetime


class EdaQuestion(BaseModel):
    question: str
    category: str  # e.g. "revenue", "distribution", "trend", "segmentation", "correlation"
