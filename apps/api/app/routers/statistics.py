from typing import Annotated

from fastapi import APIRouter, Depends

from app.dependencies.services import get_statistics_service
from app.schemas.statistics import (
    CorrelationRequest,
    RegressionRequest,
    RegressionResponse,
    StatTestRequest,
    SummaryStatsRequest,
    SummaryStatsResponse,
    TestResultResponse,
)
from app.services.statistics_service import StatisticsService

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.post("/summary", response_model=SummaryStatsResponse)
def summary(
    payload: SummaryStatsRequest, service: Annotated[StatisticsService, Depends(get_statistics_service)]
) -> SummaryStatsResponse:
    return service.summary(payload)


@router.post("/test", response_model=TestResultResponse)
def run_test(
    payload: StatTestRequest, service: Annotated[StatisticsService, Depends(get_statistics_service)]
) -> TestResultResponse:
    return service.run_test(payload)


@router.post("/correlation", response_model=TestResultResponse)
def correlation(
    payload: CorrelationRequest, service: Annotated[StatisticsService, Depends(get_statistics_service)]
) -> TestResultResponse:
    return service.correlation(payload)


@router.post("/regression", response_model=RegressionResponse)
def regression(
    payload: RegressionRequest, service: Annotated[StatisticsService, Depends(get_statistics_service)]
) -> RegressionResponse:
    return service.regression(payload)
