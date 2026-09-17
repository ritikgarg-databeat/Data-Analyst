from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.enums import DatasetSourceType, DatasetStatus, DifficultyLevel
from app.schemas.common import ORMSchema


class DatasetTableSchema(ORMSchema):
    id: str
    table_name: str
    file_format: str
    row_count: int | None = None
    column_count: int | None = None
    size_bytes: int | None = None
    grain: str | None = None
    display_order: int


class Dataset(ORMSchema):
    id: str
    name: str
    slug: str
    description: str | None = None
    source: str | None = None
    source_url: str | None = None
    domain: str | None = None
    file_path: str | None = None
    file_format: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    difficulty: DifficultyLevel
    metadata_: dict[str, Any] | None = Field(
        default=None, alias="metadata", validation_alias="dataset_metadata"
    )
    created_at: datetime
    updated_at: datetime

    # --- Phase 5 ---
    source_type: DatasetSourceType
    business_domain: str | None = None
    license: str | None = None
    size_bytes: int | None = None
    status: DatasetStatus
    status_message: str | None = None
    fingerprint: str | None = None
    version: int
    imported_at: datetime | None = None
    last_profiled_at: datetime | None = None
    kaggle_ref: str | None = None
    tags: list[str] = Field(default_factory=list)
    tables: list[DatasetTableSchema] = Field(default_factory=list)
    # Computed, not stored — used by the Dataset Hub catalog cards (section 2
    # of the Phase 5 spec: "SQL Ready" / "Python Ready" badges). Both the
    # list and detail views return this same `Dataset` shape (matching this
    # codebase's convention elsewhere — no separate list/detail DTOs).
    sql_ready: bool = False
    python_ready: bool = False


# --- Import -----------------------------------------------------------


class LocalImportForm(BaseModel):
    """The non-file fields of a multipart /datasets/import request."""

    name: str
    description: str | None = None
    business_domain: str | None = None
    difficulty: DifficultyLevel = DifficultyLevel.BEGINNER
    tags: list[str] = Field(default_factory=list)


class ReimportResponse(BaseModel):
    dataset: Dataset
    version_changed: bool


# --- Schema viewer ------------------------------------------------------


class SchemaColumnSchema(BaseModel):
    column_name: str
    inferred_sql_type: str
    data_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float


class TableSchemaResponse(BaseModel):
    table_name: str
    columns: list[SchemaColumnSchema]
    row_count: int
    generated_at: datetime


# --- Profiling ------------------------------------------------------


class ColumnProfileSchema(BaseModel):
    column_name: str
    data_type: str
    inferred_sql_type: str
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    min_value: str | None = None
    max_value: str | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None
    quantiles: dict[str, float | None] | None = None
    zero_count: int | None = None
    negative_count: int | None = None
    outlier_count: int | None = None
    outlier_method: str | None = None
    top_values: list[dict[str, Any]] | None = None
    sample_values: list[Any] | None = None
    min_length: int | None = None
    max_length: int | None = None
    avg_length: float | None = None
    extra: dict[str, Any] | None = None


class TableProfileSchema(BaseModel):
    table_name: str
    row_count: int
    column_count: int
    size_bytes: int | None = None
    duplicate_row_count: int
    generated_at: datetime
    columns: list[ColumnProfileSchema]


class DatasetProfileResponse(BaseModel):
    dataset_id: str
    tables: list[TableProfileSchema]


# --- Quality ------------------------------------------------------


class QualityIssueSchema(BaseModel):
    type: str
    detail: str
    severity: str
    column: str | None = None


class QualityReportSchema(BaseModel):
    table_name: str
    overall_score: float
    completeness_score: float
    uniqueness_score: float
    validity_score: float
    consistency_score: float
    duplicate_row_count: int
    issues: list[QualityIssueSchema]
    methodology: str
    generated_at: datetime


class DatasetQualityResponse(BaseModel):
    dataset_id: str
    tables: list[QualityReportSchema]


# --- Duplicates / outliers ------------------------------------------------


class DuplicatesResponse(BaseModel):
    table_name: str
    duplicate_row_count: int
    sample_rows: list[list[Any]]
    columns: list[str]


class OutliersResponse(BaseModel):
    table_name: str
    column_name: str
    method: str
    outlier_count: int
    lower_bound: float | None
    upper_bound: float | None
    sample_rows: list[list[Any]]
    columns: list[str]


# --- Relationships ------------------------------------------------


class DatasetRelationshipSchema(ORMSchema):
    id: str
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str


class CreateRelationshipRequest(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    relationship_type: str = "one_to_many"


# --- Notes ------------------------------------------------


class DatasetNoteSchema(ORMSchema):
    id: str
    table_name: str | None = None
    column_name: str | None = None
    body: str
    created_at: datetime
    updated_at: datetime


class CreateNoteRequest(BaseModel):
    body: str
    table_name: str | None = None
    column_name: str | None = None


# --- Versions ------------------------------------------------


class DatasetVersionSchema(ORMSchema):
    id: str
    version: int
    fingerprint: str
    row_count: int | None = None
    column_count: int | None = None
    size_bytes: int | None = None
    change_summary: str | None = None
    created_at: datetime


# --- Usage ------------------------------------------------


class DatasetUsageSchema(BaseModel):
    sql_exercises: int
    python_exercises: int
    other_exercises: int
    eda_workspaces: int
    charts: int
    projects: int


# --- Analysis explorers ------------------------------------------------


class CorrelationResponse(BaseModel):
    table_name: str
    method: str  # pearson | spearman
    columns: list[str]
    matrix: list[list[float | None]]
    note: str = "Correlation does not imply causation."


class DistributionResponse(BaseModel):
    table_name: str
    column_name: str
    bins: list[dict[str, Any]]  # [{"bin_start":..,"bin_end":..,"count":..}]
    mean: float | None
    median: float | None
    std_dev: float | None
    quantiles: dict[str, float] | None
    skewness: float | None


class TimeSeriesPoint(BaseModel):
    period: str
    value: float | None
    rolling_avg: float | None = None


class TimeSeriesResponse(BaseModel):
    table_name: str
    date_column: str
    metric_column: str
    aggregation: str
    granularity: str
    points: list[TimeSeriesPoint]


# --- Product analytics (Phase 6) --------------------------------------


class FunnelStepSchema(BaseModel):
    step: str
    users: int
    conversion_from_previous: float
    conversion_from_start: float
    drop_off: int


class FunnelResponse(BaseModel):
    table_name: str
    steps: list[FunnelStepSchema]
    methodology: str = (
        "A user 'reaches' a step if they have a matching event at any time (an unordered/"
        "'ever completed' funnel) — not necessarily in strict chronological step order."
    )


class CohortRowSchema(BaseModel):
    cohort: str
    cohort_size: int
    retention_pct: list[float | None]


class CohortRetentionResponse(BaseModel):
    table_name: str
    granularity: str
    periods: int
    cohorts: list[CohortRowSchema]


class RawColumnSchema(BaseModel):
    column_name: str
    sql_type: str


class RawSchemaResponse(BaseModel):
    """Column names straight from DuckDB DESCRIBE — unlike `TableSchemaResponse`,
    this never depends on a `DatasetProfile` existing, so it also works for
    datasets registered as plain SQL Lab databases (SqlTable-only, e.g.
    "ecommerce"/"saas-product") that the EDA pipeline never profiled."""

    table_name: str
    columns: list[RawColumnSchema]
