"""Classical hypothesis tests.

Two design decisions worth calling out, because they are the ones most
implementations get wrong:

1. The two-proportion z-test uses a **pooled** standard error for the test
   statistic (correct under H0: p_control == p_treatment) but an **unpooled**
   standard error for the confidence interval (we are no longer assuming the
   null when we estimate the size of the difference). Using one SE for both
   produces intervals that disagree with the p-value at the boundary.

2. The t-test is **Welch's**, never Student's pooled-variance version. Equal
   variance between an experiment's arms is an assumption nobody checks and
   the treatment often violates it.
"""

import math

import numpy as np
from scipy import stats

from app.stats.models import (
    Alternative,
    EffectSize,
    GroupSummary,
    Interval,
    MetricType,
    TestName,
    TestResult,
)


def _p_from_alternative(statistic: float, dist, alternative: Alternative) -> float:
    """Two-sided by default. ``greater`` means "treatment beats control"."""
    if alternative == "two-sided":
        return float(2.0 * dist.sf(abs(statistic)))
    if alternative == "greater":
        return float(dist.sf(statistic))
    return float(dist.cdf(statistic))


def _critical_value(dist, alpha: float, alternative: Alternative) -> float:
    """Critical value for the interval. One-sided tests still get a two-sided
    interval — a one-sided interval unbounded on one end tells a stakeholder
    nothing useful about the plausible size of the effect."""
    return float(dist.isf(alpha / 2.0))


def two_proportion_z_test(
    control_conversions: int,
    control_n: int,
    treatment_conversions: int,
    treatment_n: int,
    alpha: float = 0.05,
    alternative: Alternative = "two-sided",
) -> TestResult:
    """Two-proportion z-test for conversion-rate style metrics."""
    if control_n <= 0 or treatment_n <= 0:
        raise ValueError("Both groups need at least one observation")
    if not 0 <= control_conversions <= control_n:
        raise ValueError("control_conversions must be between 0 and control_n")
    if not 0 <= treatment_conversions <= treatment_n:
        raise ValueError("treatment_conversions must be between 0 and treatment_n")

    p_control = control_conversions / control_n
    p_treatment = treatment_conversions / treatment_n
    diff = p_treatment - p_control

    # Test statistic: pooled SE, because under the null the two rates are equal.
    p_pooled = (control_conversions + treatment_conversions) / (control_n + treatment_n)
    se_pooled = math.sqrt(p_pooled * (1 - p_pooled) * (1 / control_n + 1 / treatment_n))

    if se_pooled == 0:
        # Both arms all-converted or all-failed: no evidence of a difference.
        z, p_value = 0.0, 1.0
    else:
        z = diff / se_pooled
        p_value = _p_from_alternative(z, stats.norm, alternative)

    # Interval: unpooled SE, because here we are estimating the difference,
    # not testing whether it is zero.
    se_unpooled = math.sqrt(
        p_control * (1 - p_control) / control_n + p_treatment * (1 - p_treatment) / treatment_n
    )
    z_crit = _critical_value(stats.norm, alpha, alternative)
    margin = z_crit * se_unpooled

    # Relative lift interval via the log risk ratio — the natural scale for a
    # ratio, and it keeps the interval from crossing into impossible values.
    relative_pct: float | None = None
    relative_interval: Interval | None = None
    if p_control > 0:
        relative_pct = diff / p_control * 100.0
        if p_treatment > 0 and p_control < 1 and p_treatment < 1:
            log_rr = math.log(p_treatment / p_control)
            se_log_rr = math.sqrt(
                (1 - p_control) / (control_n * p_control)
                + (1 - p_treatment) / (treatment_n * p_treatment)
            )
            relative_interval = Interval(
                lower=(math.exp(log_rr - z_crit * se_log_rr) - 1) * 100.0,
                upper=(math.exp(log_rr + z_crit * se_log_rr) - 1) * 100.0,
                level=1 - alpha,
            )

    # Cohen's h — the standard effect size for a difference of proportions.
    cohens_h = 2 * math.asin(math.sqrt(p_treatment)) - 2 * math.asin(math.sqrt(p_control))

    significant = p_value < alpha
    absolute_interval = Interval(lower=diff - margin, upper=diff + margin, level=1 - alpha)

    return TestResult(
        test=TestName.TWO_PROPORTION_Z,
        test_label="Two-proportion z-test",
        metric_type=MetricType.BINARY,
        alternative=alternative,
        alpha=alpha,
        control=GroupSummary(
            name="Control",
            n=control_n,
            conversions=control_conversions,
            rate=p_control,
        ),
        treatment=GroupSummary(
            name="Treatment",
            n=treatment_n,
            conversions=treatment_conversions,
            rate=p_treatment,
        ),
        statistic=z,
        p_value=p_value,
        degrees_of_freedom=None,
        significant=significant,
        effect=EffectSize(
            absolute=diff,
            absolute_interval=absolute_interval,
            relative_pct=relative_pct,
            relative_interval=relative_interval,
            standardised=cohens_h,
            standardised_name="Cohen's h",
        ),
        assumptions=[
            "Each observation is independent — one user counted once, not once per session.",
            "Users were randomly assigned to control or treatment.",
            "Both groups have enough conversions for the normal approximation "
            "(a common rule of thumb is at least 10 conversions and 10 non-conversions per group).",
        ],
        interpretation=_interpret(
            significant=significant,
            p_value=p_value,
            alpha=alpha,
            absolute_interval=absolute_interval,
            units="percentage points",
            scale=100.0,
        ),
    )


