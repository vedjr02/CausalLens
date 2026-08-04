"use client";

/**
 * The confidence interval, drawn.
 *
 * A point estimate alone hides how much you actually know; this shows the
 * whole range the data supports, where "no effect" sits relative to it, and
 * — when the data is synthetic — where the true effect really was.
 *
 * Whether the bar clears the zero line IS the significance test, made visual.
 */
export function IntervalBar({
  lower,
  upper,
  estimate,
  trueValue,
  format,
  level,
}: {
  lower: number;
  upper: number;
  estimate: number;
  trueValue?: number | null;
  format: (value: number) => string;
  level: number;
}) {
  const candidates = [lower, upper, estimate, 0, ...(trueValue != null ? [trueValue] : [])];
  const rawMin = Math.min(...candidates);
  const rawMax = Math.max(...candidates);
  const padding = (rawMax - rawMin) * 0.18 || Math.abs(rawMax || 1) * 0.5;
  const domainMin = rawMin - padding;
  const domainMax = rawMax + padding;
  const span = domainMax - domainMin || 1;

  const toPct = (value: number) => ((value - domainMin) / span) * 100;

  const zeroPct = toPct(0);
  const lowerPct = toPct(lower);
  const upperPct = toPct(upper);
  const estimatePct = toPct(estimate);
  const truePct = trueValue != null ? toPct(trueValue) : null;

  const excludesZero = lower > 0 || upper < 0;

  return (
    <figure className="mt-1">
      <div className="relative h-24">
        {/* Baseline axis */}
        <div className="absolute inset-x-0 top-11 h-px bg-rule" />

        {/* "No effect" reference line — the thing the interval is judged against */}
        <div
          className="absolute top-5 h-14 w-px bg-ink-faint"
          style={{ left: `${zeroPct}%` }}
        />
        <span
          className="absolute top-[76px] -translate-x-1/2 whitespace-nowrap text-[11px] text-ink-faint"
          style={{ left: `${zeroPct}%` }}
        >
          no effect
        </span>

        {/* The interval itself */}
        <div
          className={`absolute top-[38px] h-[7px] rounded-full ${
            excludesZero ? "bg-accent/50" : "bg-ink-faint/55"
          }`}
          style={{ left: `${lowerPct}%`, width: `${Math.max(upperPct - lowerPct, 0.4)}%` }}
        />
        {/* Interval end caps */}
        {[lowerPct, upperPct].map((position, index) => (
          <div
            key={index}
            className={`absolute top-[33px] h-[17px] w-px ${
              excludesZero ? "bg-accent" : "bg-ink-faint"
            }`}
            style={{ left: `${position}%` }}
          />
        ))}

        {/* Point estimate */}
        <div
          className={`absolute top-[36px] h-[11px] w-[11px] -translate-x-1/2 rounded-full border-2 border-surface ${
            excludesZero ? "bg-accent" : "bg-ink-muted"
          }`}
          style={{ left: `${estimatePct}%` }}
        />

        {/* True effect — only present for synthetic data, where we know it */}
        {truePct != null && (
          <>
            <div
              className="absolute top-[22px] h-[34px] w-[2px] -translate-x-1/2 bg-caution"
              style={{ left: `${truePct}%` }}
            />
            <span
              className="absolute top-1 -translate-x-1/2 whitespace-nowrap text-[11px] font-medium text-caution"
              style={{ left: `${truePct}%` }}
            >
              true effect
            </span>
          </>
        )}
      </div>

      <div className="tnum mt-1 flex justify-between text-[12px] text-ink-faint">
        <span>{format(lower)}</span>
        <span className="text-ink-muted">
          estimate {format(estimate)}
        </span>
        <span>{format(upper)}</span>
      </div>

      <figcaption className="mt-3 text-[13px] leading-relaxed text-ink-muted">
        The bar is the {Math.round(level * 100)}% confidence interval — the range of
        effects this data is consistent with.{" "}
        {excludesZero
          ? "It sits entirely to one side of “no effect”, which is what makes the result significant."
          : "It crosses “no effect”, so a difference of zero remains a plausible explanation."}
        {truePct != null &&
          " The amber line marks the effect actually built into the simulation."}
      </figcaption>
    </figure>
  );
}
