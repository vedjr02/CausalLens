"use client";

import { IntervalBar } from "@/components/charts/IntervalBar";
import { DistributionChart } from "@/components/charts/DistributionChart";
import { Term } from "@/components/ui/Term";
import { VerdictCard, type VerdictTone } from "@/components/ui/VerdictCard";
import {
  formatCount,
  formatNumber,
  formatPValue,
  formatPercent,
  formatPercentagePoints,
  formatSigned,
} from "@/lib/format";
import type { SyntheticRunResponse } from "@/lib/types";

/**
 * Phase 1's headline verdict.
 *
 * Deliberately simple: the full verdict generator (which also weighs power
 * and sample adequacy) arrives with the verdict layer in a later phase. This
 * keeps the rule that plain English comes before any statistic.
 */
function deriveVerdict(result: SyntheticRunResponse): {
  eyebrow: string;
  headline: string;
  tone: VerdictTone;
} {
  const { significant, effect } = result.test;

  if (!significant) {
    return {
      eyebrow: "Verdict",
      headline: "Not enough evidence to call a winner",
      tone: "caution",
    };
  }
  return effect.absolute > 0
    ? {
        eyebrow: "Verdict",
        headline: "Treatment is genuinely ahead",
        tone: "positive",
      }
    : {
        eyebrow: "Verdict",
        headline: "Treatment is genuinely behind",
        tone: "negative",
      };
}

