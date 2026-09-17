"""Hypothesis testing — one dispatcher per supported test, each returning a
plain `TestResult` dataclass with the statistic, p-value, a stated decision,
and a plain-English interpretation. Deliberately explicit about which test
is used and why (spec section 11: "which test should I use and why", not
"blindly select a test") — every branch documents its own assumptions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats as scipy_stats
from statsmodels.stats.proportion import proportions_ztest

from app.core.errors import AppError

TWO_SIDED = "two-sided"
LESS = "less"
GREATER = "greater"
VALID_ALTERNATIVES = {TWO_SIDED, LESS, GREATER}


@dataclass
class TestResult:
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


def _decision_text(reject_null: bool, alpha: float, p_value: float) -> str:
    if reject_null:
        return (
            f"p = {p_value:.4f} is less than alpha = {alpha}, so we reject the null hypothesis — "
            "the observed difference is unlikely to be due to chance alone. This is a statement "
            "about statistical significance only; check practical/business significance separately."
        )
    return (
        f"p = {p_value:.4f} is not less than alpha = {alpha}, so we fail to reject the null "
        "hypothesis. This does NOT prove the null is true — it means this sample didn't provide "
        "strong enough evidence against it (could be a real effect too small to detect, or no "
        "effect at all)."
    )


def _validate_alternative(alternative: str) -> None:
    if alternative not in VALID_ALTERNATIVES:
        raise AppError(f"alternative must be one of {sorted(VALID_ALTERNATIVES)}, got '{alternative}'.")


def one_sample_t_test(
    sample: list[float], population_mean: float, *, alpha: float = 0.05, alternative: str = TWO_SIDED
) -> TestResult:
    _validate_alternative(alternative)
    if len(sample) < 2:
        raise AppError("Need at least 2 observations for a one-sample t-test.")
    arr = np.asarray(sample, dtype=float)
    statistic, p_value = scipy_stats.ttest_1samp(arr, population_mean, alternative=alternative)
    reject = bool(p_value < alpha)
    cohens_d = float((arr.mean() - population_mean) / arr.std(ddof=1)) if arr.std(ddof=1) else 0.0
    return TestResult(
        test_type="one_sample_t",
        test_name="One-sample t-test",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=float(len(arr) - 1),
        alpha=alpha,
        alternative=alternative,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value)),
        assumptions=[
            "Observations are independent.",
            "The sample is approximately normally distributed (or n is large enough for the CLT to apply).",
        ],
        effect_size=cohens_d,
        effect_size_label="Cohen's d",
    )


def independent_t_test(
    sample_a: list[float],
    sample_b: list[float],
    *,
    alpha: float = 0.05,
    alternative: str = TWO_SIDED,
    equal_var: bool = False,
) -> TestResult:
    _validate_alternative(alternative)
    if len(sample_a) < 2 or len(sample_b) < 2:
        raise AppError("Need at least 2 observations in each group for an independent t-test.")
    a, b = np.asarray(sample_a, dtype=float), np.asarray(sample_b, dtype=float)
    statistic, p_value = scipy_stats.ttest_ind(a, b, equal_var=equal_var, alternative=alternative)
    reject = bool(p_value < alpha)
    pooled_std = np.sqrt(
        ((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)
    )
    cohens_d = float((a.mean() - b.mean()) / pooled_std) if pooled_std else 0.0
    test_name = (
        "Welch's t-test (unequal variances)"
        if not equal_var
        else "Independent two-sample t-test (equal variances)"
    )
    return TestResult(
        test_type="independent_t",
        test_name=test_name,
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=None,
        alpha=alpha,
        alternative=alternative,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value)),
        assumptions=[
            "The two groups are independent of each other.",
            "Each group is approximately normally distributed (or n is large enough per group).",
            "Welch's version (default) does not assume equal variances — the safer default.",
        ],
        effect_size=cohens_d,
        effect_size_label="Cohen's d",
    )


def paired_t_test(
    before: list[float], after: list[float], *, alpha: float = 0.05, alternative: str = TWO_SIDED
) -> TestResult:
    _validate_alternative(alternative)
    if len(before) != len(after):
        raise AppError("Paired samples must have the same length (one 'before' and one 'after' per subject).")
    if len(before) < 2:
        raise AppError("Need at least 2 paired observations for a paired t-test.")
    a, b = np.asarray(before, dtype=float), np.asarray(after, dtype=float)
    statistic, p_value = scipy_stats.ttest_rel(a, b, alternative=alternative)
    diffs = b - a
    reject = bool(p_value < alpha)
    cohens_d = float(diffs.mean() / diffs.std(ddof=1)) if diffs.std(ddof=1) else 0.0
    return TestResult(
        test_type="paired_t",
        test_name="Paired t-test",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=float(len(a) - 1),
        alpha=alpha,
        alternative=alternative,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value)),
        assumptions=[
            "Observations are paired (same subject measured twice, e.g. before/after).",
            "The differences (after - before) are approximately normally distributed.",
        ],
        effect_size=cohens_d,
        effect_size_label="Cohen's d (of the differences)",
    )


def two_proportion_z_test(
    successes_a: int,
    n_a: int,
    successes_b: int,
    n_b: int,
    *,
    alpha: float = 0.05,
    alternative: str = TWO_SIDED,
) -> TestResult:
    _validate_alternative(alternative)
    for label, s, n in (("A", successes_a, n_a), ("B", successes_b, n_b)):
        if n <= 0 or s < 0 or s > n:
            raise AppError(f"Group {label}: successes must be between 0 and n, and n must be positive.")
    sm_alternative = (
        "two-sided" if alternative == TWO_SIDED else ("smaller" if alternative == LESS else "larger")
    )
    statistic, p_value = proportions_ztest([successes_a, successes_b], [n_a, n_b], alternative=sm_alternative)
    reject = bool(p_value < alpha)
    p_a, p_b = successes_a / n_a, successes_b / n_b
    return TestResult(
        test_type="two_proportion_z",
        test_name="Two-proportion z-test",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=None,
        alpha=alpha,
        alternative=alternative,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value)),
        assumptions=[
            "Each group's observations are independent (e.g. one row per user, not per event).",
            f"Sample sizes are large enough for the normal approximation (n·p and n·(1-p) ≥ ~5): "
            f"A has {n_a * p_a:.0f}/{n_a * (1 - p_a):.0f}, B has {n_b * p_b:.0f}/{n_b * (1 - p_b):.0f}.",
        ],
        effect_size=float(p_b - p_a),
        effect_size_label="Absolute difference in proportions",
    )


def chi_square_test(contingency_table: list[list[int]], *, alpha: float = 0.05) -> TestResult:
    if len(contingency_table) < 2 or any(len(row) < 2 for row in contingency_table):
        raise AppError("A chi-square test needs a contingency table with at least 2 rows and 2 columns.")
    table = np.asarray(contingency_table, dtype=float)
    if (table < 0).any():
        raise AppError("Contingency table counts cannot be negative.")
    statistic, p_value, dof, expected = scipy_stats.chi2_contingency(table)
    reject = bool(p_value < alpha)
    low_expected = int((expected < 5).sum())
    assumptions = [
        "Observations are independent (one unit contributes to exactly one cell).",
        "Expected cell counts should generally be ≥ 5 for the approximation to hold.",
    ]
    if low_expected:
        assumptions.append(
            f"Warning: {low_expected} expected cell count(s) are below 5 — the p-value may be unreliable; "
            "consider Fisher's exact test for small samples."
        )
    n = float(table.sum())
    cramers_v = (
        float(np.sqrt((statistic / n) / (min(table.shape) - 1))) if n and min(table.shape) > 1 else 0.0
    )
    return TestResult(
        test_type="chi_square",
        test_name="Chi-square test of independence",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=float(dof),
        alpha=alpha,
        alternative=TWO_SIDED,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value)),
        assumptions=assumptions,
        effect_size=cramers_v,
        effect_size_label="Cramér's V",
    )


def mann_whitney_test(
    sample_a: list[float], sample_b: list[float], *, alpha: float = 0.05, alternative: str = TWO_SIDED
) -> TestResult:
    _validate_alternative(alternative)
    if len(sample_a) < 1 or len(sample_b) < 1:
        raise AppError("Need at least 1 observation in each group for a Mann-Whitney U test.")
    a, b = np.asarray(sample_a, dtype=float), np.asarray(sample_b, dtype=float)
    statistic, p_value = scipy_stats.mannwhitneyu(a, b, alternative=alternative)
    reject = bool(p_value < alpha)
    return TestResult(
        test_type="mann_whitney",
        test_name="Mann-Whitney U test",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=None,
        alpha=alpha,
        alternative=alternative,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value))
        + " This test compares distributions/medians using ranks, not means — use it when data is "
        "skewed, has outliers, or is ordinal rather than approximately normal.",
        assumptions=[
            "Observations in each group are independent.",
            "No normality assumption — this is the non-parametric alternative to the independent t-test.",
        ],
    )


def one_way_anova(*groups: list[float], alpha: float = 0.05) -> TestResult:
    if len(groups) < 2:
        raise AppError("ANOVA needs at least 2 groups.")
    if any(len(g) < 2 for g in groups):
        raise AppError("Each group needs at least 2 observations for ANOVA.")
    arrays = [np.asarray(g, dtype=float) for g in groups]
    statistic, p_value = scipy_stats.f_oneway(*arrays)
    reject = bool(p_value < alpha)
    grand_mean = np.concatenate(arrays).mean()
    ss_between = sum(len(a) * (a.mean() - grand_mean) ** 2 for a in arrays)
    ss_total = sum((np.concatenate(arrays) - grand_mean) ** 2)
    eta_squared = float(ss_between / ss_total) if ss_total else 0.0
    return TestResult(
        test_type="anova",
        test_name="One-way ANOVA",
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=float(len(arrays) - 1),
        alpha=alpha,
        alternative=TWO_SIDED,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value))
        + " A significant ANOVA only tells you that at least one group differs — a post-hoc test "
        "(e.g. Tukey's HSD) is needed to say which pair(s) differ.",
        assumptions=[
            "Groups are independent.",
            "Each group is approximately normally distributed.",
            "Groups have approximately equal variances (homogeneity of variance).",
        ],
        effect_size=eta_squared,
        effect_size_label="Eta-squared (proportion of variance explained by group)",
    )


def correlation_test(
    x: list[float], y: list[float], *, method: str = "pearson", alpha: float = 0.05
) -> TestResult:
    if len(x) != len(y):
        raise AppError("x and y must have the same length.")
    if len(x) < 3:
        raise AppError("Need at least 3 paired observations to test a correlation.")
    if method not in ("pearson", "spearman"):
        raise AppError("method must be 'pearson' or 'spearman'.")
    fn = scipy_stats.pearsonr if method == "pearson" else scipy_stats.spearmanr
    statistic, p_value = fn(x, y)
    reject = bool(p_value < alpha)
    test_name = "Pearson correlation test" if method == "pearson" else "Spearman rank correlation test"
    return TestResult(
        test_type=f"{method}_correlation",
        test_name=test_name,
        statistic=float(statistic),
        p_value=float(p_value),
        degrees_of_freedom=float(len(x) - 2),
        alpha=alpha,
        alternative=TWO_SIDED,
        reject_null=reject,
        interpretation=_decision_text(reject, alpha, float(p_value))
        + " Remember: a significant correlation is evidence of association, never proof of causation.",
        assumptions=[
            "Observations are independent pairs."
            if method == "spearman"
            else "Observations are independent pairs, and the relationship (if any) is approximately linear.",
        ],
        effect_size=float(statistic),
        effect_size_label="Correlation coefficient (r)",
    )
