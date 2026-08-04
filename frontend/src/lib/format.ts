/** Number formatting. Statistics read wrong when precision is inconsistent. */

export function formatPercent(value: number, digits = 2): string {
  return `${(value * 100).toFixed(digits)}%`;
}

export function formatPercentagePoints(value: number, digits = 2): string {
  const points = value * 100;
  return `${points >= 0 ? "+" : ""}${points.toFixed(digits)} pp`;
}

export function formatSigned(value: number, digits = 2): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(digits)}`;
}

export function formatNumber(value: number, digits = 2): string {
  return value.toFixed(digits);
}

export function formatCount(value: number): string {
  return value.toLocaleString("en-US");
}

/**
 * P-values are never rounded to "0.0000" — that reads as certainty the data
 * cannot support. Below the display threshold we say so explicitly.
 */
export function formatPValue(p: number): string {
  if (p < 0.0001) return "< 0.0001";
  if (p < 0.001) return p.toFixed(5);
  return p.toFixed(4);
}

export function formatInterval(
  lower: number,
  upper: number,
  format: (n: number) => string,
): string {
  return `${format(lower)} to ${format(upper)}`;
}
