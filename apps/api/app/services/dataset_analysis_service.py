"""Read-heavy Dataset Hub endpoints backed directly by DuckDB against a
DatasetTable's canonical Parquet file: schema, profile, quality,
duplicates, outliers, and the correlation/distribution/time-series
explorers. Kept separate from `DatasetService` (catalog/import/CRUD) the
same way `app/sql/service.py` (execution) is kept separate from
`app/services/sql_workspace_service.py` (saved queries/workspaces).

Every `table`/`column` argument taken from a request is resolved against
real `DatasetTable`/`DatasetColumnProfile` rows *before* being handed to
`app/dataset_hub/query_engine.py` for SQL interpolation — request input is
never trusted directly (section 58 of the Phase 5 spec)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.dataset_hub import product_analytics_engine, query_engine
from app.models.dataset import Dataset, DatasetTable
from app.models.dataset_profile import DatasetColumnProfile, DatasetProfile, DatasetQualityReport
from app.models.sql_lab import SqlTable
from app.repositories.dataset import DatasetRepository
from app.schemas.dataset import (
    CohortRetentionResponse,
    CohortRowSchema,
    ColumnProfileSchema,
    CorrelationResponse,
    DatasetProfileResponse,
    DatasetQualityResponse,
    DistributionResponse,
    DuplicatesResponse,
    FunnelResponse,
    FunnelStepSchema,
    OutliersResponse,
    QualityIssueSchema,
    QualityReportSchema,
    RawColumnSchema,
    RawSchemaResponse,
    SchemaColumnSchema,
    TableProfileSchema,
    TableSchemaResponse,
    TimeSeriesPoint,
    TimeSeriesResponse,
)
from app.sql.paths import resolve_repo_path


class DatasetAnalysisService:
    def __init__(self, db: Session, user_id: str | None = None) -> None:
        self.db = db
        self.repo = DatasetRepository(db)
        self.user_id = user_id

    def _find_dataset(self, id_or_slug: str) -> Dataset:
        dataset = self.repo.get_by_id(id_or_slug) or self.repo.get_by_slug(id_or_slug)
        if dataset is None or (dataset.owner_user_id is not None and dataset.owner_user_id != self.user_id):
            raise NotFoundError(f"Dataset '{id_or_slug}' was not found.")
        return dataset

    def _resolve_table(self, dataset: Dataset, table_name: str | None) -> DatasetTable:
        if not dataset.tables:
            raise AppError(f"Dataset '{dataset.slug}' has no tables to analyze yet.")
        if table_name is None:
            return dataset.tables[0]
        for table in dataset.tables:
            if table.table_name == table_name:
                return table
        raise NotFoundError(
            f"Table '{table_name}' was not found in dataset '{dataset.slug}'.",
            details={"available_tables": [t.table_name for t in dataset.tables]},
        )

    def _latest_profile(self, dataset_id: str, table_name: str) -> DatasetProfile | None:
        stmt = (
            select(DatasetProfile)
            .where(DatasetProfile.dataset_id == dataset_id, DatasetProfile.table_name == table_name)
            .order_by(DatasetProfile.generated_at.desc())
        )
        return self.db.execute(stmt).scalars().first()

    def _assert_known_column(
        self, dataset: Dataset, table: DatasetTable, column_name: str
    ) -> DatasetColumnProfile:
        profile = self._latest_profile(dataset.id, table.table_name)
        if profile is None:
            raise AppError(f"Table '{table.table_name}' has not been profiled yet.")
        for col in profile.columns:
            if col.column_name == column_name:
                return col
        raise NotFoundError(
            f"Column '{column_name}' was not found on table '{table.table_name}'.",
            details={"available_columns": [c.column_name for c in profile.columns]},
        )

    # --- Schema --------------------------------------------------------

    def get_schema(self, id_or_slug: str, table_name: str | None) -> list[TableSchemaResponse]:
        dataset = self._find_dataset(id_or_slug)
        tables = [self._resolve_table(dataset, table_name)] if table_name else dataset.tables
        responses = []
        for table in tables:
            profile = self._latest_profile(dataset.id, table.table_name)
            if profile is None:
                continue
            responses.append(
                TableSchemaResponse(
                    table_name=table.table_name,
                    row_count=profile.row_count,
                    generated_at=profile.generated_at,
                    columns=[
                        SchemaColumnSchema(
                            column_name=c.column_name,
                            inferred_sql_type=c.inferred_sql_type,
                            data_type=c.data_type,
                            null_count=c.null_count,
                            null_percentage=c.null_percentage,
                            unique_count=c.unique_count,
                            unique_percentage=c.unique_percentage,
                        )
                        for c in profile.columns
                    ],
                )
            )
        return responses

    # --- Profile / quality --------------------------------------------

    def get_profile(self, id_or_slug: str) -> DatasetProfileResponse:
        dataset = self._find_dataset(id_or_slug)
        tables = []
        for table in dataset.tables:
            profile = self._latest_profile(dataset.id, table.table_name)
            if profile is None:
                continue
            tables.append(
                TableProfileSchema(
                    table_name=profile.table_name,
                    row_count=profile.row_count,
                    column_count=profile.column_count,
                    size_bytes=profile.size_bytes,
                    duplicate_row_count=profile.duplicate_row_count,
                    generated_at=profile.generated_at,
                    columns=[
                        ColumnProfileSchema.model_validate(c, from_attributes=True) for c in profile.columns
                    ],
                )
            )
        return DatasetProfileResponse(dataset_id=dataset.id, tables=tables)

    def get_quality(self, id_or_slug: str) -> DatasetQualityResponse:
        dataset = self._find_dataset(id_or_slug)
        reports = []
        for table in dataset.tables:
            stmt = (
                select(DatasetQualityReport)
                .where(
                    DatasetQualityReport.dataset_id == dataset.id,
                    DatasetQualityReport.table_name == table.table_name,
                )
                .order_by(DatasetQualityReport.generated_at.desc())
            )
            report = self.db.execute(stmt).scalars().first()
            if report is None:
                continue
            reports.append(
                QualityReportSchema(
                    table_name=report.table_name,
                    overall_score=report.overall_score,
                    completeness_score=report.completeness_score,
                    uniqueness_score=report.uniqueness_score,
                    validity_score=report.validity_score,
                    consistency_score=report.consistency_score,
                    duplicate_row_count=report.duplicate_row_count,
                    issues=[QualityIssueSchema(**i) for i in report.issues],
                    methodology=report.methodology,
                    generated_at=report.generated_at,
                )
            )
        return DatasetQualityResponse(dataset_id=dataset.id, tables=reports)

    # --- Duplicates / outliers ------------------------------------------

    def get_duplicates(self, id_or_slug: str, table_name: str | None, limit: int = 20) -> DuplicatesResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_table(dataset, table_name)
        columns, rows, count = query_engine.sample_duplicate_rows(
            resolve_repo_path(table.file_path), limit=limit
        )
        return DuplicatesResponse(
            table_name=table.table_name, duplicate_row_count=count, sample_rows=rows, columns=columns
        )

    def get_outliers(
        self, id_or_slug: str, table_name: str | None, column_name: str, limit: int = 20
    ) -> OutliersResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_table(dataset, table_name)
        col = self._assert_known_column(dataset, table, column_name)
        if col.data_type != "numeric":
            raise AppError(
                f"Outlier detection only applies to numeric columns; '{column_name}' is {col.data_type}."
            )
        method = col.outlier_method or "iqr"
        columns, rows, count, lower, upper = query_engine.sample_outlier_rows(
            resolve_repo_path(table.file_path), column_name, method=method, limit=limit
        )
        return OutliersResponse(
            table_name=table.table_name,
            column_name=column_name,
            method=method,
            outlier_count=count,
            lower_bound=lower,
            upper_bound=upper,
            sample_rows=rows,
            columns=columns,
        )

    # --- Explorers --------------------------------------------------

    def get_correlation(
        self, id_or_slug: str, table_name: str | None, columns: list[str] | None, method: str
    ) -> CorrelationResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_table(dataset, table_name)
        profile = self._latest_profile(dataset.id, table.table_name)
        if profile is None:
            raise AppError(f"Table '{table.table_name}' has not been profiled yet.")
        numeric_columns = {c.column_name for c in profile.columns if c.data_type == "numeric"}
        selected = columns or sorted(numeric_columns)
        unknown = [c for c in selected if c not in numeric_columns]
        if unknown:
            raise AppError(f"Not numeric columns on '{table.table_name}': {', '.join(unknown)}.")
        if len(selected) < 2:
            raise AppError("Select at least two numeric columns to compute correlation.")
        matrix = query_engine.correlation_matrix(resolve_repo_path(table.file_path), selected, method=method)
        return CorrelationResponse(
            table_name=table.table_name, method=method, columns=selected, matrix=matrix
        )

    def get_distribution(
        self, id_or_slug: str, table_name: str | None, column_name: str, bins: int
    ) -> DistributionResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_table(dataset, table_name)
        col = self._assert_known_column(dataset, table, column_name)
        if col.data_type != "numeric":
            raise AppError(
                f"Distribution explorer only applies to numeric columns; '{column_name}' is {col.data_type}."
            )
        result = query_engine.distribution(resolve_repo_path(table.file_path), column_name, bins=bins)
        return DistributionResponse(table_name=table.table_name, column_name=column_name, **result)

    def get_time_series(
        self,
        id_or_slug: str,
        table_name: str | None,
        date_column: str,
        metric_column: str,
        aggregation: str,
        granularity: str,
    ) -> TimeSeriesResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_table(dataset, table_name)
        date_col = self._assert_known_column(dataset, table, date_column)
        if date_col.data_type != "datetime":
            raise AppError(f"'{date_column}' is not a datetime column.")
        if aggregation != "COUNT":
            metric_col = self._assert_known_column(dataset, table, metric_column)
            if metric_col.data_type != "numeric":
                raise AppError(f"'{metric_column}' is not numeric.")
        points = query_engine.time_series(
            resolve_repo_path(table.file_path),
            date_column,
            metric_column,
            aggregation=aggregation,
            granularity=granularity,
        )
        return TimeSeriesResponse(
            table_name=table.table_name,
            date_column=date_column,
            metric_column=metric_column,
            aggregation=aggregation,
            granularity=granularity,
            points=[TimeSeriesPoint(**p) for p in points],
        )

    # --- Product analytics (Phase 6) ------------------------------------
    # Funnel/cohort tables (e.g. the seeded "saas-product" dataset) are
    # typically registered as plain SQL Lab databases (SqlTable rows only,
    # like "ecommerce") rather than imported through the Dataset Hub upload
    # pipeline, so they never get a DatasetProfile. These two methods
    # validate columns directly via DuckDB instead of depending on
    # `_assert_known_column`/`_latest_profile` (which require one) —
    # deliberately independent of the EDA-profile-backed explorers above.

    def _resolve_any_table(self, dataset: Dataset, table_name: str | None) -> DatasetTable | SqlTable:
        for table in dataset.tables:
            if table_name is None or table.table_name == table_name:
                return table
        sql_tables = (
            self.db.query(SqlTable)
            .filter(SqlTable.dataset_id == dataset.id)
            .order_by(SqlTable.display_order)
            .all()
        )
        if table_name is None and sql_tables:
            return sql_tables[0]
        for sql_table in sql_tables:
            if sql_table.table_name == table_name:
                return sql_table
        available = [t.table_name for t in dataset.tables] + [t.table_name for t in sql_tables]
        if not available:
            raise AppError(f"Dataset '{dataset.slug}' has no tables to analyze yet.")
        raise NotFoundError(
            f"Table '{table_name}' was not found in dataset '{dataset.slug}'.",
            details={"available_tables": available},
        )

    def _assert_column_exists(self, table: DatasetTable | SqlTable, *columns: str) -> None:
        import duckdb

        path = resolve_repo_path(table.file_path)
        read_fn = {
            "csv": "read_csv_auto",
            "parquet": "read_parquet",
            "json": "read_json_auto",
        }[table.file_format]
        con = duckdb.connect(":memory:")
        try:
            known = {
                r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {read_fn}('{path.as_posix()}')").fetchall()
            }
        finally:
            con.close()
        unknown = [c for c in columns if c not in known]
        if unknown:
            raise NotFoundError(
                f"Column(s) not found on table '{table.table_name}': {', '.join(unknown)}.",
                details={"available_columns": sorted(known)},
            )

    def get_raw_schema(self, id_or_slug: str, table_name: str | None) -> RawSchemaResponse:
        import duckdb

        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_any_table(dataset, table_name)
        path = resolve_repo_path(table.file_path)
        read_fn = {
            "csv": "read_csv_auto",
            "parquet": "read_parquet",
            "json": "read_json_auto",
        }[table.file_format]
        con = duckdb.connect(":memory:")
        try:
            rows = con.execute(f"DESCRIBE SELECT * FROM {read_fn}('{path.as_posix()}')").fetchall()
        finally:
            con.close()
        return RawSchemaResponse(
            table_name=table.table_name,
            columns=[RawColumnSchema(column_name=r[0], sql_type=r[1]) for r in rows],
        )

    def get_funnel(
        self, id_or_slug: str, table_name: str | None, user_col: str, event_col: str, steps: list[str]
    ) -> FunnelResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_any_table(dataset, table_name)
        self._assert_column_exists(table, user_col, event_col)
        rows = product_analytics_engine.funnel_conversion(
            resolve_repo_path(table.file_path), user_col, event_col, steps, file_format=table.file_format
        )
        return FunnelResponse(table_name=table.table_name, steps=[FunnelStepSchema(**r) for r in rows])

    def get_cohort_retention(
        self,
        id_or_slug: str,
        table_name: str | None,
        user_col: str,
        cohort_date_col: str,
        activity_date_col: str,
        granularity: str,
        periods: int,
    ) -> CohortRetentionResponse:
        dataset = self._find_dataset(id_or_slug)
        table = self._resolve_any_table(dataset, table_name)
        self._assert_column_exists(table, user_col, cohort_date_col, activity_date_col)
        result = product_analytics_engine.cohort_retention_matrix(
            resolve_repo_path(table.file_path),
            user_col,
            cohort_date_col,
            activity_date_col,
            granularity=granularity,
            periods=periods,
            file_format=table.file_format,
        )
        return CohortRetentionResponse(
            table_name=table.table_name,
            granularity=result["granularity"],
            periods=result["periods"],
            cohorts=[CohortRowSchema(**c) for c in result["cohorts"]],
        )
