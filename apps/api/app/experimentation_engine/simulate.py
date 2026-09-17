"""Deterministic A/B test simulations (spec sections 20 & 24) — repeatedly
draws binomial samples under an assumed true effect and re-runs the same
two-proportion z-test used by analyze.py, so a learner can see *empirically*
how often a given sample size/effect size combination reaches significance
(i.e. actual simulated power) rather than only trusting the closed-form
formula. Always seeded for reproducibility."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from statsmodels.stats.proportion import proportions_ztest

from app.core.errors import AppError

MAX_SIMULATIONS = 5000


@dataclass
class SimulationResult:
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


def simulate_ab_test(
    control_rate: float,
    treatment_rate: float,
    sample_size_per_variant: int,
    *,
    alpha: float = 0.05,
    num_simulations: int = 500,
    seed: int = 42,
) -> SimulationResult:
    for label, rate in (("control_rate", control_rate), ("treatment_rate", treatment_rate)):
        if not (0 < rate < 1):
            raise AppError(f"{label} must be strictly between 0 and 1.")
    if sample_size_per_variant < 2:
        raise AppError("sample_size_per_variant must be at least 2.")
    if not (1 <= num_simulations <= MAX_SIMULATIONS):
        raise AppError(f"num_simulations must be between 1 and {MAX_SIMULATIONS}.")

    rng = np.random.default_rng(seed)
    control_draws = rng.binomial(sample_size_per_variant, control_rate, size=num_simulations)
    treatment_draws = rng.binomial(sample_size_per_variant, treatment_rate, size=num_simulations)

    significant_count = 0
    example_run: dict | None = None
    for i in range(num_simulations):
        c_conv, t_conv = int(control_draws[i]), int(treatment_draws[i])
        _, p_value = proportions_ztest(
            [t_conv, c_conv], [sample_size_per_variant, sample_size_per_variant], alternative="two-sided"
        )
        is_sig = bool(p_value < alpha)
        if is_sig:
            significant_count += 1
        if example_run is None:
            example_run = {
                "control_conversions": c_conv,
                "treatment_conversions": t_conv,
                "p_value": float(p_value),
                "significant": is_sig,
            }

    empirical_power = significant_count / num_simulations
    true_effect = treatment_rate - control_rate
    interpretation = (
        f"Across {num_simulations} simulated experiments (true control rate {control_rate * 100:.1f}%, "
        f"true treatment rate {treatment_rate * 100:.1f}%, a real effect of "
        f"{'+' if true_effect >= 0 else ''}{true_effect * 100:.1f} points, "
        f"n={sample_size_per_variant}/variant), "
        f"{significant_count} ({empirical_power * 100:.0f}%) came back statistically significant at "
        f"alpha={alpha}. This is the empirical power — even though the effect is real and fixed here, "
        f"random sampling noise means not every run detects it. This is exactly why underpowered tests "
        "produce inconsistent-looking results across repeated runs."
    )

    return SimulationResult(
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        sample_size_per_variant=sample_size_per_variant,
        alpha=alpha,
        num_simulations=num_simulations,
        seed=seed,
        significant_count=significant_count,
        empirical_power=empirical_power,
        example_run=example_run or {},
        interpretation=interpretation,
    )
