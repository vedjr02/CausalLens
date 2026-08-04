"""Validating the methods against known ground truth.

Run the same test many times on freshly simulated data whose true effect we
set ourselves, and count how often it declares significance:

* true effect = 0  -> that rate is the **false positive rate**, and it should
  land close to alpha. If it doesn't, the method is broken.
* true effect != 0 -> that rate is the **empirical power**.

This is the check that turns "we called scipy" into "we showed it works".
"""

import numpy as np
from pydantic import BaseModel, Field
from scipy import stats

from app.stats.models import Alternative, Interval, MetricType
from app.stats.synthetic import SyntheticConfig

MAX_REPLICATIONS = 20_000


class RejectionRateResult(BaseModel):
    """How often the test declared significance across many replications."""

    replications: int
    alpha: float
    rejection_rate: float
    rejection_interval: Interval = Field(
        description="Monte Carlo interval on the rate above"
    )
    is_null: bool
    true_absolute_effect: float
    expected_rate: float | None = Field(
        None, description="Under the null this is alpha; under an effect it is unknown a priori"
    )
    within_expectation: bool | None = None
    label: str
    explanation: str


def _binary_rejection_rate(
    config: SyntheticConfig,
    alpha: float,
    replications: int,
    rng: np.random.Generator,
    alternative: Alternative,
) -> np.ndarray:
    """Vectorised two-proportion z-test across all replications at once.

    Conversion counts are the sufficient statistic, so we draw binomial counts
    directly rather than simulating individual users — mathematically identical,
    orders of magnitude faster.
    """
    n = config.n_per_group
    x_control = rng.binomial(n, config.control_parameter, size=replications)
    x_treatment = rng.binomial(n, config.treatment_parameter, size=replications)

    p_control = x_control / n
    p_treatment = x_treatment / n
    p_pooled = (x_control + x_treatment) / (2 * n)

    se = np.sqrt(p_pooled * (1 - p_pooled) * (2 / n))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.where(se > 0, (p_treatment - p_control) / se, 0.0)

    if alternative == "two-sided":
        return 2 * stats.norm.sf(np.abs(z))
    if alternative == "greater":
        return stats.norm.sf(z)
    return stats.norm.cdf(z)


def _continuous_rejection_rate(
    config: SyntheticConfig,
    alpha: float,
    replications: int,
    rng: np.random.Generator,
    alternative: Alternative,
) -> np.ndarray:
    """Vectorised Welch's t-test across all replications at once."""
    n = config.n_per_group
    assert config.std_dev is not None

    control = rng.normal(config.control_parameter, config.std_dev, size=(replications, n))
    treatment = rng.normal(config.treatment_parameter, config.std_dev, size=(replications, n))

    mean_c = control.mean(axis=1)
    mean_t = treatment.mean(axis=1)
    var_c = control.var(axis=1, ddof=1)
    var_t = treatment.var(axis=1, ddof=1)

    term_c = var_c / n
    term_t = var_t / n
    se = np.sqrt(term_c + term_t)
    df = (term_c + term_t) ** 2 / (term_c**2 / (n - 1) + term_t**2 / (n - 1))

    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(se > 0, (mean_t - mean_c) / se, 0.0)

    if alternative == "two-sided":
        return 2 * stats.t.sf(np.abs(t), df)
    if alternative == "greater":
        return stats.t.sf(t, df)
    return stats.t.cdf(t, df)


def simulate_rejection_rate(
    config: SyntheticConfig,
    alpha: float = 0.05,
    replications: int = 2000,
    seed: int | None = None,
    alternative: Alternative = "two-sided",
) -> "RejectionRateResult":
    """Re-run the experiment ``replications`` times and count significant results."""
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    if not 1 <= replications <= MAX_REPLICATIONS:
        raise ValueError(f"replications must be between 1 and {MAX_REPLICATIONS}")

    rng = np.random.default_rng(seed if seed is not None else config.seed)

    if config.metric_type is MetricType.BINARY:
        p_values = _binary_rejection_rate(config, alpha, replications, rng, alternative)
        test_label = "two-proportion z-test"
    else:
        p_values = _continuous_rejection_rate(config, alpha, replications, rng, alternative)
        test_label = "Welch's t-test"

    rejections = int(np.sum(p_values < alpha))
    rate = rejections / replications

    # Wilson interval — behaves properly for rates near 0, unlike the normal
    # approximation, which is exactly where a false-positive rate lives.
    low, high = _wilson_interval(rejections, replications)

    is_null = config.true_effect == 0.0
    expected = alpha if is_null else None
    within = (low <= alpha <= high) if is_null else None

    if is_null:
        label = "False positive rate"
        explanation = (
            f"The true effect was set to zero, so every significant result here is a "
            f"false positive. Across {replications:,} simulated experiments the "
            f"{test_label} called {rejections:,} of them significant — a false positive "
            f"rate of {rate:.1%}. The target is alpha = {alpha:.0%}, and the simulation's "
            f"own margin of error puts the true rate between {low:.1%} and {high:.1%}. "
            + (
                "That contains alpha, so the test is controlling false positives correctly."
                if within
                else "That does NOT contain alpha, which would indicate a problem with the test."
            )
        )
    else:
        label = "Statistical power"
        misses = replications - rejections
        if misses == 0:
            tail = (
                "It never missed once, so at this sample size an effect this large is "
                "essentially impossible to overlook."
            )
        else:
            tail = (
                f"The other {misses:,} times ({1 - rate:.1%}) a real effect was missed, "
                "purely because of sample noise — a false negative, not evidence of "
                "no effect."
            )
        explanation = (
            f"The true effect was set to {config.true_effect:g}, so a correct test should "
            f"detect it. Across {replications:,} simulated experiments the {test_label} "
            f"found it {rejections:,} times — an empirical power of {rate:.1%} "
            f"(margin of error {low:.1%} to {high:.1%}). " + tail
        )

    return RejectionRateResult(
        replications=replications,
        alpha=alpha,
        rejection_rate=rate,
        rejection_interval=Interval(lower=low, upper=high, level=0.95),
        is_null=is_null,
        true_absolute_effect=config.true_effect,
        expected_rate=expected,
        within_expectation=within,
        label=label,
        explanation=explanation,
    )


def _wilson_interval(successes: int, trials: int, z: float = 1.959963985) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if trials == 0:
        return 0.0, 1.0
    phat = successes / trials
    denom = 1 + z**2 / trials
    centre = (phat + z**2 / (2 * trials)) / denom
    margin = z * np.sqrt(phat * (1 - phat) / trials + z**2 / (4 * trials**2)) / denom
    return float(max(0.0, centre - margin)), float(min(1.0, centre + margin))
