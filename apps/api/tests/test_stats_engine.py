"""Unit tests for app/stats_engine/* — pure numpy/scipy/statsmodels
computations, no database/API involved. Covers descriptive statistics,
hypothesis tests, and regression (Phase 6 spec sections 4-15)."""

from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.stats_engine import descriptive, inference, regression


class TestDescriptive:
    def test_summary_stats_known_values(self) -> None:
        result = descriptive.summary_stats([1, 2, 3, 4, 5])
        assert result.count == 5
        assert result.mean == pytest.approx(3.0)
        assert result.median == pytest.approx(3.0)
        assert result.min == 1
        assert result.max == 5
        assert result.range == 4
        assert result.variance == pytest.approx(2.5, abs=1e-9)
        assert result.std_dev == pytest.approx(2.5**0.5, abs=1e-9)

    def test_outlier_detection_iqr(self) -> None:
        result = descriptive.summary_stats([10, 12, 11, 13, 12, 11, 100])
        assert result.outlier_count == 1

    def test_skewed_distribution_has_nonzero_skewness(self) -> None:
        result = descriptive.summary_stats([1, 2, 2, 3, 3, 3, 100])
        assert result.skewness > 0

    def test_confidence_interval_contains_mean(self) -> None:
        result = descriptive.summary_stats([10, 12, 11, 13, 9, 14, 10])
        ci = result.mean_confidence_interval
        assert ci.lower < result.mean < ci.upper
        assert ci.margin_of_error > 0

    def test_requires_at_least_two_values(self) -> None:
        with pytest.raises(AppError):
            descriptive.summary_stats([1])

    def test_coefficient_of_variation_none_when_mean_zero(self) -> None:
        result = descriptive.summary_stats([-1, 1, -1, 1])
        assert result.coefficient_of_variation is None

    def test_confidence_interval_for_mean_matches_summary(self) -> None:
        values = [10, 12, 11, 13, 9, 14, 10]
        ci_direct = descriptive.confidence_interval_for_mean(values)
        ci_summary = descriptive.summary_stats(values).mean_confidence_interval
        assert ci_direct.lower == pytest.approx(ci_summary.lower)
        assert ci_direct.upper == pytest.approx(ci_summary.upper)


class TestHypothesisTests:
    def test_one_sample_t_rejects_when_clearly_different(self) -> None:
        result = inference.one_sample_t_test([20, 21, 19, 22, 20, 21, 19, 20], population_mean=10)
        assert result.reject_null is True
        assert result.p_value < 0.001

    def test_one_sample_t_fails_to_reject_when_close(self) -> None:
        result = inference.one_sample_t_test([10.1, 9.9, 10.0, 10.2, 9.8], population_mean=10)
        assert result.reject_null is False

    def test_independent_t_detects_real_difference(self) -> None:
        result = inference.independent_t_test([1, 2, 3, 2, 1], [20, 21, 19, 22, 20])
        assert result.reject_null is True
        assert result.effect_size is not None
        # Cohen's d is signed (mean(a) - mean(b)) — sample_a's mean is far below
        # sample_b's, so a large *negative* value is the correct, expected sign.
        assert result.effect_size < -1

    def test_paired_t_requires_equal_length(self) -> None:
        with pytest.raises(AppError):
            inference.paired_t_test([1, 2, 3], [1, 2])

    def test_paired_t_detects_consistent_increase(self) -> None:
        before = [10, 12, 11, 13, 10, 12]
        after = [15, 17, 16, 18, 15, 17]
        result = inference.paired_t_test(before, after)
        assert result.reject_null is True

    def test_two_proportion_z_matches_known_case(self) -> None:
        # control 10% (1000/10000), treatment 12.5% (1250/10000) — a real, detectable uplift.
        result = inference.two_proportion_z_test(1250, 10000, 1000, 10000)
        assert result.reject_null is True
        assert result.effect_size == pytest.approx(-0.025, abs=1e-9)

    def test_two_proportion_z_validates_bounds(self) -> None:
        with pytest.raises(AppError):
            inference.two_proportion_z_test(1500, 1000, 100, 1000)

    def test_chi_square_independence(self) -> None:
        result = inference.chi_square_test([[30, 10], [20, 40]])
        assert result.reject_null is True
        assert result.degrees_of_freedom == 1

    def test_chi_square_requires_2x2_minimum(self) -> None:
        with pytest.raises(AppError):
            inference.chi_square_test([[5]])

    def test_mann_whitney_detects_shift(self) -> None:
        result = inference.mann_whitney_test([1, 2, 3, 4, 5], [10, 11, 12, 13, 14])
        assert result.reject_null is True

    def test_anova_detects_group_difference(self) -> None:
        result = inference.one_way_anova([1, 2, 3], [10, 11, 12], [20, 21, 22])
        assert result.reject_null is True
        assert result.effect_size > 0.9

    def test_anova_requires_two_groups(self) -> None:
        with pytest.raises(AppError):
            inference.one_way_anova([1, 2, 3])

    def test_correlation_test_pearson_perfect_positive(self) -> None:
        result = inference.correlation_test([1, 2, 3, 4, 5], [2, 4, 6, 8, 10], method="pearson")
        assert result.statistic == pytest.approx(1.0, abs=1e-9)
        assert result.reject_null is True

    def test_correlation_test_spearman(self) -> None:
        result = inference.correlation_test([1, 2, 3, 4, 5], [1, 4, 9, 16, 25], method="spearman")
        assert result.statistic == pytest.approx(1.0, abs=1e-9)

    def test_invalid_alternative_rejected(self) -> None:
        with pytest.raises(AppError):
            inference.one_sample_t_test([1, 2, 3], population_mean=0, alternative="bogus")


