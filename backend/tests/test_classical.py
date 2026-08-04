"""Unit tests for the classical hypothesis tests.

Strategy: cross-check against scipy/statsmodels where an independent
implementation exists, check hand-computable cases where it doesn't, and
verify the properties that matter (interval covers the truth, p-value and
interval agree).
"""

import math

import numpy as np
import pytest
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest

from app.stats.classical import two_proportion_z_test, welch_t_test


class TestWelchTTest:
    def test_matches_scipy_exactly(self) -> None:
        rng = np.random.default_rng(11)
        control = rng.normal(100, 15, 400)
        # Different variance in the treatment arm — the case Student's t-test
        # gets wrong and Welch's handles.
        treatment = rng.normal(104, 25, 350)

        result = welch_t_test(control, treatment)
        expected = stats.ttest_ind(treatment, control, equal_var=False)

        assert result.statistic == pytest.approx(expected.statistic, rel=1e-12)
        assert result.p_value == pytest.approx(expected.pvalue, rel=1e-12)
        assert result.degrees_of_freedom == pytest.approx(expected.df, rel=1e-12)

    def test_confidence_interval_matches_scipy(self) -> None:
        rng = np.random.default_rng(5)
        control = rng.normal(50, 8, 120)
        treatment = rng.normal(53, 12, 90)

        result = welch_t_test(control, treatment, alpha=0.05)
        expected = stats.ttest_ind(treatment, control, equal_var=False).confidence_interval(0.95)

        assert result.effect.absolute_interval.lower == pytest.approx(expected.low, rel=1e-10)
        assert result.effect.absolute_interval.upper == pytest.approx(expected.high, rel=1e-10)

    def test_does_not_assume_equal_variance(self) -> None:
        """Welch's and Student's must disagree when variances differ wildly."""
        rng = np.random.default_rng(3)
        control = rng.normal(0, 1, 50)
        treatment = rng.normal(0.5, 10, 500)

        welch = welch_t_test(control, treatment)
        student = stats.ttest_ind(treatment, control, equal_var=True)

        assert welch.p_value != pytest.approx(student.pvalue, rel=1e-3)
        # Welch's df is pulled well below the pooled n1+n2-2 = 548.
        assert welch.degrees_of_freedom is not None
        assert welch.degrees_of_freedom < 548

    def test_p_value_and_interval_agree(self) -> None:
        """Both derive from the same SE, so significance and an interval that
        excludes zero must always coincide."""
        rng = np.random.default_rng(21)
        for _ in range(25):
            control = rng.normal(10, 3, 60)
            treatment = rng.normal(10.8, 3, 60)
            result = welch_t_test(control, treatment, alpha=0.05)
            excludes_zero = (
                result.effect.absolute_interval.lower > 0
                or result.effect.absolute_interval.upper < 0
            )
            assert result.significant == excludes_zero

    def test_hedges_g_shrinks_cohens_d(self) -> None:
        rng = np.random.default_rng(9)
        control = rng.normal(0, 1, 12)
        treatment = rng.normal(1, 1, 12)
        result = welch_t_test(control, treatment)

        var_c = control.var(ddof=1)
        var_t = treatment.var(ddof=1)
        pooled = math.sqrt(((12 - 1) * var_c + (12 - 1) * var_t) / 22)
        cohens_d = (treatment.mean() - control.mean()) / pooled

        assert result.effect.standardised_name == "Hedges' g"
        assert abs(result.effect.standardised) < abs(cohens_d)

    def test_identical_groups_are_not_significant(self) -> None:
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = welch_t_test(data, data)
        assert result.p_value == pytest.approx(1.0)
        assert not result.significant
        assert result.effect.absolute == pytest.approx(0.0)

    def test_zero_variance_does_not_divide_by_zero(self) -> None:
        constant = [7.0] * 20
        result = welch_t_test(constant, constant)
        assert result.p_value == 1.0
        assert not result.significant

    def test_rejects_groups_that_are_too_small(self) -> None:
        with pytest.raises(ValueError, match="at least two observations"):
            welch_t_test([1.0], [2.0, 3.0])

    def test_one_sided_alternative_halves_the_p_value(self) -> None:
        rng = np.random.default_rng(4)
        control = rng.normal(0, 1, 200)
        treatment = rng.normal(0.4, 1, 200)

        two_sided = welch_t_test(control, treatment, alternative="two-sided")
        greater = welch_t_test(control, treatment, alternative="greater")

        assert greater.p_value == pytest.approx(two_sided.p_value / 2, rel=1e-9)