def welch_t_test(
    control: np.ndarray | list[float],
    treatment: np.ndarray | list[float],
    alpha: float = 0.05,
    alternative: Alternative = "two-sided",
) -> TestResult:
    """Welch's two-sample t-test for continuous metrics.

    Welch's, not Student's: we do not assume the two arms share a variance.
    """
    control_arr = np.asarray(control, dtype=float)
    treatment_arr = np.asarray(treatment, dtype=float)

    n_control, n_treatment = control_arr.size, treatment_arr.size
    if n_control < 2 or n_treatment < 2:
        raise ValueError("Each group needs at least two observations for a t-test")

    mean_control = float(control_arr.mean())
    mean_treatment = float(treatment_arr.mean())
    # ddof=1 — sample variance, not population variance.
    var_control = float(control_arr.var(ddof=1))
    var_treatment = float(treatment_arr.var(ddof=1))

    diff = mean_treatment - mean_control
    se = math.sqrt(var_control / n_control + var_treatment / n_treatment)

    if se == 0:
        t_stat, p_value, df = 0.0, 1.0, float(n_control + n_treatment - 2)
        margin = 0.0
    else:
        # Welch–Satterthwaite degrees of freedom.
        term_control = var_control / n_control
        term_treatment = var_treatment / n_treatment
        df = (term_control + term_treatment) ** 2 / (
            term_control**2 / (n_control - 1) + term_treatment**2 / (n_treatment - 1)
        )
        t_stat = diff / se
        t_dist = stats.t(df)
        p_value = _p_from_alternative(t_stat, t_dist, alternative)
        margin = _critical_value(t_dist, alpha, alternative) * se

    # Cohen's d against the pooled SD, then Hedges' g to correct the small-sample bias.
    pooled_sd = math.sqrt(
        ((n_control - 1) * var_control + (n_treatment - 1) * var_treatment)
        / (n_control + n_treatment - 2)
    )
    cohens_d = diff / pooled_sd if pooled_sd > 0 else 0.0
    correction = 1 - 3 / (4 * (n_control + n_treatment) - 9)
    hedges_g = cohens_d * correction

    relative_pct = (diff / mean_control * 100.0) if mean_control != 0 else None
    relative_interval = (
        Interval(
            lower=(diff - margin) / mean_control * 100.0,
            upper=(diff + margin) / mean_control * 100.0,
            level=1 - alpha,
        )
        if mean_control > 0
        else None
    )

    significant = p_value < alpha
    absolute_interval = Interval(lower=diff - margin, upper=diff + margin, level=1 - alpha)

    return TestResult(
        test=TestName.WELCH_T,
        test_label="Welch's two-sample t-test",
        metric_type=MetricType.CONTINUOUS,
        alternative=alternative,
        alpha=alpha,
        control=GroupSummary(
            name="Control",
            n=n_control,
            mean=mean_control,
            std_dev=math.sqrt(var_control),
        ),
        treatment=GroupSummary(
            name="Treatment",
            n=n_treatment,
            mean=mean_treatment,
            std_dev=math.sqrt(var_treatment),
        ),
        statistic=t_stat,
        p_value=p_value,
        degrees_of_freedom=df,
        significant=significant,
        effect=EffectSize(
            absolute=diff,
            absolute_interval=absolute_interval,
            relative_pct=relative_pct,
            relative_interval=relative_interval,
            standardised=hedges_g,
            standardised_name="Hedges' g",
        ),
        assumptions=[
            "Each observation is independent.",
            "Users were randomly assigned to control or treatment.",
            "The group means are approximately normally distributed. With large "
            "samples the Central Limit Theorem usually covers this; with small or "
            "heavily skewed samples, prefer the non-parametric test.",
            "Equal variances are NOT assumed — this is Welch's test.",
        ],
        interpretation=_interpret(
            significant=significant,
            p_value=p_value,
            alpha=alpha,
            absolute_interval=absolute_interval,
            units="units",
            scale=1.0,
        ),
    )


def _interpret(
    *,
    significant: bool,
    p_value: float,
    alpha: float,
    absolute_interval: Interval,
    units: str,
    scale: float,
) -> str:
    """A short plain-English reading of the result.

    The full verdict layer arrives in a later phase; this is the one-line
    version so raw statistics are never the only thing on screen.
    """
    lower = absolute_interval.lower * scale
    upper = absolute_interval.upper * scale
    confidence = int(round(absolute_interval.level * 100))

    if significant:
        direction = "an increase" if absolute_interval.lower > 0 else "a decrease"
        if lower < 0 < upper:
            direction = "a change"
        return (
            f"The difference is statistically significant (p = {p_value:.4f}, below the "
            f"{alpha:g} threshold). The data is consistent with {direction} of between "
            f"{lower:.2f} and {upper:.2f} {units}, at {confidence}% confidence."
        )

    return (
        f"The difference is not statistically significant (p = {p_value:.4f}, above the "
        f"{alpha:g} threshold). The true effect could plausibly be anywhere from "
        f"{lower:.2f} to {upper:.2f} {units} — which includes no effect at all. "
        "That is not the same as proving there is no effect."
    )
