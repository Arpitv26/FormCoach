import type { SavedSet } from "./store";

export function median(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b), mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}
export function activity(sets: SavedSet[]) {
  const known = sets.filter(set => set.analysis.summary.totalReps !== null);
  return {
    sets: sets.length, days: new Set(sets.map(set => set.performedDate)).size,
    reps: known.length ? known.reduce((sum, set) => sum + set.analysis.summary.totalReps!, 0) : null,
    unknown: sets.length - known.length,
    partial: sets.filter(set => set.analysis.status === "partial").length,
  };
}
export function timing(set: SavedSet) {
  const values = set.analysis.reps.map(rep => rep.measurements.durationMs).filter((value): value is number => typeof value === "number" && Number.isFinite(value) && value > 0);
  return { median: median(values), spread: values.length > 1 ? Math.max(...values) - Math.min(...values) : null };
}
/** A wire-contract version is not an analyzer version; unknown revisions cannot establish a trend. */
export function comparable(a: SavedSet, b: SavedSet) {
  return !!a.analysisRevision && a.analysisRevision === b.analysisRevision
    && a.analysis.contractVersion === b.analysis.contractVersion
    && a.analysis.exercise?.id === b.analysis.exercise?.id
    && a.analysis.source.type === b.analysis.source.type;
}
export function movement(set: SavedSet) {
  const keys = ["smoothedLeftElbowExcursionDeg", "smoothedRightElbowExcursionDeg", "smoothedLeftShoulderExcursionDeg", "smoothedRightShoulderExcursionDeg"] as const;
  return keys.flatMap(key => {
    const values = set.analysis.reps.map(rep => rep.measurements[key]).filter((n): n is number => typeof n === "number" && Number.isFinite(n));
    const value = median(values);
    return value === null ? [] : [{ key, label: `${key.includes("Left") ? "Left" : "Right"} ${key.includes("Elbow") ? "elbow" : "shoulder"} range`, value }];
  });
}