export function ResultsReport({ result }: { result: SyntheticRunResponse }) {
  const { test, comparison, ground_truth, validation, distributions } = result;
  const isBinary = test.metric_type === "binary";
  const verdict = deriveVerdict(result);

  const formatEffect = (value: number) =>
    isBinary ? formatPercentagePoints(value) : formatSigned(value, 2);

  return (
    <div className="space-y-12">
      <VerdictCard
        eyebrow={verdict.eyebrow}
        headline={verdict.headline}
        body={test.interpretation}
        tone={verdict.tone}
        footnote={`Based on a ${test.test_label.toLowerCase()} at a ${
          test.alpha * 100
        }% significance threshold, on ${formatCount(test.control.n)} users per group.`}
      />

      {/* The payoff of synthetic data: we know the answer, so we can grade the method. */}
      <Section
        title="Checked against the truth"
        caption="Because this data was simulated, the real effect is known. That makes it possible to say plainly whether the statistics got it right — something no real dataset can tell you."
      >
        <div className="grid grid-cols-3 gap-6 border-y border-rule py-5">
          <Stat
            label="True effect"
            glossary="trueEffect"
            value={formatEffect(ground_truth.true_absolute_effect)}
          />
          <Stat
            label="Estimated effect"
            value={formatEffect(comparison.estimated_absolute_effect)}
          />
          <Stat
            label="Interval covers truth"
            value={comparison.interval_covers_truth ? "Yes" : "No"}
            tone={comparison.interval_covers_truth ? "positive" : "caution"}
          />
        </div>
        <p className="mt-5 text-[15px] leading-relaxed text-ink-muted">
          {comparison.verdict}
        </p>
      </Section>

      <Section
        title="What the experiment measured"
        caption="The raw numbers behind the verdict."
      >
        <table className="w-full border-collapse text-[15px]">
          <thead>
            <tr className="border-b border-rule text-left text-[12px] uppercase tracking-[0.1em] text-ink-faint">
              <th className="py-2 font-medium">Group</th>
              <th className="py-2 text-right font-medium">Users</th>
              <th className="py-2 text-right font-medium">
                {isBinary ? "Conversions" : "Average"}
              </th>
              <th className="py-2 text-right font-medium">
                {isBinary ? "Rate" : <Term name="standardDeviation">Std. dev.</Term>}
              </th>
            </tr>
          </thead>
          <tbody className="tnum">
            {[test.control, test.treatment].map((group) => (
              <tr key={group.name} className="border-b border-rule">
                <td className="py-2.5">{group.name}</td>
                <td className="py-2.5 text-right">{formatCount(group.n)}</td>
                <td className="py-2.5 text-right">
                  {isBinary
                    ? formatCount(group.conversions ?? 0)
                    : formatNumber(group.mean ?? 0)}
                </td>
                <td className="py-2.5 text-right">
                  {isBinary
                    ? formatPercent(group.rate ?? 0)
                    : formatNumber(group.std_dev ?? 0)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section
        title="How big is the difference, and how sure are we?"
        caption="A p-value says whether an effect is real. It says nothing about whether the effect is big enough to matter — that is what these numbers are for."
      >
        <div className="grid grid-cols-4 gap-6 border-b border-rule pb-5">
          <Stat
            label="p-value"
            glossary="pValue"
            value={formatPValue(test.p_value)}
            tone={test.significant ? "positive" : "neutral"}
          />
          <Stat
            label={isBinary ? "Absolute difference" : "Difference in averages"}
            glossary="absoluteEffect"
            value={formatEffect(test.effect.absolute)}
          />
          <Stat
            label="Relative lift"
            glossary="relativeLift"
            value={
              test.effect.relative_pct != null
                ? `${formatSigned(test.effect.relative_pct, 1)}%`
                : "—"
            }
          />
          <Stat
            label={test.effect.standardised_name ?? "Effect size"}
            glossary={isBinary ? "cohensH" : "hedgesG"}
            value={
              test.effect.standardised != null
                ? formatNumber(test.effect.standardised, 3)
                : "—"
            }
          />
        </div>

        <div className="mt-7">
          <IntervalBar
            lower={test.effect.absolute_interval.lower}
            upper={test.effect.absolute_interval.upper}
            estimate={test.effect.absolute}
            trueValue={ground_truth.true_absolute_effect}
            level={test.effect.absolute_interval.level}
            format={formatEffect}
          />
        </div>

        {test.effect.relative_interval && (
          <p className="tnum mt-6 text-[14px] text-ink-muted">
            In relative terms, the data is consistent with a lift between{" "}
            <span className="text-ink">
              {formatSigned(test.effect.relative_interval.lower, 1)}%
            </span>{" "}
            and{" "}
            <span className="text-ink">
              {formatSigned(test.effect.relative_interval.upper, 1)}%
            </span>
            .
          </p>
        )}
      </Section>

      {distributions && (
        <Section
          title="The distributions"
          caption="Averages hide the shape of the data."
        >
          <DistributionChart distributions={distributions} unitLabel="Metric value" />
        </Section>
      )}

      {validation && (
        <Section
          title="Does the method actually work?"
          caption="The same experiment, re-run many times on fresh simulated data, to check the method's behaviour rather than trust one lucky sample."
        >
          <div className="grid grid-cols-3 gap-6 border-y border-rule py-5">
            <Stat
              label={validation.label}
              glossary={validation.is_null ? "falsePositiveRate" : "power"}
              value={formatPercent(validation.rejection_rate, 1)}
              tone={
                validation.is_null
                  ? validation.within_expectation
                    ? "positive"
                    : "caution"
                  : "neutral"
              }
            />
            {validation.is_null && (
              <Stat
                label="Target (alpha)"
                glossary="alpha"
                value={formatPercent(validation.alpha, 1)}
              />
            )}
            <Stat
              label="Replications"
              glossary="replications"
              value={formatCount(validation.replications)}
            />
          </div>
          <p className="mt-5 text-[15px] leading-relaxed text-ink-muted">
            {validation.explanation}
          </p>
        </Section>
      )}

      <Section
        title="What this test assumes"
        caption="Every method leans on something. A result is only as trustworthy as the assumptions underneath it, so they are stated rather than hidden."
      >
        <ul className="space-y-2.5">
          {test.assumptions.map((assumption) => (
            <li
              key={assumption}
              className="flex gap-3 text-[15px] leading-relaxed text-ink-muted"
            >
              <span className="mt-[9px] h-1 w-1 shrink-0 rounded-full bg-ink-faint" />
              {assumption}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

function Section({
  title,
  caption,
  children,
}: {
  title: string;
  caption?: string;
  children: React.ReactNode;
}) {
  return (
    <section>
      <h3 className="text-[17px] font-medium tracking-tight text-ink">{title}</h3>
      {caption && (
        <p className="mt-1.5 max-w-2xl text-[14px] leading-relaxed text-ink-muted">
          {caption}
        </p>
      )}
      <div className="mt-5">{children}</div>
    </section>
  );
}

function Stat({
  label,
  value,
  glossary,
  tone = "neutral",
}: {
  label: string;
  value: string;
  glossary?: React.ComponentProps<typeof Term>["name"];
  tone?: "neutral" | "positive" | "caution";
}) {
  const toneClass =
    tone === "positive"
      ? "text-positive"
      : tone === "caution"
        ? "text-caution"
        : "text-ink";

  return (
    <div>
      <p className="text-[12px] uppercase tracking-[0.08em] text-ink-faint">
        {glossary ? <Term name={glossary}>{label}</Term> : label}
      </p>
      <p className={`tnum mt-1.5 text-[22px] font-medium tracking-tight ${toneClass}`}>
        {value}
      </p>
    </div>
  );
}