class TestTwoProportionZTest:
    def test_matches_statsmodels(self) -> None:
        result = two_proportion_z_test(
            control_conversions=200, control_n=2000, treatment_conversions=250, treatment_n=2000
        )
        # statsmodels orders the arms as given; ours is treatment - control.
        expected_z, expected_p = proportions_ztest(
            count=np.array([250, 200]), nobs=np.array([2000, 2000])
        )

        assert result.statistic == pytest.approx(expected_z, rel=1e-10)
        assert result.p_value == pytest.approx(expected_p, rel=1e-10)

    def test_hand_computed_example(self) -> None:
        """Worked by hand: p1=0.10, p2=0.12, n=1000 each.

        pooled = 0.11
        SE     = sqrt(0.11 * 0.89 * (2/1000)) = 0.01399286
        z      = 0.02 / SE                    = 1.42930085
        p      = 2 * P(Z > 1.42930085)        = 0.15291778
        """
        result = two_proportion_z_test(100, 1000, 120, 1000)

        se_pooled = math.sqrt(0.11 * 0.89 * (2 / 1000))
        assert se_pooled == pytest.approx(0.01399286, abs=1e-8)
        assert result.statistic == pytest.approx(0.02 / se_pooled, rel=1e-12)
        assert result.statistic == pytest.approx(1.42930085, abs=1e-8)
        assert result.p_value == pytest.approx(0.15291778, abs=1e-8)
        assert not result.significant

    def test_interval_uses_unpooled_standard_error(self) -> None:
        """The interval must NOT reuse the pooled SE from the test statistic."""
        result = two_proportion_z_test(100, 1000, 120, 1000, alpha=0.05)

        se_unpooled = math.sqrt(0.10 * 0.90 / 1000 + 0.12 * 0.88 / 1000)
        z_crit = stats.norm.isf(0.025)
        assert result.effect.absolute_interval.lower == pytest.approx(
            0.02 - z_crit * se_unpooled, rel=1e-12
        )
        assert result.effect.absolute_interval.upper == pytest.approx(
            0.02 + z_crit * se_unpooled, rel=1e-12
        )

        se_pooled = math.sqrt(0.11 * 0.89 * (2 / 1000))
        assert se_unpooled != pytest.approx(se_pooled, rel=1e-6)

    def test_relative_lift_and_its_interval(self) -> None:
        result = two_proportion_z_test(100, 1000, 120, 1000)
        assert result.effect.relative_pct == pytest.approx(20.0)

        interval = result.effect.relative_interval
        assert interval is not None
        # A 20% lift that is not significant must have an interval spanning zero.
        assert interval.lower < 0 < interval.upper
        assert interval.lower < 20.0 < interval.upper

    def test_cohens_h(self) -> None:
        result = two_proportion_z_test(100, 1000, 120, 1000)
        expected = 2 * math.asin(math.sqrt(0.12)) - 2 * math.asin(math.sqrt(0.10))
        assert result.effect.standardised == pytest.approx(expected, rel=1e-12)
        assert result.effect.standardised_name == "Cohen's h"

    def test_degenerate_all_or_nothing_groups(self) -> None:
        assert two_proportion_z_test(0, 100, 0, 100).p_value == 1.0
        assert two_proportion_z_test(100, 100, 100, 100).p_value == 1.0

    def test_rejects_impossible_inputs(self) -> None:
        with pytest.raises(ValueError, match="between 0 and control_n"):
            two_proportion_z_test(150, 100, 10, 100)
        with pytest.raises(ValueError, match="at least one observation"):
            two_proportion_z_test(0, 0, 10, 100)

    def test_never_reports_a_p_value_without_an_effect_size(self) -> None:
        """A spec rule: a p-value alone is not a business answer."""
        result = two_proportion_z_test(100, 1000, 120, 1000)
        assert result.effect.absolute is not None
        assert result.effect.absolute_interval is not None
        assert result.effect.standardised is not None
        assert result.assumptions
        assert result.interpretation
