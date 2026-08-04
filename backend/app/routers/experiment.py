"""Endpoints for running a synthetic experiment end to end."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.stats.classical import two_proportion_z_test, welch_t_test
from app.stats.models import Alternative, MetricType, TestResult
from app.stats.summarise import Distribution, shared_histogram
from app.stats.synthetic import GroundTruth, SyntheticConfig, generate_arrays
from app.stats.validation import RejectionRateResult, simulate_rejection_rate

router = APIRouter(prefix="/api/experiment", tags=["experiment"])


class SyntheticRunRequest(BaseModel):
    config: SyntheticConfig
    alpha: float = Field(0.05, gt=0.0, lt=1.0)
    alternative: Alternative = "two-sided"
    run_validation: bool = Field(
        True,
        description="Also re-run the experiment many times to measure the "
        "method's false positive rate or power against the known truth",
    )
    replications: int = Field(2000, ge=100, le=20_000)


class GroundTruthComparison(BaseModel):
    """Did the test land on the answer we already knew?

    This is the payoff of the synthetic generator: the true effect is not a
    guess, so we can state plainly whether the method got it right.
    """

    true_absolute_effect: float
    estimated_absolute_effect: float
    interval_covers_truth: bool
    conclusion_is_correct: bool
    verdict: str


class SyntheticRunResponse(BaseModel):
    ground_truth: GroundTruth
    test: TestResult
    comparison: GroundTruthComparison
    distributions: list[Distribution] | None = None
    validation: RejectionRateResult | None = None


def _compare_to_truth(truth: GroundTruth, test: TestResult) -> GroundTruthComparison:
    interval = test.effect.absolute_interval
    covers = interval.lower <= truth.true_absolute_effect <= interval.upper

    # "Correct" means the significance call matches reality: detect a real
    # effect, and stay quiet when there isn't one.
    effect_exists = truth.true_absolute_effect != 0.0
    correct = test.significant == effect_exists

    if effect_exists and test.significant:
        verdict = (
            "Correct call. A real effect existed and the test found it. "
            f"The true effect was {truth.true_absolute_effect:g}; the test estimated "
            f"{test.effect.absolute:g}."
        )
    elif effect_exists and not test.significant:
        verdict = (
            "Missed it — a false negative. A real effect of "
            f"{truth.true_absolute_effect:g} existed, but this sample wasn't strong "
            "enough to detect it. That is what low statistical power looks like, and "
            "it is why 'not significant' never means 'no effect'."
        )
    elif not effect_exists and test.significant:
        verdict = (
            "False positive. There was genuinely no effect, yet the test called this "
            "significant. This happens to roughly alpha of all experiments by chance "
            "alone — it is the cost of the threshold, not a bug."
        )
    else:
        verdict = (
            "Correct call. There was genuinely no effect, and the test correctly "
            "declined to claim one."
        )

    if not covers:
        verdict += (
            " Note that the confidence interval did not cover the true effect — "
            "expected in about 5% of experiments at 95% confidence."
        )

    return GroundTruthComparison(
        true_absolute_effect=truth.true_absolute_effect,
        estimated_absolute_effect=test.effect.absolute,
        interval_covers_truth=covers,
        conclusion_is_correct=correct,
        verdict=verdict,
    )


@router.post("/synthetic", response_model=SyntheticRunResponse)
async def run_synthetic_experiment(request: SyntheticRunRequest) -> SyntheticRunResponse:
    """Generate an experiment with a known true effect, analyse it, and report
    whether the method recovered the answer we already knew."""
    config = request.config

    try:
        control, treatment = generate_arrays(config)

        if config.metric_type is MetricType.BINARY:
            test = two_proportion_z_test(
                control_conversions=int(control.sum()),
                control_n=int(control.size),
                treatment_conversions=int(treatment.sum()),
                treatment_n=int(treatment.size),
                alpha=request.alpha,
                alternative=request.alternative,
            )
            distributions = None
        else:
            test = welch_t_test(
                control, treatment, alpha=request.alpha, alternative=request.alternative
            )
            distributions = list(shared_histogram(control, treatment))

        base = config.control_parameter
        truth = GroundTruth(
            metric_type=config.metric_type,
            control_parameter=base,
            treatment_parameter=config.treatment_parameter,
            true_absolute_effect=config.true_effect,
            true_relative_effect_pct=(config.true_effect / base * 100.0) if base else None,
            is_null=config.true_effect == 0.0,
            n_per_group=config.n_per_group,
            seed=config.seed,
        )

        validation = (
            simulate_rejection_rate(
                config,
                alpha=request.alpha,
                replications=request.replications,
                alternative=request.alternative,
            )
            if request.run_validation
            else None
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return SyntheticRunResponse(
        ground_truth=truth,
        test=test,
        comparison=_compare_to_truth(truth, test),
        distributions=distributions,
        validation=validation,
    )


class ValidationRequest(BaseModel):
    config: SyntheticConfig
    alpha: float = Field(0.05, gt=0.0, lt=1.0)
    replications: int = Field(2000, ge=100, le=20_000)
    alternative: Alternative = "two-sided"


@router.post("/validate", response_model=RejectionRateResult)
async def validate_method(request: ValidationRequest) -> RejectionRateResult:
    """Re-run the same experiment many times against known ground truth and
    report how often the method was right."""
    try:
        return simulate_rejection_rate(
            request.config,
            alpha=request.alpha,
            replications=request.replications,
            alternative=request.alternative,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
