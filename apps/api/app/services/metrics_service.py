"""The Metrics Library (Phase 6, spec section 42) — read-only reference
data seeded from database/seeds/metrics.yaml, analogous to TagService."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.models.metric import MetricDefinition
from app.schemas.metrics import MetricDefinitionSchema


class MetricsService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_metrics(
        self, *, category: str | None = None, q: str | None = None
    ) -> list[MetricDefinitionSchema]:
        stmt = select(MetricDefinition).order_by(MetricDefinition.display_order, MetricDefinition.name)
        if category:
            stmt = stmt.where(MetricDefinition.category == category)
        rows = list(self.db.execute(stmt).scalars().all())
        if q:
            needle = q.strip().lower()
            rows = [
                m
                for m in rows
                if needle in m.name.lower() or needle in m.slug.lower() or needle in m.definition.lower()
            ]
        return [MetricDefinitionSchema.model_validate(m) for m in rows]

    def get(self, id_or_slug: str) -> MetricDefinitionSchema:
        metric = self.db.get(MetricDefinition, id_or_slug)
        if metric is None:
            metric = self.db.execute(
                select(MetricDefinition).where(MetricDefinition.slug == id_or_slug)
            ).scalar_one_or_none()
        if metric is None:
            raise NotFoundError(f"Metric '{id_or_slug}' was not found.", details={"id_or_slug": id_or_slug})
        return MetricDefinitionSchema.model_validate(metric)
