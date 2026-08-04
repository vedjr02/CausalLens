import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paper: "var(--paper)",
        surface: "var(--surface)",
        ink: {
          DEFAULT: "var(--ink)",
          muted: "var(--ink-muted)",
          faint: "var(--ink-faint)",
        },
        rule: {
          DEFAULT: "var(--rule)",
          strong: "var(--rule-strong)",
        },
        accent: {
          DEFAULT: "var(--accent)",
          soft: "var(--accent-soft)",
        },
        positive: {
          DEFAULT: "var(--signal-positive)",
          soft: "var(--signal-positive-soft)",
        },
        caution: {
          DEFAULT: "var(--signal-caution)",
          soft: "var(--signal-caution-soft)",
        },
        negative: {
          DEFAULT: "var(--signal-negative)",
          soft: "var(--signal-negative-soft)",
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
