from pydantic import BaseModel


class SampleSizeRequest(BaseModel):
    baseline_conversion: float
    expected_uplift_relative: float
    alpha: float = 0.05
    power: float = 0.8


class SampleSizeResponse(BaseModel):
    baseline_conversion: float
    expected_uplift: float
    absolute_mde: float
    alpha: float
    power: float
    sample_size_per_variant: int
    total_sample_size: int
    assumptions: str


class PowerRequest(BaseModel):
    baseline_conversion: float
    sample_size_per_variant: int
    expected_uplift_relative: float
    alpha: float = 0.05


class PowerResponse(BaseModel):
    baseline_conversion: float
    sample_size_per_variant: int
    absolute_mde: float
    alpha: float
    achieved_power: float
    assumptions: str
    interpretation: str


class AnalyzeABTestRequest(BaseModel):
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int
    alpha: float = 0.05
    minimum_practical_effect: float | None = None


class AnalyzeABTestResponse(BaseModel):
    control_users: int
    control_conversions: int
    treatment_users: int
    treatment_conversions: int
    control_rate: float
    treatment_rate: float
    absolute_difference: float
    relative_uplift: float | None
    confidence_interval_95: tuple[float, float]
    z_statistic: float
    p_value: float
    alpha: float
    is_statistically_significant: bool
    minimum_practical_effect: float | None
    is_practically_significant: bool | None
    verdict: str
    interpretation: str


class SimulateABTestRequest(BaseModel):
    control_rate: float
    treatment_rate: float
    sample_size_per_variant: int
    alpha: float = 0.05
    num_simulations: int = 500
    seed: int = 42


class SimulateABTestResponse(BaseModel):
    control_rate: float
    treatment_rate: float
    sample_size_per_variant: int
    alpha: float
    num_simulations: int
    seed: int
    significant_count: int
    empirical_power: float
    example_run: dict
    interpretation: str
