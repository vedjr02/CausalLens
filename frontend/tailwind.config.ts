import type { Config } from "tailwindcss";

/**
 * Colours come from CSS variables holding space-separated RGB channels, so
 * that opacity modifiers (`bg-accent/50`, `border-positive/25`) actually
 * work. Pointing these at hex variables instead makes every such class
 * render transparent, with no build error to warn you.
 */
const withAlpha = (variable: string) => `rgb(var(${variable}) / <alpha-value>)`;

const config: Config = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: withAlpha("--paper-rgb"),
        surface: withAlpha("--surface-rgb"),
        ink: {
          DEFAULT: withAlpha("--ink-rgb"),
          muted: withAlpha("--ink-muted-rgb"),
          faint: withAlpha("--ink-faint-rgb"),
        },
        rule: {
          DEFAULT: withAlpha("--rule-rgb"),
          strong: withAlpha("--rule-strong-rgb"),
        },
        accent: {
          DEFAULT: withAlpha("--accent-rgb"),
          soft: withAlpha("--accent-soft-rgb"),
        },
        positive: {
          DEFAULT: withAlpha("--signal-positive-rgb"),
          soft: withAlpha("--signal-positive-soft-rgb"),
        },
        caution: {
          DEFAULT: withAlpha("--signal-caution-rgb"),
          soft: withAlpha("--signal-caution-soft-rgb"),
        },
        negative: {
          DEFAULT: withAlpha("--signal-negative-rgb"),
          soft: withAlpha("--signal-negative-soft-rgb"),
        },
      },
      fontFamily: {
        sans: ["var(--font-geist-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-geist-mono)", "ui-monospace", "monospace"],
      },
      maxWidth: {
        // A report column, not a dashboard grid.
        report: "56rem",
      },
    },
  },
  plugins: [],
};
export default config;
