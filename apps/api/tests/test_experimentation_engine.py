"""Unit tests for app/experimentation_engine/* — pure statsmodels/numpy
computations, no database/API involved. Covers sample size, power, A/B
analysis, and simulation (Phase 6 spec sections 19-24)."""

from __future__ import annotations

import pytest

from app.core.errors import AppError
from app.experimentation_engine import analyze, sample_size, simulate


class TestSampleSize:
    def test_sample_size_positive_and_reasonable(self) -> None:
        result = sample_size.sample_size_for_proportions(0.1, 0.2)
        assert result.sample_size_per_variant > 0
        assert result.total_sample_size == result.sample_size_per_variant * 2

    def test_smaller_effect_needs_more_samples(self) -> None:
        big_effect = sample_size.sample_size_for_proportions(0.1, 0.5)
        small_effect = sample_size.sample_size_for_proportions(0.1, 0.05)
        assert small_effect.sample_size_per_variant > big_effect.sample_size_per_variant

    def test_higher_power_needs_more_samples(self) -> None:
        low_power = sample_size.sample_size_for_proportions(0.1, 0.2, power=0.7)
        high_power = sample_size.sample_size_for_proportions(0.1, 0.2, power=0.95)
        assert high_power.sample_size_per_variant > low_power.sample_size_per_variant

    def test_invalid_baseline_rejected(self) -> None:
        with pytest.raises(AppError):
            sample_size.sample_size_for_proportions(1.5, 0.2)

    def test_uplift_pushing_rate_out_of_bounds_rejected(self) -> None:
        with pytest.raises(AppError):
            sample_size.sample_size_for_proportions(0.9, 0.5)

    def test_power_for_sample_size_matches_target_roughly(self) -> None:
        ss = sample_size.sample_size_for_proportions(0.1, 0.2, power=0.8)
        power_result = sample_size.power_for_sample_size(0.1, ss.sample_size_per_variant, 0.2)
        assert power_result.achieved_power == pytest.approx(0.8, abs=0.02)

    def test_larger_sample_increases_power(self) -> None:
        low = sample_size.power_for_sample_size(0.1, 500, 0.2)
        high = sample_size.power_for_sample_size(0.1, 5000, 0.2)
        assert high.achieved_power > low.achieved_power


class TestAnalyze:
    def test_analyze_detects_significant_uplift(self) -> None:
        result = analyze.analyze_ab_test(10000, 1000, 10000, 1250)
        assert result.is_statistically_significant is True
        assert result.relative_uplift == pytest.approx(0.25, abs=1e-9)
        assert result.verdict == "Ship-worthy evidence"

    def test_analyze_small_sample_inconclusive(self) -> None:
        result = analyze.analyze_ab_test(100, 10, 100, 12)
        assert result.is_statistically_significant is False
        assert result.verdict == "Inconclusive"

    def test_analyze_practical_significance_threshold(self) -> None:
        result = analyze.analyze_ab_test(10000, 1000, 10000, 1250, minimum_practical_effect=0.05)
        assert result.is_practically_significant is False
        assert result.verdict == "Statistically significant but too small to matter"

    def test_analyze_rejects_invalid_conversions(self) -> None:
        with pytest.raises(AppError):
            analyze.analyze_ab_test(100, 200, 100, 10)

    def test_analyze_rejects_zero_users(self) -> None:
        with pytest.raises(AppError):
            analyze.analyze_ab_test(0, 0, 100, 10)


class TestSimulate:
    def test_simulate_is_deterministic_for_same_seed(self) -> None:
        r1 = simulate.simulate_ab_test(0.1, 0.15, 2000, num_simulations=200, seed=7)
        r2 = simulate.simulate_ab_test(0.1, 0.15, 2000, num_simulations=200, seed=7)
        assert r1.empirical_power == r2.empirical_power
        assert r1.significant_count == r2.significant_count
        assert r1.example_run == r2.example_run

    def test_simulate_different_seed_can_differ(self) -> None:
        r1 = simulate.simulate_ab_test(0.1, 0.11, 300, num_simulations=100, seed=1)
        r2 = simulate.simulate_ab_test(0.1, 0.11, 300, num_simulations=100, seed=2)
        # Not strictly guaranteed to differ, but with a small effect + small n this is
        # true with overwhelming probability — if it ever flakes, the seeds chosen here
        # should be revisited, not the assertion loosened.
        assert (r1.significant_count, r1.example_run) != (r2.significant_count, r2.example_run)

    def test_simulate_more_power_with_larger_effect(self) -> None:
        small_effect = simulate.simulate_ab_test(0.1, 0.11, 2000, num_simulations=300, seed=1)
        large_effect = simulate.simulate_ab_test(0.1, 0.30, 2000, num_simulations=300, seed=1)
        assert large_effect.empirical_power > small_effect.empirical_power

    def test_simulate_rejects_invalid_rate(self) -> None:
        with pytest.raises(AppError):
            simulate.simulate_ab_test(1.5, 0.1, 100)

    def test_simulate_rejects_too_many_simulations(self) -> None:
        with pytest.raises(AppError):
            simulate.simulate_ab_test(0.1, 0.2, 100, num_simulations=999999)
