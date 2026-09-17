from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_dataset_analysis_service, get_dataset_service
from app.models.enums import DifficultyLevel
from app.schemas.dataset import (
    CohortRetentionResponse,
    CorrelationResponse,
    CreateNoteRequest,
    CreateRelationshipRequest,
    Dataset,
    DatasetNoteSchema,
    DatasetProfileResponse,
    DatasetQualityResponse,
    DatasetRelationshipSchema,
    DatasetUsageSchema,
    DatasetVersionSchema,
    DistributionResponse,
    DuplicatesResponse,
    FunnelResponse,
    LocalImportForm,
    OutliersResponse,
    RawSchemaResponse,
    TableSchemaResponse,
    TimeSeriesResponse,
)
from app.services.dataset_analysis_service import DatasetAnalysisService
from app.services.dataset_service import DatasetFilters, DatasetService

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("", response_model=list[Dataset])
def list_datasets(
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    q: str | None = Query(default=None),
    business_domain: str | None = Query(default=None),
    source_type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    tag: str | None = Query(default=None),
) -> list[Dataset]:
    return service.list_datasets(
        DatasetFilters(q=q, business_domain=business_domain, source_type=source_type, status=status, tag=tag)
    )


@router.post("/import", response_model=Dataset, status_code=201)
async def import_local_dataset(
    background_tasks: BackgroundTasks,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    files: list[UploadFile] = File(...),
    name: str = Form(...),
    description: str | None = Form(default=None),
    business_domain: str | None = Form(default=None),
    difficulty: DifficultyLevel = Form(default=DifficultyLevel.BEGINNER),
    tags: str = Form(default=""),
) -> Dataset:
    """Accepts one or more files in a single multipart request — more than
    one file is treated as a dataset collection (section 6/7 of the Phase 5
    spec), e.g. an ecommerce/ folder's customers.csv + orders.csv +
    products.csv uploaded together."""
    form = LocalImportForm(
        name=name,
        description=description,
        business_domain=business_domain,
        difficulty=difficulty,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    return service.start_local_import(files, form, background_tasks)


@router.get("/{id_or_slug}", response_model=Dataset)
def get_dataset(id_or_slug: str, service: Annotated[DatasetService, Depends(get_dataset_service)]) -> Dataset:
    return service.get(id_or_slug)


@router.post("/{id_or_slug}/reimport", response_model=Dataset)
async def reimport_dataset(
    id_or_slug: str,
    background_tasks: BackgroundTasks,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
    files: list[UploadFile] = File(...),
) -> Dataset:
    return service.reimport(id_or_slug, files, background_tasks)


@router.post("/{id_or_slug}/profile", response_model=Dataset)
def trigger_reprofile(
    id_or_slug: str,
    background_tasks: BackgroundTasks,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> Dataset:
    return service.trigger_reprofile(id_or_slug, background_tasks)


@router.get("/{id_or_slug}/profile", response_model=DatasetProfileResponse)
def get_profile(
    id_or_slug: str, service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)]
) -> DatasetProfileResponse:
    return service.get_profile(id_or_slug)


@router.get("/{id_or_slug}/schema", response_model=list[TableSchemaResponse])
def get_schema(
    id_or_slug: str,
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
) -> list[TableSchemaResponse]:
    return service.get_schema(id_or_slug, table)


@router.get("/{id_or_slug}/quality", response_model=DatasetQualityResponse)
def get_quality(
    id_or_slug: str, service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)]
) -> DatasetQualityResponse:
    return service.get_quality(id_or_slug)


@router.get("/{id_or_slug}/duplicates", response_model=DuplicatesResponse)
def get_duplicates(
    id_or_slug: str,
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
) -> DuplicatesResponse:
    return service.get_duplicates(id_or_slug, table, limit)


@router.get("/{id_or_slug}/outliers", response_model=OutliersResponse)
def get_outliers(
    id_or_slug: str,
    column: Annotated[str, Query()],
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=200),
) -> OutliersResponse:
    return service.get_outliers(id_or_slug, table, column, limit)


@router.get("/{id_or_slug}/relationships", response_model=list[DatasetRelationshipSchema])
def list_relationships(
    id_or_slug: str, service: Annotated[DatasetService, Depends(get_dataset_service)]
) -> list[DatasetRelationshipSchema]:
    return service.list_relationships(id_or_slug)


