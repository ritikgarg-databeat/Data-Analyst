"""Linear regression via statsmodels OLS — simple (one predictor) and
multiple (several predictors), returning coefficients, R²/adjusted R², and
per-coefficient significance, framed for interpretation rather than just
calculation (spec section 15)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import statsmodels.api as sm

from app.core.errors import AppError


@dataclass
class Coefficient:
    name: str
    value: float
    std_error: float
    t_statistic: float
    p_value: float
    confidence_interval_95: tuple[float, float]
    significant: bool


@dataclass
class RegressionResult:
    formula_description: str
    intercept: Coefficient
    coefficients: list[Coefficient]
    r_squared: float
    adjusted_r_squared: float
    n_observations: int
    residual_std_error: float
    interpretation: str
    multicollinearity_warning: str | None = None


def _to_coefficient(name: str, model, index: int) -> Coefficient:
    # sm.OLS fit on plain numpy arrays (not a pandas DataFrame) returns plain
    # numpy arrays for params/bse/tvalues/pvalues/conf_int — no .iloc.
    ci_low, ci_high = model.conf_int()[index]
    p_value = float(model.pvalues[index])
    return Coefficient(
        name=name,
        value=float(model.params[index]),
        std_error=float(model.bse[index]),
        t_statistic=float(model.tvalues[index]),
        p_value=p_value,
        confidence_interval_95=(float(ci_low), float(ci_high)),
        significant=p_value < 0.05,
    )


def _check_multicollinearity(feature_matrix: np.ndarray, feature_names: list[str]) -> str | None:
    """Flags pairwise |correlation| > 0.85 among predictors — a cheap, dependency-free
    proxy for multicollinearity (a full VIF calculation needs a second regression per
    feature; this catches the common, easy-to-explain case)."""
    if feature_matrix.shape[1] < 2:
        return None
    corr = np.corrcoef(feature_matrix, rowvar=False)
    flagged = []
    for i in range(len(feature_names)):
        for j in range(i + 1, len(feature_names)):
            if abs(corr[i, j]) > 0.85:
                flagged.append(f"{feature_names[i]} & {feature_names[j]} (r={corr[i, j]:.2f})")
    if not flagged:
        return None
    return (
        "Possible multicollinearity between: " + "; ".join(flagged) + ". Highly correlated predictors "
        "make individual coefficients unstable and hard to interpret — consider dropping one, "
        "combining them, or interpreting the pair jointly rather than each coefficient alone."
    )


def simple_linear_regression(
    x: list[float], y: list[float], x_name: str = "x", y_name: str = "y"
) -> RegressionResult:
    return multiple_regression({x_name: x}, y, y_name=y_name)


def multiple_regression(
    features: dict[str, list[float]], y: list[float], y_name: str = "y"
) -> RegressionResult:
    if not features:
        raise AppError("At least one predictor (feature) is required.")
    feature_names = list(features.keys())
    n = len(y)
    for name, values in features.items():
        if len(values) != n:
            raise AppError(f"Feature '{name}' has {len(values)} values but y has {n}.")
    if n < len(feature_names) + 2:
        raise AppError(
            f"Need at least {len(feature_names) + 2} observations to fit a regression with "
            f"{len(feature_names)} predictor(s) (got {n})."
        )

    x_matrix = np.column_stack([np.asarray(features[name], dtype=float) for name in feature_names])
    y_arr = np.asarray(y, dtype=float)
    x_with_const = sm.add_constant(x_matrix, has_constant="add")
    model = sm.OLS(y_arr, x_with_const).fit()

    intercept = _to_coefficient("intercept", model, 0)
    coefficients = [_to_coefficient(name, model, i + 1) for i, name in enumerate(feature_names)]

    n_params = len(feature_names)
    if len(coefficients) == 1:
        direction = "increase" if coefficients[0].value >= 0 else "decrease"
        significance_label = (
            "statistically significant" if coefficients[0].significant else "not statistically significant"
        )
        interpretation = (
            f"A 1-unit increase in {feature_names[0]} is associated with a "
            f"{abs(coefficients[0].value):.4g} {direction} in {y_name}, on average "
            f"(p={coefficients[0].p_value:.4f}, {significance_label} at alpha=0.05). "
            f"This model explains {model.rsquared * 100:.1f}% of the variance in {y_name} "
            f"(R²={model.rsquared:.3f})."
        )
    else:
        sig_terms = [c.name for c in coefficients if c.significant]
        interpretation = (
            f"Holding the other {n_params - 1} predictor(s) constant, each coefficient below shows the "
            f"average change in {y_name} per 1-unit increase in that predictor. "
            f"{len(sig_terms)}/{n_params} predictors are statistically significant at alpha=0.05"
            + (f" ({', '.join(sig_terms)})" if sig_terms else "")
            + f". This model explains {model.rsquared * 100:.1f}% of the variance in {y_name} "
            f"(R²={model.rsquared:.3f}, adjusted R²={model.rsquared_adj:.3f})."
        )
    interpretation += (
        " Regression shows association, not causation — omitted variables, reverse causality, or "
        "confounders can produce a coefficient that looks meaningful but isn't causal."
    )

    return RegressionResult(
        formula_description=f"{y_name} ~ " + " + ".join(feature_names),
        intercept=intercept,
        coefficients=coefficients,
        r_squared=float(model.rsquared),
        adjusted_r_squared=float(model.rsquared_adj),
        n_observations=n,
        residual_std_error=float(np.sqrt(model.mse_resid)),
        interpretation=interpretation,
        multicollinearity_warning=_check_multicollinearity(x_matrix, feature_names),
    )
