from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.models.dataset import Dataset
from app.models.sql_lab import SqlQueryHistory, SqlTable
from app.sql import registry
from app.sql.engines.base import SqlEngineError, SqlExecutionResult, TablePreview, TableSchema


@dataclass
class TableSummary:
    table_name: str
    grain: str | None
    row_count: int | None
    column_count: int | None


class SqlExecutionService:
    def __init__(self, db: Session, settings: Settings | None = None, user_id: str | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.user_id = user_id

    def list_engines(self) -> list[registry.EngineInfo]:
        return registry.list_engines(self.settings)

    def list_databases(self) -> list[registry.DatabaseInfo]:
        return registry.list_databases(self.db, self.settings, self.user_id)

    def _get_engine(self, engine_name: str, database_name: str):
        try:
            return registry.get_engine(self.db, self.settings, engine_name, database_name, self.user_id)
        except SqlEngineError as exc:
            raise NotFoundError(str(exc)) from exc

    def list_tables(self, engine_name: str, database_name: str) -> list[TableSummary]:
        engine = self._get_engine(engine_name, database_name)

        if engine_name == "duckdb":
            stmt = (
                select(SqlTable)
                .join(Dataset, Dataset.id == SqlTable.dataset_id)
                .where(
                    Dataset.slug == database_name,
                    or_(Dataset.owner_user_id.is_(None), Dataset.owner_user_id == self.user_id),
                )
                .order_by(SqlTable.display_order)
            )
            rows = self.db.execute(stmt).scalars().all()
            return [TableSummary(t.table_name, t.grain, t.row_count, t.column_count) for t in rows]

        return [TableSummary(name, None, None, None) for name in engine.list_tables()]

    def get_table_schema(self, engine_name: str, database_name: str, table_name: str) -> TableSchema:
        engine = self._get_engine(engine_name, database_name)
        try:
            return engine.get_table_schema(table_name)
        except SqlEngineError as exc:
            raise NotFoundError(str(exc)) from exc

    def preview_table(self, engine_name: str, database_name: str, table_name: str) -> TablePreview:
        engine = self._get_engine(engine_name, database_name)
        try:
            return engine.preview_table(table_name, sample_rows=self.settings.sql_lab_preview_row_limit)
        except SqlEngineError as exc:
            raise NotFoundError(str(exc)) from exc

    def execute(
        self, *, user_id: str, engine_name: str, database_name: str, query: str, log_history: bool = True
    ) -> SqlExecutionResult:
        engine = self._get_engine(engine_name, database_name)
        result = engine.execute(
            query,
            timeout_seconds=self.settings.sql_lab_query_timeout_seconds,
            row_limit=self.settings.sql_lab_row_limit,
        )

        if log_history:
            self.db.add(
                SqlQueryHistory(
                    user_id=user_id,
                    engine=engine_name,
                    database=database_name,
                    query=query,
                    status=result.status,
                    row_count=result.row_count if result.is_success else None,
                    execution_time_ms=result.execution_time_ms,
                    error_message=result.error.message if result.error else None,
                )
            )
            self.db.commit()

        return result