class TestRegression:
    def test_simple_linear_regression_perfect_fit(self) -> None:
        result = regression.simple_linear_regression([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
        assert result.r_squared == pytest.approx(1.0, abs=1e-9)
        assert result.coefficients[0].value == pytest.approx(2.0, abs=1e-6)
        assert result.intercept.value == pytest.approx(0.0, abs=1e-6)

    def test_multiple_regression_two_predictors(self) -> None:
        # y = 2*x1 + 3*x2 exactly
        x1 = [1, 2, 3, 4, 5, 6]
        x2 = [1, 1, 2, 2, 3, 3]
        y = [2 * a + 3 * b for a, b in zip(x1, x2, strict=True)]
        result = regression.multiple_regression({"x1": x1, "x2": x2}, y)
        assert result.r_squared == pytest.approx(1.0, abs=1e-6)
        coef_by_name = {c.name: c.value for c in result.coefficients}
        assert coef_by_name["x1"] == pytest.approx(2.0, abs=1e-4)
        assert coef_by_name["x2"] == pytest.approx(3.0, abs=1e-4)

    def test_regression_requires_enough_observations(self) -> None:
        with pytest.raises(AppError):
            regression.simple_linear_regression([1, 2], [1, 2])

    def test_regression_mismatched_lengths_rejected(self) -> None:
        with pytest.raises(AppError):
            regression.multiple_regression({"x": [1, 2, 3]}, [1, 2])

    def test_multicollinearity_flagged(self) -> None:
        x1 = [1, 2, 3, 4, 5, 6, 7, 8]
        x2 = [1.01, 2.02, 2.99, 4.01, 5.02, 5.98, 7.01, 8.02]  # near-identical to x1
        y = [1, 3, 2, 5, 4, 6, 8, 7]
        result = regression.multiple_regression({"x1": x1, "x2": x2}, y)
        assert result.multicollinearity_warning is not None

    def test_no_multicollinearity_warning_for_uncorrelated_predictors(self) -> None:
        x1 = [1, 2, 3, 4, 5, 6, 7, 8]
        x2 = [5, 1, 4, 2, 8, 3, 7, 6]
        y = [1, 3, 2, 5, 4, 6, 8, 7]
        result = regression.multiple_regression({"x1": x1, "x2": x2}, y)
        assert result.multicollinearity_warning is None
