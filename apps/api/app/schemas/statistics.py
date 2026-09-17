from pydantic import BaseModel, model_validator


class DatasetColumnRef(BaseModel):
    """Points at a column in an already-profiled dataset table, as an
    alternative to submitting raw numbers directly."""

    dataset_id: str
    table_name: str
    column: str


class ConfidenceIntervalSchema(BaseModel):
    level: float
    lower: float
    upper: float
    margin_of_error: float


class SummaryStatsRequest(BaseModel):
    values: list[float] | None = None
    dataset: DatasetColumnRef | None = None
    confidence: float = 0.95

    @model_validator(mode="after")
    def _require_one_source(self) -> "SummaryStatsRequest":
        if not self.values and not self.dataset:
            raise ValueError("Provide either `values` or `dataset`.")
        return self


class SummaryStatsResponse(BaseModel):
    count: int
    mean: float
    median: float
    mode: list[float]
    min: float
    max: float
    range: float
    variance: float
    std_dev: float
    coefficient_of_variation: float | None
    q1: float
    q3: float
    iqr: float
    percentiles: dict[str, float]
    skewness: float
    outlier_count: int
    outlier_bounds: tuple[float, float]
    mean_confidence_interval: ConfidenceIntervalSchema
    methodology: str


class StatTestRequest(BaseModel):
    test_type: str
    alpha: float = 0.05
    alternative: str = "two-sided"

    # Raw-array inputs (any subset used depending on test_type)
    sample_a: list[float] | None = None
    sample_b: list[float] | None = None
    groups: list[list[float]] | None = None
    population_mean: float | None = None
    successes_a: int | None = None
    n_a: int | None = None
    successes_b: int | None = None
    n_b: int | None = None
    contingency_table: list[list[int]] | None = None

    # Dataset-backed inputs (resolved to arrays by the service before dispatch)
    dataset_a: DatasetColumnRef | None = None
    dataset_b: DatasetColumnRef | None = None


class TestResultResponse(BaseModel):
    test_type: str
    test_name: str
    statistic: float
    p_value: float
    degrees_of_freedom: float | None
    alpha: float
    alternative: str
    reject_null: bool
    interpretation: str
    assumptions: list[str]
    effect_size: float | None = None
    effect_size_label: str | None = None


class CorrelationRequest(BaseModel):
    x: list[float] | None = None
    y: list[float] | None = None
    dataset_x: DatasetColumnRef | None = None
    dataset_y: DatasetColumnRef | None = None
    method: str = "pearson"
    alpha: float = 0.05

    @model_validator(mode="after")
    def _require_one_source(self) -> "CorrelationRequest":
        has_arrays = self.x is not None and self.y is not None
        has_dataset = self.dataset_x is not None and self.dataset_y is not None
        if not has_arrays and not has_dataset:
            raise ValueError("Provide either both `x`/`y` or both `dataset_x`/`dataset_y`.")
        return self


class RegressionRequest(BaseModel):
    features: dict[str, list[float]] | None = None
    y: list[float] | None = None
    y_name: str = "y"
    dataset_id: str | None = None
    table_name: str | None = None
    feature_columns: list[str] | None = None
    target_column: str | None = None

    @model_validator(mode="after")
    def _require_one_source(self) -> "RegressionRequest":
        has_raw = bool(self.features) and self.y is not None
        has_dataset = bool(
            self.dataset_id and self.table_name and self.feature_columns and self.target_column
        )
        if not has_raw and not has_dataset:
            raise ValueError(
                "Provide either both `features`/`y`, or "
                "`dataset_id`/`table_name`/`feature_columns`/`target_column`."
            )
        return self


class CoefficientSchema(BaseModel):
    name: str
    value: float
    std_error: float
    t_statistic: float
    p_value: float
    confidence_interval_95: tuple[float, float]
    significant: bool


class RegressionResponse(BaseModel):
    formula_description: str
    intercept: CoefficientSchema
    coefficients: list[CoefficientSchema]
    r_squared: float
    adjusted_r_squared: float
    n_observations: int
    residual_std_error: float
    interpretation: str
    multicollinearity_warning: str | None = None
