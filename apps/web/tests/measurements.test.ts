import assert from "node:assert/strict";
import test from "node:test";
import fixture from "../../../contracts/examples/pushup-comparison-analysis.json";
import type { AnalysisResponse } from "../src/lib/api/types";
import { formatMetric, repMetric, referenceComparisons } from "../src/lib/results/measurements";
const analysis = fixture as AnalysisResponse;
test("comparison rendering uses supplied references and deltas without assigning a score", () => {
  const items = referenceComparisons(analysis.reps[2]);
  assert.deepEqual(items[0], { label: "Counted time", current: "3.20 s", reference: "reps 1–2", baseline: "1.70 s", change: "+1.50 s" });
  assert.equal(items[1].change, "-41.00°");
  assert.deepEqual(referenceComparisons(analysis.reps[0]), []);
});
test("charts preserve zero and unknown values; either measured anatomical side can render", () => {
  const rep = { ...analysis.reps[0], measurements: { durationMs: 0, smoothedRightElbowExcursionDeg: 80 } };
  assert.equal(repMetric(rep, "duration"), 0);
  assert.equal(repMetric(rep, "range"), 80);
  assert.equal(repMetric({ ...rep, measurements: {} }, "range"), null);
  assert.equal(formatMetric(null, "duration"), "Unavailable");
  assert.equal(formatMetric(0, "duration"), "0.00 s");
});
