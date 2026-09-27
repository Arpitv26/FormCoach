import type { RepAnalysis } from "../api/types";
export type RepMetric = "duration" | "range";
export function repMetric(rep: RepAnalysis, metric: RepMetric): number | null {
  const value = metric === "duration" ? rep.measurements.durationMs :
    rep.measurements.smoothedLeftElbowExcursionDeg ?? rep.measurements.smoothedRightElbowExcursionDeg;
  return typeof value === "number" && Number.isFinite(value) && value >= 0 ? value : null;
}
export function formatMetric(value: number | null, metric: RepMetric) {
  return value === null ? "Unavailable" : metric === "duration" ? `${(value / 1000).toFixed(2)} s` : `${value.toFixed(1)}°`;
}
export function referenceComparisons(rep: RepAnalysis) {
  const m = rep.measurements;
  const start = m.comparisonReferenceStartRep, end = m.comparisonReferenceEndRep;
  if (start == null || end == null) return [];
  const reference = `reps ${start}–${end}`;
  const items: { label: string; current: string; reference: string; baseline: string; change: string }[] = [];
  const duration = repMetric(rep, "duration"), range = repMetric(rep, "range");
  const delta = (value: number) => `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
  if (duration !== null && m.referenceMedianDurationMs != null && m.durationDeltaMs != null)
    items.push({ label: "Counted time", current: formatMetric(duration, "duration"), reference, baseline: formatMetric(m.referenceMedianDurationMs, "duration"), change: `${delta(m.durationDeltaMs / 1000)} s` });
  if (range !== null && m.referenceMedianElbowExcursionDeg != null && m.elbowExcursionDeltaDeg != null)
    items.push({ label: "Observed elbow range", current: formatMetric(range, "range"), reference, baseline: formatMetric(m.referenceMedianElbowExcursionDeg, "range"), change: `${delta(m.elbowExcursionDeltaDeg)}°` });
  return items;
}
