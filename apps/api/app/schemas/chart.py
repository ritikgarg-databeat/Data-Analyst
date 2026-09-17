from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMSchema


class ChartConfig(BaseModel):
    x: str | None = None
    y: str | None = None
    aggregation: str | None = None  # SUM | AVG | COUNT | MIN | MAX | None
    color: str | None = None
    filters: list[dict[str, Any]] = []
    sort: str | None = None  # "x_asc" | "x_desc" | "y_asc" | "y_desc" | None
    bins: int | None = None
    date_granularity: str | None = None  # day|week|month|quarter|year
    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None


class Chart(ORMSchema):
    id: str
    dataset_id: str
    table_name: str
    workspace_id: str | None = None
    title: str
    chart_type: str
    config: ChartConfig
    insight_observation: str | None = None
    insight_why_it_matters: str | None = None
    insight_recommended_action: str | None = None
    created_at: datetime
    updated_at: datetime


class CreateChartRequest(BaseModel):
    dataset_id: str
    table_name: str
    chart_type: str
    title: str
    config: ChartConfig
    workspace_id: str | None = None


class UpdateChartRequest(BaseModel):
    title: str | None = None
    chart_type: str | None = None
    config: ChartConfig | None = None
    insight_observation: str | None = None
    insight_why_it_matters: str | None = None
    insight_recommended_action: str | None = None


class ChartDataResponse(BaseModel):
    """The query result behind a chart, shaped for the frontend to hand
    directly to react-plotly.js — rendering itself always happens client
    side (section 23: "Render using Plotly")."""

    chart_type: str
    x_values: list[Any]
    series: list[dict[str, Any]]  # [{"name": "<color-group-or-y-label>", "y_values": [...]}]
    warnings: list[str]
    recommendation: str | None = None


class RecommendRequest(BaseModel):
    x_type: str  # numeric | categorical | datetime
    y_type: str | None = None


class RecommendResponse(BaseModel):
    chart_type: str
    reason: str
