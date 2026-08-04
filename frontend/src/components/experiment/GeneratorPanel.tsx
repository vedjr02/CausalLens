"use client";

import { NumberField, SegmentedField } from "@/components/ui/Field";
import { Term } from "@/components/ui/Term";
import type { MetricType } from "@/lib/types";

export interface GeneratorState {
  metricType: MetricType;
  nPerGroup: number;
  baselineRatePct: number;
  trueEffectPp: number;
  baselineMean: number;
  stdDev: number;
  trueEffectAbsolute: number;
  alphaPct: number;
  replications: number;
  seed: number;
}

export const DEFAULT_GENERATOR_STATE: GeneratorState = {
  metricType: "binary",
  nPerGroup: 5000,
  baselineRatePct: 10,
  trueEffectPp: 0,
  baselineMean: 100,
  stdDev: 25,
  trueEffectAbsolute: 0,
  alphaPct: 5,
  replications: 2000,
  seed: 42,
};

export function GeneratorPanel({
  state,
  onChange,
  onRun,
  loading,
}: {
  state: GeneratorState;
  onChange: (next: GeneratorState) => void;
  onRun: () => void;
  loading: boolean;
}) {
  const set = <K extends keyof GeneratorState>(key: K, value: GeneratorState[K]) =>
    onChange({ ...state, [key]: value });

  const isBinary = state.metricType === "binary";
  const isNull = isBinary ? state.trueEffectPp === 0 : state.trueEffectAbsolute === 0;

  return (
    <section className="rounded-lg border border-rule bg-surface px-7 py-6">
      <h2 className="text-[17px] font-medium tracking-tight">Set up the experiment</h2>
      <p className="mt-1.5 max-w-2xl text-[14px] leading-relaxed text-ink-muted">
        You choose the truth: the real effect is whatever you set it to. The data is
        then simulated around it, so you can watch whether the statistics recover the
        answer you already know.
      </p>

      <div className="mt-6 grid grid-cols-2 gap-x-8 gap-y-5">
        <div className="col-span-2">
          <SegmentedField<MetricType>
            label="Metric type"
            value={state.metricType}
            onChange={(value) => set("metricType", value)}
            options={[
              { value: "binary", label: "Conversion rate" },
              { value: "continuous", label: "Continuous value" },
            ]}
          />
        </div>

        {isBinary ? (
          <>
            <NumberField
              label="Baseline conversion rate"
              glossary="baselineRate"
              value={state.baselineRatePct}
              onChange={(value) => set("baselineRatePct", value)}
              min={0.1}
              max={99.9}
              step={0.5}
              suffix="%"
              hint="What control converts at today."
            />
            <NumberField
              label="True effect"
              glossary="trueEffect"
              value={state.trueEffectPp}
              onChange={(value) => set("trueEffectPp", value)}
              step={0.5}
              suffix="pp"
              hint="Set 0 to test for false positives."
            />
          </>
        ) : (
          <>
            <NumberField
              label="Baseline average"
              value={state.baselineMean}
              onChange={(value) => set("baselineMean", value)}
              step={1}
              hint="What control averages today."
            />
            <NumberField
              label="True effect"
              glossary="trueEffect"
              value={state.trueEffectAbsolute}
              onChange={(value) => set("trueEffectAbsolute", value)}
              step={0.5}
              hint="Set 0 to test for false positives."
            />
            <NumberField
              label="Noise (standard deviation)"
              glossary="standardDeviation"
              value={state.stdDev}
              onChange={(value) => set("stdDev", value)}
              min={0.001}
              step={1}
              hint="Higher means a noisier metric."
            />
          </>
        )}

        <NumberField
          label="Users per group"
          value={state.nPerGroup}
          onChange={(value) => set("nPerGroup", Math.round(value))}
          min={2}
          max={500000}
          step={500}
        />
        <NumberField
          label="Significance threshold"
          glossary="alpha"
          value={state.alphaPct}
          onChange={(value) => set("alphaPct", value)}
          min={0.1}
          max={50}
          step={1}
          suffix="%"
        />
        <NumberField
          label="Replications"
          glossary="replications"
          value={state.replications}
          onChange={(value) => set("replications", Math.round(value))}
          min={100}
          max={20000}
          step={500}
          hint="How many times to re-run the whole experiment."
        />
        <NumberField
          label="Random seed"
          glossary="seed"
          value={state.seed}
          onChange={(value) => set("seed", Math.round(value))}
          step={1}
          hint="Same seed, same data."
        />
      </div>

      <div className="mt-7 flex items-center gap-5 border-t border-rule pt-5">
        <button
          type="button"
          onClick={onRun}
          disabled={loading}
          className="rounded-md bg-ink px-5 py-2.5 text-[14px] font-medium text-paper transition-opacity hover:opacity-90 disabled:opacity-45"
        >
          {loading ? "Running…" : "Run the experiment"}
        </button>
        <p className="text-[13px] leading-relaxed text-ink-faint">
          {isNull ? (
            <>
              True effect is zero, so any significant result is a{" "}
              <Term name="falsePositiveRate">false positive</Term>.
            </>
          ) : (
            <>A real effect exists — the question is whether this sample finds it.</>
          )}
        </p>
      </div>
    </section>
  );
}
