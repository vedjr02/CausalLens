"use client";

import { useCallback, useEffect, useState } from "react";
import {
  DEFAULT_GENERATOR_STATE,
  GeneratorPanel,
  type GeneratorState,
} from "@/components/experiment/GeneratorPanel";
import { ResultsReport } from "@/components/experiment/ResultsReport";
import { apiFetch, ApiError } from "@/lib/api";
import type { SyntheticRunRequest, SyntheticRunResponse } from "@/lib/types";

function toRequest(state: GeneratorState): SyntheticRunRequest {
  const isBinary = state.metricType === "binary";

  return {
    config: {
      metric_type: state.metricType,
      n_per_group: state.nPerGroup,
      // Percentages and percentage points are how people think about
      // conversion rates; the engine works in raw proportions.
      baseline_rate: isBinary ? state.baselineRatePct / 100 : null,
      baseline_mean: isBinary ? null : state.baselineMean,
      std_dev: isBinary ? null : state.stdDev,
      true_effect: isBinary ? state.trueEffectPp / 100 : state.trueEffectAbsolute,
      seed: state.seed,
    },
    alpha: state.alphaPct / 100,
    alternative: "two-sided",
    run_validation: true,
    replications: state.replications,
  };
}

export default function Home() {
  const [state, setState] = useState<GeneratorState>(DEFAULT_GENERATOR_STATE);
  const [result, setResult] = useState<SyntheticRunResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const run = useCallback(async (config: GeneratorState) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch<SyntheticRunResponse>(
        "/api/experiment/synthetic",
        { method: "POST", body: JSON.stringify(toRequest(config)) },
      );
      setResult(response);
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Something went wrong running the analysis.",
      );
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Land on a worked example rather than an empty page — the null-effect case
  // is the most instructive place to start.
  useEffect(() => {
    void run(DEFAULT_GENERATOR_STATE);
  }, [run]);

  return (
    <main className="mx-auto max-w-report px-8 py-16">
      <header className="border-b border-rule pb-8">
        <p className="text-xs uppercase tracking-[0.18em] text-ink-faint">
          CausalLens
        </p>
        <h1 className="mt-4 max-w-2xl text-[34px] font-medium leading-[1.15] tracking-tight">
          Is that difference real, or did you get lucky?
        </h1>
        <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-ink-muted">
          Set a true effect, simulate the experiment, and see whether the statistics
          recover it. Every term on this page has a plain-English definition &mdash;
          hover any underlined word.
        </p>
      </header>

      <div className="mt-10">
        <GeneratorPanel
          state={state}
          onChange={setState}
          onRun={() => void run(state)}
          loading={loading}
        />
      </div>

      {error && (
        <div
          role="alert"
          className="mt-8 rounded-lg border border-negative/25 bg-negative-soft px-6 py-5"
        >
          <p className="text-[13px] font-medium uppercase tracking-[0.12em] text-negative">
            Could not run the analysis
          </p>
          <p className="mt-2 text-[15px] leading-relaxed text-ink-muted">{error}</p>
        </div>
      )}

      {result && (
        <div className="mt-14">
          <ResultsReport result={result} />
        </div>
      )}

      <footer className="mt-20 border-t border-rule pt-6 text-[13px] text-ink-faint">
        Phase 1 &mdash; synthetic generator, two-proportion z-test, and Welch&rsquo;s
        t-test. Power analysis, sequential testing, Bayesian inference, and causal
        impact follow.
      </footer>
    </main>
  );
}
