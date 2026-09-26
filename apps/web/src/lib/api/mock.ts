import fixture from "../../../../../contracts/examples/squat-analysis.json";
import type { AnalysisResponse } from "./types";

/** Synthetic UI fixture. Never substitute this for a failed real analysis request. */
export function getMockAnalysis(): AnalysisResponse {
  return structuredClone(fixture) as AnalysisResponse;
}
