/** TypeScript mirrors of the FastAPI statistical engine's response models. */

export type MetricType = "binary" | "continuous";
export type Alternative = "two-sided" | "greater" | "less";
export type TestName = "two_proportion_z" | "welch_t" | "mann_whitney_u";

export interface Interval {
  lower: number;
  upper: number;
  level: number;
}

export interface GroupSummary {
  name: string;
  n: number;
  conversions: number | null;
  rate: number | null;
  mean: number | null;
  std_dev: number | null;
}

export interface EffectSize {
  absolute: number;
  absolute_interval: Interval;
  relative_pct: number | null;
  relative_interval: Interval | null;
  standardised: number | null;
  standardised_name: string | null;
}

export interface TestResult {
  test: TestName;
  test_label: string;
  metric_type: MetricType;
  alternative: Alternative;
  alpha: number;
  control: GroupSummary;
  treatment: GroupSummary;
  statistic: number;
  p_value: number;
  degrees_of_freedom: number | null;
  significant: boolean;
  effect: EffectSize;
  assumptions: string[];
  interpretation: string;
}

export interface GroundTruth {
  metric_type: MetricType;
  control_parameter: number;
  treatment_parameter: number;
  true_absolute_effect: number;
  true_relative_effect_pct: number | null;
  is_null: boolean;
  n_per_group: number;
  seed: number | null;
}

export interface GroundTruthComparison {
  true_absolute_effect: number;
  estimated_absolute_effect: number;
  interval_covers_truth: boolean;
  conclusion_is_correct: boolean;
  verdict: string;
}

export interface RejectionRateResult {
  replications: number;
  alpha: number;
  rejection_rate: number;
  rejection_interval: Interval;
  is_null: boolean;
  true_absolute_effect: number;
  expected_rate: number | null;
  within_expectation: boolean | null;
  label: string;
  explanation: string;
}

export interface HistogramBin {
  start: number;
  end: number;
  centre: number;
  count: number;
}

export interface Distribution {
  name: string;
  bins: HistogramBin[];
  mean: number;
  std_dev: number;
  n: number;
}

export interface SyntheticConfig {
  metric_type: MetricType;
  n_per_group: number;
  baseline_rate?: number | null;
  baseline_mean?: number | null;
  std_dev?: number | null;
  true_effect: number;
  seed?: number | null;
}

export interface SyntheticRunRequest {
  config: SyntheticConfig;
  alpha: number;
  alternative: Alternative;
  run_validation: boolean;
  replications: number;
}

export interface SyntheticRunResponse {
  ground_truth: GroundTruth;
  test: TestResult;
  comparison: GroundTruthComparison;
  distributions: Distribution[] | null;
  validation: RejectionRateResult | null;
}
