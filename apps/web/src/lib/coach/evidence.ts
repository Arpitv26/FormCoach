import type { AnalysisResponse } from "../api/types";

/** Only follow own data properties; evidence is a path, never executable code or HTML. */
export function evidenceValue(analysis: AnalysisResponse, path: string): unknown {
  let current: unknown = analysis;
  for (const part of path.split(".")) {
    if (!/^(\d+|[a-zA-Z][a-zA-Z0-9]*)$/.test(part) || ["constructor", "prototype", "__proto__"].includes(part)) return undefined;
    if (current === null || typeof current !== "object" || !Object.prototype.hasOwnProperty.call(current, part)) return undefined;
    current = (current as Record<string, unknown>)[part];
  }
  return current;
}

export function describeEvidence(analysis: AnalysisResponse, path: string) {
  const match = /^reps\.(\d+)\./.exec(path);
  const rep = match ? analysis.reps[Number(match[1])] : undefined;
  const movement = /^movementObservations\.(\d+)\./.exec(path);
  const visual = /^visualReview\.findings\.(\d+)\./.exec(path);
  const visualTime = visual && /\.evidenceTimestampsMs\.\d+$/.test(path);
  const key = path.split(".").at(-1) ?? path;
  const label = key.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/Ms$/, " (seconds)").replace(/Deg$/, " (degrees)");
  const value = evidenceValue(analysis, path);
  let text = "Unavailable";
  if (typeof value === "number" && Number.isFinite(value)) text = key.endsWith("Ms") || visualTime ? `${(value / 1000).toFixed(2)} s` : key.endsWith("Deg") ? `${value.toFixed(1)}°` : `${value}`;
  else if (typeof value === "string" || typeof value === "boolean") text = String(value);
  return { label: `${rep ? `Rep ${rep.repNumber} · ` : movement ? `Movement moment ${Number(movement[1]) + 1} · ` : visual ? `Visual observation ${Number(visual[1]) + 1} · ` : ""}${visualTime ? "Video time" : label}`, text, rep, seekMs: visualTime && typeof value === "number" ? value : undefined };
}
