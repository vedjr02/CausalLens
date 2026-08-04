"""Synthetic experiment data with known ground truth.

This is the backbone of the project. Because the true effect is set by the
user, every statistical method in the app can be checked against an answer we
already know — including the case that matters most, a true effect of exactly
zero, where any "significant" result is by construction a false positive.
"""

from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, model_validator

from app.stats.models import MetricType

MAX_N_PER_GROUP = 500_000


class SyntheticConfig(BaseModel):
    """Ground truth for a simulated experiment."""

    metric_type: MetricType
    n_per_group: int = Field(1000, ge=2, le=MAX_N_PER_GROUP)

    # Binary metrics
    baseline_rate: float | None = Field(
        None, ge=0.0, le=1.0, description="Control conversion rate, e.g. 0.10"
    )

    # Continuous metrics
    baseline_mean: float | None = Field(None, description="Control mean")
    std_dev: float | None = Field(
        None, gt=0.0, description="Within-group standard deviation (the noise)"
    )

    # The true effect. Zero is a first-class, deliberately supported value:
    # it is how you check a method's false-positive rate.
    true_effect: float = Field(
        0.0,
        description=(
            "Absolute effect for binary metrics (in rate units, e.g. 0.02 = "
            "+2 percentage points); absolute mean difference for continuous."
        ),
    )

    seed: int | None = Field(None, description="Set for reproducible draws")

    @model_validator(mode="after")
    def check_required_fields(self) -> "SyntheticConfig":
        if self.metric_type is MetricType.BINARY:
            if self.baseline_rate is None:
                raise ValueError("baseline_rate is required for a binary metric")
            treatment_rate = self.baseline_rate + self.true_effect
            if not 0.0 <= treatment_rate <= 1.0:
                raise ValueError(
                    f"baseline_rate + true_effect = {treatment_rate:.4f}, which is "
                    "not a valid probability. Reduce the true effect."
                )
        else:
            if self.baseline_mean is None:
                raise ValueError("baseline_mean is required for a continuous metric")
            if self.std_dev is None:
                raise ValueError("std_dev is required for a continuous metric")
        return self

    @property
    def treatment_parameter(self) -> float:
        """The true treatment-arm parameter implied by the config."""
        base = self.baseline_rate if self.metric_type is MetricType.BINARY else self.baseline_mean
        assert base is not None
        return base + self.true_effect

    @property
    def control_parameter(self) -> float:
        base = self.baseline_rate if self.metric_type is MetricType.BINARY else self.baseline_mean
        assert base is not None
        return base


class GroundTruth(BaseModel):
    """What we actually set — kept alongside the sample so the UI can show
    "the true effect was X, here is what each method concluded"."""

    metric_type: MetricType
    control_parameter: float
    treatment_parameter: float
    true_absolute_effect: float
    true_relative_effect_pct: float | None
    is_null: bool = Field(description="True when there is genuinely no effect")
    n_per_group: int
    seed: int | None


class SyntheticDataset(BaseModel):
    """A generated experiment: raw observations plus the truth behind them."""

    ground_truth: GroundTruth
    control: list[float]
    treatment: list[float]


def _rng(seed: int | None) -> np.random.Generator:
    return np.random.default_rng(seed)


def generate(config: SyntheticConfig) -> SyntheticDataset:
    """Draw one synthetic experiment from the configured ground truth."""
    rng = _rng(config.seed)
    n = config.n_per_group

    if config.metric_type is MetricType.BINARY:
        p_control = config.control_parameter
        p_treatment = config.treatment_parameter
        control = rng.binomial(1, p_control, size=n).astype(float)
        treatment = rng.binomial(1, p_treatment, size=n).astype(float)
    else:
        assert config.std_dev is not None
        control = rng.normal(config.control_parameter, config.std_dev, size=n)
        treatment = rng.normal(config.treatment_parameter, config.std_dev, size=n)

    base = config.control_parameter
    relative = (config.true_effect / base * 100.0) if base != 0 else None

    return SyntheticDataset(
        ground_truth=GroundTruth(
            metric_type=config.metric_type,
            control_parameter=config.control_parameter,
            treatment_parameter=config.treatment_parameter,
            true_absolute_effect=config.true_effect,
            true_relative_effect_pct=relative,
            is_null=config.true_effect == 0.0,
            n_per_group=n,
            seed=config.seed,
        ),
        control=control.tolist(),
        treatment=treatment.tolist(),
    )


def generate_arrays(
    config: SyntheticConfig, seed: int | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Fast path for simulation loops — returns arrays, skips model validation.

    ``seed`` overrides the config's seed so a loop can draw independent
    replications from the same ground truth.
    """
    rng = _rng(seed if seed is not None else config.seed)
    n = config.n_per_group

    if config.metric_type is MetricType.BINARY:
        return (
            rng.binomial(1, config.control_parameter, size=n).astype(float),
            rng.binomial(1, config.treatment_parameter, size=n).astype(float),
        )

    assert config.std_dev is not None
    return (
        rng.normal(config.control_parameter, config.std_dev, size=n),
        rng.normal(config.treatment_parameter, config.std_dev, size=n),
    )


MetricLiteral = Literal["binary", "continuous"]
