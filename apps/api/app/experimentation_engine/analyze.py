"""The A/B Test Analyzer (spec section 21) — takes raw control/treatment
counts and returns rates, uplift, a confidence interval, and a p-value,
while explicitly separating statistical significance from practical
significance (spec section 22) rather than reducing the decision to
"p < 0.05 = ship"."""

from __future__ import annotations

import math
from dataclasses import dataclass

from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest

from app.core.errors import AppError


@dataclass
class ABTestResult:
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


def analyze_ab_test(
    control_users: int,
    control_conversions: int,
    treatment_users: int,
    treatment_conversions: int,
    *,
    alpha: float = 0.05,
    minimum_practical_effect: float | None = None,
) -> ABTestResult:
    for label, users, conversions in (
        ("control", control_users, control_conversions),
        ("treatment", treatment_users, treatment_conversions),
    ):
        if users <= 0:
            raise AppError(f"{label}_users must be positive.")
        if conversions < 0 or conversions > users:
            raise AppError(f"{label}_conversions must be between 0 and {label}_users.")
    if not (0 < alpha < 1):
        raise AppError("alpha must be between 0 and 1.")

    control_rate = control_conversions / control_users
    treatment_rate = treatment_conversions / treatment_users
    absolute_diff = treatment_rate - control_rate
    relative_uplift = (absolute_diff / control_rate) if control_rate > 0 else None

    z_stat, p_value = proportions_ztest(
        [treatment_conversions, control_conversions],
        [treatment_users, control_users],
        alternative="two-sided",
    )
    ci_low, ci_high = confint_proportions_2indep(
        treatment_conversions, treatment_users, control_conversions, control_users, method="wald", alpha=alpha
    )
    if math.isnan(ci_low) or math.isnan(ci_high):
        ci_low, ci_high = absolute_diff, absolute_diff

    is_significant = bool(p_value < alpha)

    is_practical: bool | None = None
    if minimum_practical_effect is not None:
        is_practical = abs(absolute_diff) >= minimum_practical_effect

    if is_significant and (is_practical is None or is_practical):
        verdict = "Ship-worthy evidence"
    elif is_significant and is_practical is False:
        verdict = "Statistically significant but too small to matter"
    elif not is_significant and is_practical:
        verdict = "Practically meaningful but not statistically confirmed"
    else:
        verdict = "Inconclusive"

    relative_uplift_text = (
        f", {'+' if relative_uplift >= 0 else ''}{relative_uplift * 100:.1f}% relative"
        if relative_uplift is not None
        else ""
    )
    parts = [
        f"Control converts at {control_rate * 100:.2f}%, treatment at {treatment_rate * 100:.2f}% "
        f"({'+' if absolute_diff >= 0 else ''}{absolute_diff * 100:.2f} points"
        + relative_uplift_text
        + f"). The 95% CI for the difference is [{ci_low * 100:.2f}%, {ci_high * 100:.2f}%], p={p_value:.4f}."
    ]
    if is_significant:
        parts.append(f"This clears the alpha={alpha} significance threshold.")
    else:
        parts.append(
            f"This does not clear the alpha={alpha} significance threshold — the observed difference "
            "could plausibly be noise; consider whether the test was adequately powered."
        )
    if minimum_practical_effect is not None:
        if is_practical:
            parts.append(
                f"The observed effect (|{absolute_diff * 100:.2f} points|) also meets your stated minimum "
                f"practical effect of {minimum_practical_effect * 100:.2f} points."
            )
        else:
            parts.append(
                f"However, the observed effect is smaller than your stated minimum practical effect of "
                f"{minimum_practical_effect * 100:.2f} points — even if real, it may not be worth the cost "
                "of shipping."
            )
    else:
        parts.append(
            "No minimum practical effect was supplied — statistical significance alone doesn't tell you "
            "whether this effect is big enough to matter for the business."
        )

    return ABTestResult(
        control_users=control_users,
        control_conversions=control_conversions,
        treatment_users=treatment_users,
        treatment_conversions=treatment_conversions,
        control_rate=control_rate,
        treatment_rate=treatment_rate,
        absolute_difference=absolute_diff,
        relative_uplift=relative_uplift,
        confidence_interval_95=(float(ci_low), float(ci_high)),
        z_statistic=float(z_stat),
        p_value=float(p_value),
        alpha=alpha,
        is_statistically_significant=is_significant,
        minimum_practical_effect=minimum_practical_effect,
        is_practically_significant=is_practical,
        verdict=verdict,
        interpretation=" ".join(parts),
    )
