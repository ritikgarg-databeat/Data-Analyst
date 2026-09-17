from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.services import get_metrics_service
from app.schemas.metrics import MetricDefinitionSchema
from app.services.metrics_service import MetricsService

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricDefinitionSchema])
def list_metrics(
    service: Annotated[MetricsService, Depends(get_metrics_service)],
    category: str | None = Query(default=None),
    q: str | None = Query(default=None),
) -> list[MetricDefinitionSchema]:
    return service.list_metrics(category=category, q=q)


@router.get("/{id_or_slug}", response_model=MetricDefinitionSchema)
def get_metric(
    id_or_slug: str, service: Annotated[MetricsService, Depends(get_metrics_service)]
) -> MetricDefinitionSchema:
    return service.get(id_or_slug)
