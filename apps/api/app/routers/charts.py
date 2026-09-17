from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.dependencies.current_user import CurrentUserId
from app.dependencies.services import get_chart_service
from app.schemas.chart import (
    Chart,
    ChartDataResponse,
    CreateChartRequest,
    RecommendRequest,
    RecommendResponse,
    UpdateChartRequest,
)
from app.services.chart_service import ChartService

router = APIRouter(prefix="/charts", tags=["charts"])


@router.get("", response_model=list[Chart])
def list_charts(
    user_id: CurrentUserId,
    service: Annotated[ChartService, Depends(get_chart_service)],
    dataset_id: str | None = Query(default=None),
) -> list[Chart]:
    return service.list_charts(user_id, dataset_id)


@router.post("/recommend", response_model=RecommendResponse)
def recommend(
    payload: RecommendRequest, service: Annotated[ChartService, Depends(get_chart_service)]
) -> RecommendResponse:
    return service.recommend(payload.x_type, payload.y_type)


@router.post("", response_model=Chart, status_code=201)
def create_chart(
    payload: CreateChartRequest,
    user_id: CurrentUserId,
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> Chart:
    return service.create(user_id, payload)


@router.get("/{chart_id}", response_model=Chart)
def get_chart(
    chart_id: str, user_id: CurrentUserId, service: Annotated[ChartService, Depends(get_chart_service)]
) -> Chart:
    return service.get(user_id, chart_id)


@router.patch("/{chart_id}", response_model=Chart)
def update_chart(
    chart_id: str,
    payload: UpdateChartRequest,
    user_id: CurrentUserId,
    service: Annotated[ChartService, Depends(get_chart_service)],
) -> Chart:
    return service.update(user_id, chart_id, payload)


@router.delete("/{chart_id}", status_code=204)
def delete_chart(
    chart_id: str, user_id: CurrentUserId, service: Annotated[ChartService, Depends(get_chart_service)]
) -> None:
    service.delete(user_id, chart_id)


@router.get("/{chart_id}/data", response_model=ChartDataResponse)
def get_chart_data(
    chart_id: str, user_id: CurrentUserId, service: Annotated[ChartService, Depends(get_chart_service)]
) -> ChartDataResponse:
    return service.get_data(user_id, chart_id)