@router.post("/{id_or_slug}/relationships", response_model=DatasetRelationshipSchema, status_code=201)
def add_relationship(
    id_or_slug: str,
    payload: CreateRelationshipRequest,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetRelationshipSchema:
    return service.add_relationship(id_or_slug, payload)


@router.delete("/{id_or_slug}/relationships/{relationship_id}", status_code=204)
def delete_relationship(
    id_or_slug: str, relationship_id: str, service: Annotated[DatasetService, Depends(get_dataset_service)]
) -> None:
    service.delete_relationship(id_or_slug, relationship_id)


@router.get("/{id_or_slug}/notes", response_model=list[DatasetNoteSchema])
def list_notes(
    id_or_slug: str, service: Annotated[DatasetService, Depends(get_dataset_service)]
) -> list[DatasetNoteSchema]:
    return service.list_notes(id_or_slug)


@router.post("/{id_or_slug}/notes", response_model=DatasetNoteSchema, status_code=201)
def add_note(
    id_or_slug: str,
    payload: CreateNoteRequest,
    user_id: CurrentUserId,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> DatasetNoteSchema:
    return service.add_note(id_or_slug, user_id, payload)


@router.delete("/{id_or_slug}/notes/{note_id}", status_code=204)
def delete_note(
    id_or_slug: str,
    note_id: str,
    user_id: CurrentUserId,
    service: Annotated[DatasetService, Depends(get_dataset_service)],
) -> None:
    service.delete_note(id_or_slug, note_id, user_id)


@router.get("/{id_or_slug}/versions", response_model=list[DatasetVersionSchema])
def list_versions(
    id_or_slug: str, service: Annotated[DatasetService, Depends(get_dataset_service)]
) -> list[DatasetVersionSchema]:
    return service.list_versions(id_or_slug)


@router.get("/{id_or_slug}/usage", response_model=DatasetUsageSchema)
def get_usage(
    id_or_slug: str, service: Annotated[DatasetService, Depends(get_dataset_service)]
) -> DatasetUsageSchema:
    return service.get_usage(id_or_slug)


@router.get("/{id_or_slug}/analysis/correlation", response_model=CorrelationResponse)
def get_correlation(
    id_or_slug: str,
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    columns: str | None = Query(default=None, description="Comma-separated numeric column names"),
    method: str = Query(default="pearson"),
) -> CorrelationResponse:
    column_list = [c.strip() for c in columns.split(",") if c.strip()] if columns else None
    return service.get_correlation(id_or_slug, table, column_list, method)


@router.get("/{id_or_slug}/analysis/distribution", response_model=DistributionResponse)
def get_distribution(
    id_or_slug: str,
    column: Annotated[str, Query()],
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    bins: int = Query(default=20, ge=1, le=200),
) -> DistributionResponse:
    return service.get_distribution(id_or_slug, table, column, bins)


@router.get("/{id_or_slug}/analysis/timeseries", response_model=TimeSeriesResponse)
def get_time_series(
    id_or_slug: str,
    date_column: Annotated[str, Query()],
    metric_column: Annotated[str, Query()],
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    aggregation: str = Query(default="SUM"),
    granularity: str = Query(default="month"),
) -> TimeSeriesResponse:
    return service.get_time_series(id_or_slug, table, date_column, metric_column, aggregation, granularity)


@router.get("/{id_or_slug}/analysis/raw-schema", response_model=RawSchemaResponse)
def get_raw_schema(
    id_or_slug: str,
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
) -> RawSchemaResponse:
    return service.get_raw_schema(id_or_slug, table)


@router.get("/{id_or_slug}/analysis/funnel", response_model=FunnelResponse)
def get_funnel(
    id_or_slug: str,
    user_col: Annotated[str, Query()],
    event_col: Annotated[str, Query()],
    steps: Annotated[str, Query(description="Comma-separated event names, in funnel order")],
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
) -> FunnelResponse:
    step_list = [s.strip() for s in steps.split(",") if s.strip()]
    return service.get_funnel(id_or_slug, table, user_col, event_col, step_list)


@router.get("/{id_or_slug}/analysis/cohort-retention", response_model=CohortRetentionResponse)
def get_cohort_retention(
    id_or_slug: str,
    user_col: Annotated[str, Query()],
    cohort_date_col: Annotated[str, Query()],
    activity_date_col: Annotated[str, Query()],
    service: Annotated[DatasetAnalysisService, Depends(get_dataset_analysis_service)],
    table: str | None = Query(default=None),
    granularity: str = Query(default="month"),
    periods: int = Query(default=6, ge=1, le=24),
) -> CohortRetentionResponse:
    return service.get_cohort_retention(
        id_or_slug, table, user_col, cohort_date_col, activity_date_col, granularity, periods
    )
