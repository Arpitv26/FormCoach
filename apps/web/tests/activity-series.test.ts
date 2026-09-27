import assert from "node:assert/strict";
import test from "node:test";
import { activitySeries } from "../src/lib/log/activity-series";
import type { SavedSet } from "../src/lib/log/store";
import type { AnalysisResponse } from "../src/lib/api/types";
import fixture from "../../../contracts/examples/visual-review-analysis.json";
const set = (date: string, reps: number | null): SavedSet => ({ id: date, performedDate: date, analysisAt: `${date}T12:00:00Z`, notes: "", analysisRevision: null, analysis: { ...fixture, summary: { ...fixture.summary, totalReps: reps } } as AnalysisResponse });
test("activity uses calendar days across month and daylight-saving boundaries", () => {
  const series = activitySeries([], "2026-03-10", 14);
  assert.equal(series.length, 14);
  assert.equal(series[0].date, "2026-02-25");
  assert.equal(series.at(-1)?.date, "2026-03-10");
  assert.equal(new Set(series.map(day => day.date)).size, 14);
});
test("activity separates an empty day, a known zero count, and unknown counts", () => {
  const series = activitySeries([set("2026-09-26", 0), set("2026-09-27", null), set("2026-09-27", 6)], "2026-09-27", 3);
  assert.deepEqual(series.map(({ sets, reps, unknown }) => ({ sets, reps, unknown })), [{ sets: 0, reps: null, unknown: 0 }, { sets: 1, reps: 0, unknown: 0 }, { sets: 2, reps: 6, unknown: 1 }]);
});
test("activity periods exclude future and out-of-range performed dates", () => {
  const entries = [set("2026-09-01", 4), set("2026-09-21", 6), set("2026-09-28", 8)];
  assert.equal(activitySeries(entries, "2026-09-27", 7).reduce((sum, day) => sum + day.sets, 0), 1);
  assert.equal(activitySeries(entries, "2026-09-27", 28).reduce((sum, day) => sum + day.sets, 0), 2);
});
