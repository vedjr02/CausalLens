"""Shared schemas for the statistical engine.

These are plain data carriers. Nothing here imports FastAPI — the statistical
functions stay pure and independently testable.
"""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class MetricType(StrEnum):
    """Binary metrics are conversions; continuous metrics are things like
    revenue per user or session length."""

    BINARY = "binary"
    CONTINUOUS = "continuous"


class TestName(StrEnum):
    TWO_PROPORTION_Z = "two_proportion_z"
    WELCH_T = "welch_t"
    MANN_WHITNEY_U = "mann_whitney_u"


Alternative = Literal["two-sided", "greater", "less"]


class Interval(BaseModel):
    """A confidence or credible interval. Always reported alongside a point
    estimate — a point estimate on its own hides how much we actually know."""

    lower: float
    upper: float
    level: float = Field(0.95, description="e.g. 0.95 for a 95% interval")


class GroupSummary(BaseModel):
    """Observed summary of one arm of the experiment."""

    name: str
    n: int
    # Binary metrics
    conversions: int | None = None
    rate: float | None = None
    # Continuous metrics
    mean: float | None = None
    std_dev: float | None = None


class EffectSize(BaseModel):
    """The size of the difference, in every form a stakeholder might need.

    A p-value answers "is it real"; these answer "is it worth anything".
    """

    absolute: float = Field(description="Treatment minus control, in metric units")
    absolute_interval: Interval
    relative_pct: float | None = Field(
        None, description="Lift as a percentage of the control baseline"
    )
    relative_interval: Interval | None = None
    standardised: float | None = Field(
        None, description="Cohen's d (continuous) or Cohen's h (binary)"
    )
    standardised_name: str | None = None


class TestResult(BaseModel):
    """Output of a single hypothesis test.

    Deliberately never returns a p-value on its own: effect size, interval,
    and assumptions travel with it.
    """

    test: TestName
    test_label: str
    metric_type: MetricType
    alternative: Alternative
    alpha: float

    control: GroupSummary
    treatment: GroupSummary

    statistic: float
    p_value: float
    degrees_of_freedom: float | None = None
    significant: bool

    effect: EffectSize
    assumptions: list[str]
    interpretation: str
