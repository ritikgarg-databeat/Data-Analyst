"""Statistics API (Phase 6, spec section 57) — descriptive stats, hypothesis
tests, correlation, and regression, computed directly in the API process
(scipy/statsmodels are core dependencies as of this phase — see
pyproject.toml) rather than via the Python Lab sandbox. Dataset-backed
requests are resolved to real column names/values via the same
validate-before-interpolate posture as DatasetAnalysisService."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.errors import AppError, NotFoundError
from app.dataset_hub import query_engine
from app.models.dataset import Dataset, DatasetTable
from app.models.sql_lab import SqlTable
from app.repositories.dataset import DatasetRepository
from app.schemas.statistics import (
    CoefficientSchema,
    ConfidenceIntervalSchema,
    CorrelationRequest,
    DatasetColumnRef,
    RegressionRequest,
    RegressionResponse,
    StatTestRequest,
    SummaryStatsRequest,
    SummaryStatsResponse,
    TestResultResponse,
)
from app.sql.paths import resolve_repo_path
from app.stats_engine import descriptive, inference, regression


class StatisticsService:
    def __init__(self, db: Session, user_id: str | None = None) -> None:
        self.db = db
        self.repo = DatasetRepository(db)
        self.user_id = user_id

    def _find_dataset(self, id_or_slug: str) -> Dataset:
        dataset = self.repo.get_by_id(id_or_slug) or self.repo.get_by_slug(id_or_slug)
        if dataset is None or (
            self.user_id is not None
            and dataset.owner_user_id is not None
            and dataset.owner_user_id != self.user_id
        ):
            raise NotFoundError(f"Dataset '{id_or_slug}' was not found.")
        return dataset

    def _resolve_table(self, dataset: Dataset, table_name: str) -> DatasetTable | SqlTable:
        # Datasets seeded purely as SQL Lab databases (e.g. "ecommerce",
        # "saas-product") only ever get SqlTable rows, never a DatasetTable —
        # same dual-check precedent as DatasetService.to_schema() (Phase 5).
        for table in dataset.tables:
            if table.table_name == table_name:
                return table
        sql_table = (
            self.db.query(SqlTable)
            .filter(SqlTable.dataset_id == dataset.id, SqlTable.table_name == table_name)
            .one_or_none()
        )
        if sql_table is not None:
            return sql_table
        available = [t.table_name for t in dataset.tables] + [
            t.table_name for t in self.db.query(SqlTable).filter(SqlTable.dataset_id == dataset.id).all()
        ]
        raise NotFoundError(
            f"Table '{table_name}' was not found in dataset '{dataset.slug}'.",
            details={"available_tables": available},
        )

    def _assert_known_column(self, table: DatasetTable | SqlTable, column: str) -> None:
        # Resolve via DuckDB DESCRIBE rather than requiring a prior profile —
        # Phase 6 datasets/tables may be queried for stats before an EDA
        # profile has ever been generated.
        import duckdb

        path = resolve_repo_path(table.file_path)
        con = duckdb.connect(":memory:")
        try:
            read_fn = {"csv": "read_csv_auto", "parquet": "read_parquet", "json": "read_json_auto"}[
                table.file_format
            ]
            columns = {
                r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {read_fn}('{path.as_posix()}')").fetchall()
            }
        finally:
            con.close()
        if column not in columns:
            raise NotFoundError(
                f"Column '{column}' was not found on table '{table.table_name}'.",
                details={"available_columns": sorted(columns)},
            )

    def _values_for(self, ref: DatasetColumnRef) -> list[float]:
        dataset = self._find_dataset(ref.dataset_id)
        table = self._resolve_table(dataset, ref.table_name)
        self._assert_known_column(table, ref.column)
        path = resolve_repo_path(table.file_path)
        return query_engine.column_values(path, ref.column, file_format=table.file_format)

    # --- Summary --------------------------------------------------------

    def summary(self, payload: SummaryStatsRequest) -> SummaryStatsResponse:
        values = payload.values
        if values is None:
            # SummaryStatsRequest.model_validator guarantees `dataset` is set when `values` isn't.
            dataset_ref = payload.dataset
            assert dataset_ref is not None
            values = self._values_for(dataset_ref)
        result = descriptive.summary_stats(values, confidence=payload.confidence)
        return SummaryStatsResponse(
            count=result.count,
            mean=result.mean,
            median=result.median,
            mode=result.mode,
            min=result.min,
            max=result.max,
            range=result.range,
            variance=result.variance,
            std_dev=result.std_dev,
            coefficient_of_variation=result.coefficient_of_variation,
            q1=result.q1,
            q3=result.q3,
            iqr=result.iqr,
            percentiles=result.percentiles,
            skewness=result.skewness,
            outlier_count=result.outlier_count,
            outlier_bounds=result.outlier_bounds,
            mean_confidence_interval=ConfidenceIntervalSchema(
                level=result.mean_confidence_interval.level,
                lower=result.mean_confidence_interval.lower,
                upper=result.mean_confidence_interval.upper,
                margin_of_error=result.mean_confidence_interval.margin_of_error,
            ),
            methodology=result.methodology,
        )

    # --- Hypothesis tests -------------------------------------------------

    def run_test(self, payload: StatTestRequest) -> TestResultResponse:
        sample_a = payload.sample_a
        sample_b = payload.sample_b
        if payload.dataset_a is not None:
            sample_a = self._values_for(payload.dataset_a)
        if payload.dataset_b is not None:
            sample_b = self._values_for(payload.dataset_b)

        test_type = payload.test_type
        if test_type == "one_sample_t":
            if sample_a is None or payload.population_mean is None:
                raise AppError("one_sample_t requires sample_a (or dataset_a) and population_mean.")
            result = inference.one_sample_t_test(
                sample_a, payload.population_mean, alpha=payload.alpha, alternative=payload.alternative
            )
        elif test_type == "independent_t":
            if sample_a is None or sample_b is None:
                raise AppError("independent_t requires sample_a/sample_b (or dataset_a/dataset_b).")
            result = inference.independent_t_test(
                sample_a, sample_b, alpha=payload.alpha, alternative=payload.alternative
            )
        elif test_type == "paired_t":
            if sample_a is None or sample_b is None:
                raise AppError("paired_t requires sample_a/sample_b (or dataset_a/dataset_b).")
            result = inference.paired_t_test(
                sample_a, sample_b, alpha=payload.alpha, alternative=payload.alternative
            )
        elif test_type == "two_proportion_z":
            successes_a, n_a, successes_b, n_b = (
                payload.successes_a,
                payload.n_a,
                payload.successes_b,
                payload.n_b,
            )
            if successes_a is None or n_a is None or successes_b is None or n_b is None:
                raise AppError("two_proportion_z requires successes_a, n_a, successes_b, n_b.")
            result = inference.two_proportion_z_test(
                successes_a, n_a, successes_b, n_b, alpha=payload.alpha, alternative=payload.alternative
            )
        elif test_type == "chi_square":
            contingency_table = payload.contingency_table
            if contingency_table is None:
                raise AppError("chi_square requires contingency_table.")
            result = inference.chi_square_test(contingency_table, alpha=payload.alpha)
        elif test_type == "mann_whitney":
            if sample_a is None or sample_b is None:
                raise AppError("mann_whitney requires sample_a/sample_b (or dataset_a/dataset_b).")
            result = inference.mann_whitney_test(
                sample_a, sample_b, alpha=payload.alpha, alternative=payload.alternative
            )
        elif test_type == "anova":
            groups = payload.groups
            if not groups or len(groups) < 2:
                raise AppError("anova requires groups: a list of at least 2 numeric arrays.")
            result = inference.one_way_anova(*groups, alpha=payload.alpha)
        else:
            raise AppError(
                f"Unsupported test_type '{test_type}'. Use one of: one_sample_t, independent_t, paired_t, "
                "two_proportion_z, chi_square, mann_whitney, anova."
            )

        return TestResultResponse(**result.__dict__)

    # --- Correlation -------------------------------------------------------

    def correlation(self, payload: CorrelationRequest) -> TestResultResponse:
        x = payload.x
        if x is None:
            # CorrelationRequest.model_validator guarantees dataset_x/dataset_y are set otherwise.
            dataset_x_ref = payload.dataset_x
            assert dataset_x_ref is not None
            x = self._values_for(dataset_x_ref)
        y = payload.y
        if y is None:
            dataset_y_ref = payload.dataset_y
            assert dataset_y_ref is not None
            y = self._values_for(dataset_y_ref)
        result = inference.correlation_test(x, y, method=payload.method, alpha=payload.alpha)
        return TestResultResponse(**result.__dict__)

    # --- Regression ----------------------------------------------------

    def regression(self, payload: RegressionRequest) -> RegressionResponse:
        if payload.features is not None and payload.y is not None:
            result = regression.multiple_regression(payload.features, payload.y, y_name=payload.y_name)
        else:
            # RegressionRequest.model_validator guarantees these are all set otherwise.
            dataset_id, table_name, feature_columns, target_column = (
                payload.dataset_id,
                payload.table_name,
                payload.feature_columns,
                payload.target_column,
            )
            assert dataset_id is not None
            assert table_name is not None
            assert feature_columns is not None
            assert target_column is not None

            dataset = self._find_dataset(dataset_id)
            table = self._resolve_table(dataset, table_name)
            for col in [*feature_columns, target_column]:
                self._assert_known_column(table, col)
            path = resolve_repo_path(table.file_path)
            features = {
                col: query_engine.column_values(path, col, file_format=table.file_format)
                for col in feature_columns
            }
            y = query_engine.column_values(path, target_column, file_format=table.file_format)
            result = regression.multiple_regression(features, y, y_name=target_column)

        return RegressionResponse(
            formula_description=result.formula_description,
            intercept=CoefficientSchema(**result.intercept.__dict__),
            coefficients=[CoefficientSchema(**c.__dict__) for c in result.coefficients],
            r_squared=result.r_squared,
            adjusted_r_squared=result.adjusted_r_squared,
            n_observations=result.n_observations,
            residual_std_error=result.residual_std_error,
            interpretation=result.interpretation,
            multicollinearity_warning=result.multicollinearity_warning,
        )
