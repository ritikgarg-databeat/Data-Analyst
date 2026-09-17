"""Experimentation API (Phase 6) — sample size, power, A/B analysis, and
simulation. Entirely stateless/computational (no experiment-tracking table
in this phase — see the roadmap's "what Phase 6 does not build")."""

from __future__ import annotations

from app.experimentation_engine import analyze, sample_size, simulate
from app.schemas.experiments import (
    AnalyzeABTestRequest,
    AnalyzeABTestResponse,
    PowerRequest,
    PowerResponse,
    SampleSizeRequest,
    SampleSizeResponse,
    SimulateABTestRequest,
    SimulateABTestResponse,
)


class ExperimentService:
    def __init__(self, db=None) -> None:  # db unused today; kept for DI-pattern consistency
        self.db = db

    def sample_size(self, payload: SampleSizeRequest) -> SampleSizeResponse:
        result = sample_size.sample_size_for_proportions(
            payload.baseline_conversion,
            payload.expected_uplift_relative,
            alpha=payload.alpha,
            power=payload.power,
        )
        return SampleSizeResponse(**result.__dict__)

    def power(self, payload: PowerRequest) -> PowerResponse:
        result = sample_size.power_for_sample_size(
            payload.baseline_conversion,
            payload.sample_size_per_variant,
            payload.expected_uplift_relative,
            alpha=payload.alpha,
        )
        return PowerResponse(**result.__dict__)

    def analyze(self, payload: AnalyzeABTestRequest) -> AnalyzeABTestResponse:
        result = analyze.analyze_ab_test(
            payload.control_users,
            payload.control_conversions,
            payload.treatment_users,
            payload.treatment_conversions,
            alpha=payload.alpha,
            minimum_practical_effect=payload.minimum_practical_effect,
        )
        return AnalyzeABTestResponse(**result.__dict__)

    def simulate(self, payload: SimulateABTestRequest) -> SimulateABTestResponse:
        result = simulate.simulate_ab_test(
            payload.control_rate,
            payload.treatment_rate,
            payload.sample_size_per_variant,
            alpha=payload.alpha,
            num_simulations=payload.num_simulations,
            seed=payload.seed,
        )
        return SimulateABTestResponse(**result.__dict__)
