"""DB-aware orchestration for the Data Quality Lab: CRUD over DataQualityRule
plus real rule execution (translate -> run via DuckDB -> persist a
DataQualityRun), mirroring app/sql/service.py's shape."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import NotFoundError
from app.data_quality.engine import DataQualityRuleError, build_check_sql, interpret_result
from app.models.data_quality import DataQualityRule, DataQualityRun
from app.models.dataset import Dataset
from app.models.enums import DataQualityStatus
from app.sql import registry
from app.sql.engines.base import SqlEngineError


class DataQualityService:
    def __init__(self, db: Session, settings: Settings | None = None, user_id: str | None = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.user_id = user_id

    def _find_dataset(self, dataset_id: str) -> Dataset:
        dataset = self.db.scalar(
            select(Dataset).where(
                Dataset.id == dataset_id,
                or_(Dataset.owner_user_id.is_(None), Dataset.owner_user_id == self.user_id),
            )
        )
        if dataset is None:
            raise NotFoundError(f"Dataset '{dataset_id}' not found.")
        return dataset

    # --- Rule CRUD -------------------------------------------------------

    def list_rules(self, user_id: str, dataset_id: str | None = None) -> list[DataQualityRule]:
        stmt = select(DataQualityRule).where(DataQualityRule.user_id == user_id)
        if dataset_id:
            stmt = stmt.where(DataQualityRule.dataset_id == dataset_id)
        stmt = stmt.order_by(DataQualityRule.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def get_rule(self, user_id: str, rule_id: str) -> DataQualityRule:
        rule = self.db.get(DataQualityRule, rule_id)
        if rule is None or rule.user_id != user_id:
            raise NotFoundError(f"Data quality rule '{rule_id}' not found.")
        return rule

    def create_rule(
        self,
        user_id: str,
        *,
        dataset_id: str,
        table_name: str,
        column_name: str | None,
        rule_type,
        config: dict,
        name: str | None,
    ) -> DataQualityRule:
        self._find_dataset(dataset_id)
        rule = DataQualityRule(
            user_id=user_id,
            dataset_id=dataset_id,
            table_name=table_name,
            column_name=column_name,
            rule_type=rule_type,
            config=config,
            name=name,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, user_id: str, rule_id: str) -> None:
        rule = self.get_rule(user_id, rule_id)
        self.db.delete(rule)
        self.db.commit()

    # --- Execution --------------------------------------------------------

    def run_rule(self, user_id: str, rule_id: str) -> DataQualityRun:
        rule = self.get_rule(user_id, rule_id)
        dataset = self._find_dataset(rule.dataset_id)

        try:
            sql = build_check_sql(
                rule.rule_type, table_name=rule.table_name, column_name=rule.column_name, config=rule.config
            )
        except DataQualityRuleError as exc:
            return self._save_run(
                rule,
                DataQualityStatus.ERROR,
                expected_value=None,
                actual_value=None,
                details={"error": str(exc)},
            )

        try:
            engine = registry.get_engine(self.db, self.settings, "duckdb", dataset.slug, user_id=self.user_id)
        except SqlEngineError as exc:
            return self._save_run(
                rule,
                DataQualityStatus.ERROR,
                expected_value=None,
                actual_value=None,
                details={"error": str(exc)},
            )

        result = engine.execute(
            sql,
            timeout_seconds=self.settings.sql_lab_query_timeout_seconds,
            row_limit=1,
        )
        if not result.is_success:
            message = result.error.message if result.error else "Query failed."
            return self._save_run(
                rule,
                DataQualityStatus.ERROR,
                expected_value=None,
                actual_value=None,
                details={"error": message},
            )

        value = result.rows[0][0] if result.rows else None
        outcome = interpret_result(rule.rule_type, rule.config, value)
        return self._save_run(
            rule,
            outcome.status,
            expected_value=outcome.expected_value,
            actual_value=outcome.actual_value,
            details=outcome.details,
        )

    def _save_run(
        self,
        rule: DataQualityRule,
        status: DataQualityStatus,
        *,
        expected_value: str | None,
        actual_value: str | None,
        details: dict,
    ) -> DataQualityRun:
        run = DataQualityRun(
            rule_id=rule.id,
            status=status,
            expected_value=expected_value,
            actual_value=actual_value,
            details=details,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, user_id: str, rule_id: str, limit: int = 20) -> list[DataQualityRun]:
        self.get_rule(user_id, rule_id)  # ownership check
        stmt = (
            select(DataQualityRun)
            .where(DataQualityRun.rule_id == rule_id)
            .order_by(DataQualityRun.executed_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())
