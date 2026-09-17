from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.services import get_analytics_case_service
from app.schemas.analytics_cases import AnalyticsCaseSchema
from app.services.analytics_case_service import AnalyticsCaseService

router = APIRouter(prefix="/analytics/cases", tags=["analytics-cases"])


@router.get("", response_model=list[AnalyticsCaseSchema])
def list_cases(
    service: Annotated[AnalyticsCaseService, Depends(get_analytics_case_service)],
    domain: str | None = Query(
        default=None, description="Filter by tag substring, e.g. 'business' or 'product'"
    ),
) -> list[AnalyticsCaseSchema]:
    return service.list_cases(domain=domain)


@router.get("/{slug}", response_model=AnalyticsCaseSchema)
def get_case(
    slug: str, service: Annotated[AnalyticsCaseService, Depends(get_analytics_case_service)]
) -> AnalyticsCaseSchema:
    return service.get_case(slug)
