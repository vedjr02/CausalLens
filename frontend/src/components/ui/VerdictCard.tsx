"use client";

export type VerdictTone = "positive" | "caution" | "negative" | "neutral";

const TONE_STYLES: Record<VerdictTone, { border: string; bg: string; label: string }> = {
  positive: {
    border: "border-positive/25",
    bg: "bg-positive-soft",
    label: "text-positive",
  },
  caution: {
    border: "border-caution/25",
    bg: "bg-caution-soft",
    label: "text-caution",
  },
  negative: {
    border: "border-negative/25",
    bg: "bg-negative-soft",
    label: "text-negative",
  },
  neutral: {
    border: "border-rule-strong",
    bg: "bg-surface",
    label: "text-ink-muted",
  },
};

/**
 * The single most important element on any results page.
 *
 * It comes before every chart and every p-value, and it says what to do in
 * words a non-technical stakeholder can act on. Statistics are the evidence
 * underneath, not the answer itself.
 */
export function VerdictCard({
  eyebrow,
  headline,
  body,
  tone,
  footnote,
}: {
  eyebrow: string;
  headline: string;
  body: string;
  tone: VerdictTone;
  footnote?: string;
}) {
  const styles = TONE_STYLES[tone];

  return (
    <section
      aria-label="Verdict"
      className={`rounded-lg border ${styles.border} ${styles.bg} px-7 py-6`}
    >
      <p className={`text-[11px] font-medium uppercase tracking-[0.14em] ${styles.label}`}>
        {eyebrow}
      </p>
      <h2 className="mt-3 text-[26px] font-medium leading-[1.25] tracking-tight text-ink">
        {headline}
      </h2>
      <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-ink-muted">
        {body}
      </p>
      {footnote && (
        <p className="mt-4 border-t border-ink/[0.07] pt-3 text-[13px] leading-relaxed text-ink-faint">
          {footnote}
        </p>
      )}
    </section>
  );
}
