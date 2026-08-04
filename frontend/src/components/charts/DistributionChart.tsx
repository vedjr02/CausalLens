"use client";

import {
  Area,
  ComposedChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Distribution } from "@/lib/types";

/**
 * Both groups' distributions, overlaid on shared bins.
 *
 * The point is to show how much the two distributions overlap. Two averages
 * can differ while nearly every individual value is interchangeable — that
 * overlap is what a p-value is quietly reasoning about.
 */
export function DistributionChart({
  distributions,
  unitLabel,
}: {
  distributions: Distribution[];
  unitLabel: string;
}) {
  const [control, treatment] = distributions;

  const data = control.bins.map((bin, index) => ({
    centre: bin.centre,
    control: bin.count,
    treatment: treatment.bins[index]?.count ?? 0,
  }));

  return (
    <figure>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 0 }}>
            <XAxis
              dataKey="centre"
              type="number"
              domain={["dataMin", "dataMax"]}
              tickFormatter={(value: number) => value.toFixed(0)}
              tick={{ fontSize: 11, fill: "var(--ink-faint)" }}
              axisLine={{ stroke: "var(--rule)" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "var(--ink-faint)" }}
              axisLine={false}
              tickLine={false}
              width={40}
            />
            <Tooltip
              cursor={{ stroke: "var(--rule-strong)" }}
              contentStyle={{
                border: "1px solid var(--rule-strong)",
                borderRadius: 6,
                fontSize: 12,
                background: "var(--surface)",
              }}
              labelFormatter={(value: number) => `${unitLabel} ≈ ${value.toFixed(1)}`}
              formatter={(value: number, name: string) => [
                `${value} users`,
                name === "control" ? "Control" : "Treatment",
              ]}
            />
            <Area
              type="monotone"
              dataKey="control"
              stroke="var(--ink-muted)"
              fill="var(--ink-muted)"
              fillOpacity={0.14}
              strokeWidth={1.5}
              isAnimationActive={false}
            />
            <Area
              type="monotone"
              dataKey="treatment"
              stroke="var(--accent)"
              fill="var(--accent)"
              fillOpacity={0.14}
              strokeWidth={1.5}
              isAnimationActive={false}
            />
            <ReferenceLine
              x={control.mean}
              stroke="var(--ink-muted)"
              strokeDasharray="3 3"
            />
            <ReferenceLine
              x={treatment.mean}
              stroke="var(--accent)"
              strokeDasharray="3 3"
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 flex gap-5 text-[12px] text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-[2px] w-4 bg-ink-muted" /> Control
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-[2px] w-4 bg-accent" /> Treatment
        </span>
        <span className="text-ink-faint">Dashed lines mark each group&rsquo;s average.</span>
      </div>

      <figcaption className="mt-3 text-[13px] leading-relaxed text-ink-muted">
        How individual values are spread within each group. The averages differ, but
        notice how far the two shapes overlap &mdash; that overlap is the noise the
        test has to see through before it can call a difference real.
      </figcaption>
    </figure>
  );
}
