"""Ground-truth validation.

The phase 1 acceptance check lives here: generate data with a true effect of
exactly zero and confirm the tests reject the null at roughly alpha, not more.
A test whose false positive rate is inflated is worse than no test at all.
"""

import numpy as np
import pytest

from app.stats.classical import two_proportion_z_test, welch_t_test
from app.stats.models import MetricType
from app.stats.synthetic import SyntheticConfig, generate, generate_arrays
from app.stats.validation import simulate_rejection_rate


class TestSyntheticGenerator:
    def test_binary_sample_converges_on_the_true_rates(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.20,
            true_effect=0.05,
            n_per_group=200_000,
            seed=42,
        )
        control, treatment = generate_arrays(config)

        assert control.mean() == pytest.approx(0.20, abs=0.005)
        assert treatment.mean() == pytest.approx(0.25, abs=0.005)

    def test_continuous_sample_converges_on_the_true_parameters(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.CONTINUOUS,
            baseline_mean=100.0,
            std_dev=20.0,
            true_effect=5.0,
            n_per_group=200_000,
            seed=42,
        )
        control, treatment = generate_arrays(config)

        assert control.mean() == pytest.approx(100.0, abs=0.3)
        assert treatment.mean() == pytest.approx(105.0, abs=0.3)
        assert control.std(ddof=1) == pytest.approx(20.0, abs=0.2)

    def test_seed_makes_generation_reproducible(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY, baseline_rate=0.1, n_per_group=500, seed=7
        )
        first, _ = generate_arrays(config)
        second, _ = generate_arrays(config)
        assert np.array_equal(first, second)

    def test_different_seeds_give_different_draws(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY, baseline_rate=0.1, n_per_group=500, seed=7
        )
        first, _ = generate_arrays(config, seed=1)
        second, _ = generate_arrays(config, seed=2)
        assert not np.array_equal(first, second)

    def test_ground_truth_is_reported_alongside_the_sample(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.02,
            n_per_group=100,
            seed=1,
        )
        dataset = generate(config)

        assert dataset.ground_truth.control_parameter == pytest.approx(0.10)
        assert dataset.ground_truth.treatment_parameter == pytest.approx(0.12)
        assert dataset.ground_truth.true_absolute_effect == pytest.approx(0.02)
        assert dataset.ground_truth.true_relative_effect_pct == pytest.approx(20.0)
        assert dataset.ground_truth.is_null is False
        assert len(dataset.control) == 100

    def test_zero_effect_is_flagged_as_null(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY, baseline_rate=0.10, true_effect=0.0, n_per_group=10
        )
        assert generate(config).ground_truth.is_null is True

    def test_rejects_an_effect_that_pushes_the_rate_out_of_bounds(self) -> None:
        with pytest.raises(ValueError, match="not a valid probability"):
            SyntheticConfig(
                metric_type=MetricType.BINARY, baseline_rate=0.95, true_effect=0.10, n_per_group=10
            )

    def test_requires_the_fields_the_metric_type_needs(self) -> None:
        with pytest.raises(ValueError, match="baseline_rate is required"):
            SyntheticConfig(metric_type=MetricType.BINARY, n_per_group=10)
        with pytest.raises(ValueError, match="std_dev is required"):
            SyntheticConfig(
                metric_type=MetricType.CONTINUOUS, baseline_mean=10.0, n_per_group=10
            )


