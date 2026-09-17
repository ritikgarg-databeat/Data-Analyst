"""Descriptive statistics — pure functions over a list of numbers.

No DB/DuckDB dependency here: callers (the statistics service) are
responsible for pulling the actual numbers out of a dataset column via
DuckDB first (same "engine gets primitives in, primitives out" convention
as app/dataset_hub/*), or the caller passed raw numbers directly from a
request body.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mode as _mode

import numpy as np
from scipy import stats as scipy_stats

from app.core.errors import AppError


@dataclass
class ConfidenceInterval:
    level: float
    lower: float
    upper: float
    margin_of_error: float


@dataclass
class DescriptiveSummary:
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
    mean_confidence_interval: ConfidenceInterval
    methodology: str = field(
        default=(
            "Variance/std dev use the sample (n-1, ddof=1) formula. Quartiles use linear "
            "interpolation (numpy default). Outliers are flagged by the 1.5×IQR rule "
            "(below Q1-1.5×IQR or above Q3+1.5×IQR). The mean's confidence interval uses "
            "the t-distribution (appropriate for small samples with an unknown population "
            "std dev) — see the Confidence Intervals lesson for how to read it correctly."
        )
    )


DEFAULT_PERCENTILES = (5, 10, 25, 50, 75, 90, 95, 99)


def summary_stats(
    values: list[float], *, confidence: float = 0.95, percentiles: tuple[int, ...] = DEFAULT_PERCENTILES
) -> DescriptiveSummary:
    if len(values) < 2:
        raise AppError("Need at least 2 values to compute descriptive statistics.")

    arr = np.asarray(values, dtype=float)
    n = arr.size
    mean = float(arr.mean())
    median = float(np.median(arr))
    try:
        modes = [float(_mode(arr.tolist()))]
    except Exception:
        modes = []
    variance = float(arr.var(ddof=1))
    std_dev = float(arr.std(ddof=1))
    q1, q3 = (float(x) for x in np.percentile(arr, [25, 75]))
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outlier_count = int(np.sum((arr < lower_bound) | (arr > upper_bound)))
    skewness = float(scipy_stats.skew(arr)) if n >= 3 else 0.0

    sem = std_dev / (n**0.5) if n > 0 else 0.0
    t_crit = float(scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1)) if n > 1 else 0.0
    margin = t_crit * sem
    ci = ConfidenceInterval(
        level=confidence, lower=mean - margin, upper=mean + margin, margin_of_error=margin
    )

    return DescriptiveSummary(
        count=n,
        mean=mean,
        median=median,
        mode=modes,
        min=float(arr.min()),
        max=float(arr.max()),
        range=float(arr.max() - arr.min()),
        variance=variance,
        std_dev=std_dev,
        coefficient_of_variation=(std_dev / mean) if mean != 0 else None,
        q1=q1,
        q3=q3,
        iqr=iqr,
        percentiles={str(p): float(np.percentile(arr, p)) for p in percentiles},
        skewness=skewness,
        outlier_count=outlier_count,
        outlier_bounds=(lower_bound, upper_bound),
        mean_confidence_interval=ci,
    )


def confidence_interval_for_mean(values: list[float], *, confidence: float = 0.95) -> ConfidenceInterval:
    if len(values) < 2:
        raise AppError("Need at least 2 values to compute a confidence interval.")
    arr = np.asarray(values, dtype=float)
    n = arr.size
    mean = float(arr.mean())
    sem = float(arr.std(ddof=1)) / (n**0.5)
    t_crit = float(scipy_stats.t.ppf(1 - (1 - confidence) / 2, df=n - 1))
    margin = t_crit * sem
    return ConfidenceInterval(
        level=confidence, lower=mean - margin, upper=mean + margin, margin_of_error=margin
    )
