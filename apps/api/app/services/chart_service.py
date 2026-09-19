"""Saved charts + the chart-data query, recommendation, and mistake-detector
endpoints (sections 22-27 of the Phase 5 spec)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.dataset_hub import chart_engine
from app.models.chart import Chart as ChartModel
from app.models.dataset import Dataset, DatasetTable
from app.models.dataset_profile import DatasetColumnProfile, DatasetProfile
from app.models.eda import EdaWorkspace
from app.repositories.dataset import DatasetRepository
from app.schemas.chart import (
    Chart as ChartSchema,
)
from app.schemas.chart import (
    ChartConfig,
    ChartDataResponse,
    CreateChartRequest,
    RecommendResponse,
    UpdateChartRequest,
)
from app.sql.paths import resolve_repo_path


class ChartService:
    def __init__(self, db: Session, user_id: str | None = None) -> None:
        self.db = db
        self.dataset_repo = DatasetRepository(db)
        self.user_id = user_id

    def _find_dataset(self, id_or_slug: str) -> Dataset:
        dataset = self.dataset_repo.get_by_id(id_or_slug) or self.dataset_repo.get_by_slug(id_or_slug)
        if dataset is None or (
            self.user_id is not None
            and dataset.owner_user_id is not None
            and dataset.owner_user_id != self.user_id
        ):
            raise NotFoundError(f"Dataset '{id_or_slug}' was not found.")
        return dataset

    def _find_table(self, dataset: Dataset, table_name: str) -> DatasetTable:
        for table in dataset.tables:
            if table.table_name == table_name:
                return table
        raise NotFoundError(f"Table '{table_name}' was not found in dataset '{dataset.slug}'.")

    def _column_types(self, dataset_id: str, table_name: str) -> dict[str, str]:
        stmt = (
            select(DatasetColumnProfile)
            .join(DatasetProfile, DatasetProfile.id == DatasetColumnProfile.profile_id)
            .where(DatasetProfile.dataset_id == dataset_id, DatasetProfile.table_name == table_name)
            .order_by(DatasetProfile.generated_at.desc())
        )
        columns = self.db.execute(stmt).scalars().all()
        return {c.column_name: c.data_type for c in columns}

    def _to_schema(self, chart: ChartModel) -> ChartSchema:
        return ChartSchema(
            id=chart.id,
            dataset_id=chart.dataset_id,
            table_name=chart.table_name,
            workspace_id=chart.workspace_id,
            title=chart.title,
            chart_type=chart.chart_type,
            config=ChartConfig(**chart.config),
            insight_observation=chart.insight_observation,
            insight_why_it_matters=chart.insight_why_it_matters,
            insight_recommended_action=chart.insight_recommended_action,
            created_at=chart.created_at,
            updated_at=chart.updated_at,
        )

    def list_charts(self, user_id: str, dataset_id: str | None = None) -> list[ChartSchema]:
        stmt = select(ChartModel).where(ChartModel.user_id == user_id)
        if dataset_id:
            dataset = self._find_dataset(dataset_id)
            stmt = stmt.where(ChartModel.dataset_id == dataset.id)
        stmt = stmt.order_by(ChartModel.updated_at.desc())
        return [self._to_schema(c) for c in self.db.execute(stmt).scalars().all()]

    def create(self, user_id: str, payload: CreateChartRequest) -> ChartSchema:
        dataset = self._find_dataset(payload.dataset_id)
        self._find_table(dataset, payload.table_name)
        if payload.workspace_id is not None:
            workspace = self.db.get(EdaWorkspace, payload.workspace_id)
            if workspace is None or workspace.user_id != user_id or workspace.dataset_id != dataset.id:
                raise NotFoundError(f"EDA workspace '{payload.workspace_id}' was not found.")
        chart = ChartModel(
            user_id=user_id,
            dataset_id=dataset.id,
            table_name=payload.table_name,
            workspace_id=payload.workspace_id,
            title=payload.title,
            chart_type=payload.chart_type,
            config=payload.config.model_dump(),
        )
        self.db.add(chart)
        self.db.commit()
        self.db.refresh(chart)
        return self._to_schema(chart)

    def _find(self, user_id: str, chart_id: str) -> ChartModel:
        chart = self.db.get(ChartModel, chart_id)
        if chart is None or chart.user_id != user_id:
            raise NotFoundError(f"Chart '{chart_id}' was not found.")
        return chart

    def get(self, user_id: str, chart_id: str) -> ChartSchema:
        return self._to_schema(self._find(user_id, chart_id))

    def update(self, user_id: str, chart_id: str, payload: UpdateChartRequest) -> ChartSchema:
        chart = self._find(user_id, chart_id)
        if payload.title is not None:
            chart.title = payload.title
        if payload.chart_type is not None:
            chart.chart_type = payload.chart_type
        if payload.config is not None:
            chart.config = payload.config.model_dump()
        if payload.insight_observation is not None:
            chart.insight_observation = payload.insight_observation
        if payload.insight_why_it_matters is not None:
            chart.insight_why_it_matters = payload.insight_why_it_matters
        if payload.insight_recommended_action is not None:
            chart.insight_recommended_action = payload.insight_recommended_action
        self.db.commit()
        self.db.refresh(chart)
        return self._to_schema(chart)

    def delete(self, user_id: str, chart_id: str) -> None:
        chart = self._find(user_id, chart_id)
        self.db.delete(chart)
        self.db.commit()

    def get_data(self, user_id: str, chart_id: str) -> ChartDataResponse:
        chart = self._find(user_id, chart_id)
        dataset = self._find_dataset(chart.dataset_id)
        table = self._find_table(dataset, chart.table_name)
        column_types = self._column_types(dataset.id, table.table_name)

        for field in ("x", "y", "color"):
            value = chart.config.get(field)
            if value and value not in column_types:
                raise AppError(f"Column '{value}' was not found on table '{table.table_name}'.")

        result = chart_engine.build_chart_data(
            resolve_repo_path(table.file_path), chart.chart_type, chart.config
        )

        category_count = len(result["x_values"])
        series_count = len(result["series"])
        warnings = chart_engine.detect_mistakes(
            chart.chart_type,
            category_count=category_count,
            series_count=series_count,
            has_title_or_labels=bool(
                chart.title or chart.config.get("x_label") or chart.config.get("y_label")
            ),
            sorted_bars=bool(chart.config.get("sort")),
        )

        x_type = column_types.get(chart.config.get("x"), "categorical")
        y_type = column_types.get(chart.config.get("y")) if chart.config.get("y") else None
        recommended_type, reason = chart_engine.recommend_chart_type(x_type, y_type)
        recommendation = reason if recommended_type != chart.chart_type else None

        return ChartDataResponse(
            chart_type=chart.chart_type,
            x_values=result["x_values"],
            series=result["series"],
            warnings=warnings,
            recommendation=recommendation,
        )

    def recommend(self, x_type: str, y_type: str | None) -> RecommendResponse:
        chart_type, reason = chart_engine.recommend_chart_type(x_type, y_type)
        return RecommendResponse(chart_type=chart_type, reason=reason)