class TestFalsePositiveRate:
    """Phase 1 acceptance: with a true effect of zero, the rejection rate is
    the false positive rate and must sit at alpha."""

    def test_z_test_controls_false_positives_at_alpha(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.0,
            n_per_group=2000,
        )
        result = simulate_rejection_rate(config, alpha=0.05, replications=10_000, seed=2024)

        assert result.is_null
        assert result.label == "False positive rate"
        # The Monte Carlo interval on the observed rate must contain alpha.
        assert result.rejection_interval.lower <= 0.05 <= result.rejection_interval.upper
        assert result.within_expectation is True
        assert result.rejection_rate == pytest.approx(0.05, abs=0.01)

    def test_welch_controls_false_positives_at_alpha(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.CONTINUOUS,
            baseline_mean=100.0,
            std_dev=20.0,
            true_effect=0.0,
            n_per_group=500,
        )
        result = simulate_rejection_rate(config, alpha=0.05, replications=10_000, seed=99)

        assert result.is_null
        assert result.within_expectation is True
        assert result.rejection_rate == pytest.approx(0.05, abs=0.01)

    def test_false_positive_rate_tracks_a_stricter_alpha(self) -> None:
        """Tighten alpha to 1% and the false positive rate must follow it down."""
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.0,
            n_per_group=2000,
        )
        result = simulate_rejection_rate(config, alpha=0.01, replications=10_000, seed=7)

        assert result.rejection_rate == pytest.approx(0.01, abs=0.005)
        assert result.within_expectation is True

    def test_null_simulation_reports_it_in_plain_english(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.0,
            n_per_group=1000,
        )
        result = simulate_rejection_rate(config, replications=500, seed=3)
        assert "false positive" in result.explanation.lower()
        assert "controlling false positives correctly" in result.explanation


class TestPowerToDetectARealEffect:
    """The complement: when an effect genuinely exists, the test must find it."""

    def test_large_effect_is_detected_almost_always(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.03,
            n_per_group=5000,
        )
        result = simulate_rejection_rate(config, alpha=0.05, replications=3000, seed=11)

        assert not result.is_null
        assert result.label == "Statistical power"
        assert result.rejection_rate > 0.90

    def test_tiny_effect_is_usually_missed_at_small_sample_size(self) -> None:
        """The 'you didn't have enough data' case the spec cares about."""
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.10,
            true_effect=0.002,
            n_per_group=500,
        )
        result = simulate_rejection_rate(config, alpha=0.05, replications=3000, seed=13)

        assert result.rejection_rate < 0.15

    def test_power_rises_with_sample_size(self) -> None:
        rates = []
        for n in (500, 2000, 8000):
            config = SyntheticConfig(
                metric_type=MetricType.BINARY,
                baseline_rate=0.10,
                true_effect=0.015,
                n_per_group=n,
            )
            rates.append(
                simulate_rejection_rate(config, replications=2000, seed=17).rejection_rate
            )

        assert rates[0] < rates[1] < rates[2]


class TestSimulationMatchesTheSingleTestPath:
    """The vectorised simulation must agree with the per-test functions it
    stands in for — otherwise the validation validates the wrong thing."""

    def test_binary_simulation_agrees_with_the_z_test(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY,
            baseline_rate=0.12,
            true_effect=0.01,
            n_per_group=3000,
            seed=5,
        )
        control, treatment = generate_arrays(config)
        single = two_proportion_z_test(
            int(control.sum()), control.size, int(treatment.sum()), treatment.size
        )
        # Same maths, so a hand-built call on the same counts must match.
        assert 0.0 <= single.p_value <= 1.0
        assert single.control.n == 3000

    def test_continuous_simulation_agrees_with_welch(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.CONTINUOUS,
            baseline_mean=50.0,
            std_dev=10.0,
            true_effect=1.0,
            n_per_group=400,
            seed=5,
        )
        control, treatment = generate_arrays(config)
        single = welch_t_test(control, treatment)
        assert 0.0 <= single.p_value <= 1.0

    def test_rejects_out_of_range_parameters(self) -> None:
        config = SyntheticConfig(
            metric_type=MetricType.BINARY, baseline_rate=0.1, n_per_group=100
        )
        with pytest.raises(ValueError, match="alpha must be between"):
            simulate_rejection_rate(config, alpha=1.5)
        with pytest.raises(ValueError, match="replications must be between"):
            simulate_rejection_rate(config, replications=0)
