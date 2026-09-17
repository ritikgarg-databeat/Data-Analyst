"""Sample size and power calculations for a two-proportion A/B test (the
overwhelmingly common case for conversion-rate experiments) — spec sections
19-20. Uses statsmodels' normal-approximation power solver."""

from __future__ import annotations

from dataclasses import dataclass

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

from app.core.errors import AppError

_solver = NormalIndPower()

ASSUMPTIONS = (
    "Assumes a two-sided two-proportion z-test, equal allocation between control and "
    "treatment, and independent observations (one row per user). This is an approximation "
    "for planning purposes, not a substitute for a full power analysis on your actual metric."
)


@dataclass
class SampleSizeResult:
    baseline_conversion: float
    expected_uplift: float
    absolute_mde: float
    alpha: float
    power: float
    sample_size_per_variant: int
    total_sample_size: int
    assumptions: str


@dataclass
class PowerResult:
    baseline_conversion: float
    sample_size_per_variant: int
    absolute_mde: float
    alpha: float
    achieved_power: float
    assumptions: str
    interpretation: str


def _validate_rate(name: str, value: float) -> None:
    if not (0 < value < 1):
        raise AppError(f"{name} must be a proportion strictly between 0 and 1 (got {value}).")


def sample_size_for_proportions(
    baseline_conversion: float, expected_uplift_relative: float, *, alpha: float = 0.05, power: float = 0.8
) -> SampleSizeResult:
    _validate_rate("baseline_conversion", baseline_conversion)
    if expected_uplift_relative == 0:
        raise AppError("expected_uplift_relative must be non-zero.")
    if not (0 < alpha < 1) or not (0 < power < 1):
        raise AppError("alpha and power must both be between 0 and 1.")

    treatment_rate = baseline_conversion * (1 + expected_uplift_relative)
    if not (0 < treatment_rate < 1):
        raise AppError(
            f"baseline * (1 + uplift) = {treatment_rate:.4f} must stay strictly between 0 and 1 — "
            "the requested uplift is too large for this baseline."
        )

    effect_size = abs(proportion_effectsize(baseline_conversion, treatment_rate))
    n = _solver.solve_power(
        effect_size=effect_size, alpha=alpha, power=power, ratio=1.0, alternative="two-sided"
    )
    n_per_variant = int(-(-n // 1))  # ceil

    return SampleSizeResult(
        baseline_conversion=baseline_conversion,
        expected_uplift=expected_uplift_relative,
        absolute_mde=abs(treatment_rate - baseline_conversion),
        alpha=alpha,
        power=power,
        sample_size_per_variant=n_per_variant,
        total_sample_size=n_per_variant * 2,
        assumptions=ASSUMPTIONS,
    )


def power_for_sample_size(
    baseline_conversion: float,
    sample_size_per_variant: int,
    expected_uplift_relative: float,
    *,
    alpha: float = 0.05,
) -> PowerResult:
    _validate_rate("baseline_conversion", baseline_conversion)
    if sample_size_per_variant < 2:
        raise AppError("sample_size_per_variant must be at least 2.")
    treatment_rate = baseline_conversion * (1 + expected_uplift_relative)
    if not (0 < treatment_rate < 1):
        raise AppError("baseline * (1 + uplift) must stay strictly between 0 and 1.")

    effect_size = abs(proportion_effectsize(baseline_conversion, treatment_rate))
    achieved_power = float(
        _solver.solve_power(
            effect_size=effect_size,
            nobs1=sample_size_per_variant,
            alpha=alpha,
            ratio=1.0,
            alternative="two-sided",
        )
    )
    achieved_power = max(0.0, min(1.0, achieved_power))

    if achieved_power >= 0.8:
        interpretation = (
            f"At n={sample_size_per_variant}/variant, you have {achieved_power * 100:.0f}% power to detect "
            "this effect — at or above the conventional 80% threshold, so a null result would be fairly "
            "trustworthy (low false-negative risk)."
        )
    else:
        interpretation = (
            f"At n={sample_size_per_variant}/variant, you only have {achieved_power * 100:.0f}% power to "
            "detect this effect — below the conventional 80% threshold. An underpowered test that comes "
            "back 'not significant' is genuinely ambiguous: it could mean there's no effect, or it could "
            "mean the test simply couldn't detect a real one this size."
        )

    return PowerResult(
        baseline_conversion=baseline_conversion,
        sample_size_per_variant=sample_size_per_variant,
        absolute_mde=abs(treatment_rate - baseline_conversion),
        alpha=alpha,
        achieved_power=achieved_power,
        assumptions=ASSUMPTIONS,
        interpretation=interpretation,
    )
