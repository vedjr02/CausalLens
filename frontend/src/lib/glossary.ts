/**
 * Plain-English definitions for every statistical term the app shows.
 *
 * The whole point of this product is translating rigour into business
 * language, so no term reaches the screen without one of these. Definitions
 * are one line, avoid other jargon, and say what it means for a decision —
 * not what the textbook says.
 */

export interface GlossaryEntry {
  term: string;
  definition: string;
}

export const GLOSSARY = {
  pValue: {
    term: "p-value",
    definition:
      "If the change truly did nothing, how often would you see a difference at least this big by luck alone? Small means luck is a poor explanation.",
  },
  significance: {
    term: "statistically significant",
    definition:
      "The difference is larger than random noise comfortably explains. It says the effect is probably real — not that it is large or worth shipping.",
  },
  alpha: {
    term: "significance threshold (alpha)",
    definition:
      "The false-alarm rate you agree to accept up front. At 5%, roughly 1 in 20 experiments with no real effect will still look significant.",
  },
  confidenceInterval: {
    term: "confidence interval",
    definition:
      "The range of effect sizes the data is consistent with. Repeat the experiment many times and about 95% of these ranges would contain the true effect.",
  },
  absoluteEffect: {
    term: "absolute difference",
    definition:
      "Treatment minus control, in the metric's own units. A move from 10% to 12% is an absolute difference of 2 percentage points.",
  },
  relativeLift: {
    term: "relative lift",
    definition:
      "The difference as a percentage of where you started. A move from 10% to 12% is a 20% relative lift — the number that usually ends up in the business case.",
  },
  effectSize: {
    term: "standardised effect size",
    definition:
      "The difference expressed in units of the data's own spread, so effects can be compared across metrics measured on different scales.",
  },
  cohensH: {
    term: "Cohen's h",
    definition:
      "A standardised effect size for the gap between two rates. Roughly: 0.2 is small, 0.5 medium, 0.8 large.",
  },
  hedgesG: {
    term: "Hedges' g",
    definition:
      "A standardised difference between two averages, corrected for the bias that shows up in small samples. Roughly: 0.2 small, 0.5 medium, 0.8 large.",
  },
  power: {
    term: "statistical power",
    definition:
      "The chance your experiment detects a real effect of a given size. Low power means a real effect can easily be missed, so a null result proves nothing.",
  },
  falsePositiveRate: {
    term: "false positive rate",
    definition:
      "How often a test declares a winner when nothing actually changed. A trustworthy test keeps this at the threshold you set, not above it.",
  },
  falseNegative: {
    term: "false negative",
    definition:
      "A real effect the test failed to detect, almost always because the sample was too small to see something that size.",
  },
  nullHypothesis: {
    term: "null hypothesis",
    definition:
      "The starting assumption that the change did nothing. A test only ever measures how badly the data fits that assumption.",
  },
  welchTest: {
    term: "Welch's t-test",
    definition:
      "Compares two averages without assuming both groups vary by the same amount — the safe default, since a treatment often changes the spread as well as the average.",
  },
  zTest: {
    term: "two-proportion z-test",
    definition:
      "Compares two conversion rates to judge whether the gap between them is bigger than chance would produce.",
  },
  degreesOfFreedom: {
    term: "degrees of freedom",
    definition:
      "How much independent information the sample carries. More of it makes the test's conclusions more reliable.",
  },
  standardDeviation: {
    term: "standard deviation",
    definition:
      "How spread out the individual values are around their average. Higher spread means more noise to see through.",
  },
  baselineRate: {
    term: "baseline rate",
    definition:
      "The conversion rate you get today, before any change. Everything else is measured against it.",
  },
  trueEffect: {
    term: "true effect",
    definition:
      "The real difference built into this simulation. Because you set it, you can check whether the statistics actually recovered it.",
  },
  replications: {
    term: "replications",
    definition:
      "How many times the whole experiment is re-run on fresh simulated data, to see how the method behaves on average rather than on one lucky sample.",
  },
  seed: {
    term: "random seed",
    definition:
      "Fixes the random draws so the same settings always produce the same data. Useful when you want a result you can point at twice.",
  },
} as const satisfies Record<string, GlossaryEntry>;

export type GlossaryKey = keyof typeof GLOSSARY;
