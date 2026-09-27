import assert from "node:assert/strict";
import test from "node:test";
import fixture from "../../../contracts/examples/pushup-comparison-analysis.json";
import observation from "../../../contracts/examples/pushup-movement-observation.json";
import type { AnalysisResponse } from "../src/lib/api/types";
import { deleteSet, EMPTY_LOG, LOG_KEY, readLog, saveSet, STORAGE_UNAVAILABLE, validDate, type SavedSet } from "../src/lib/log/store";
import { activity, comparable, movement, timing } from "../src/lib/log/trackers";

function record(id = "set-a", response: AnalysisResponse = fixture as AnalysisResponse): SavedSet {
  const analysis = structuredClone(response) as AnalysisResponse;
  analysis.provenance = { kind: "measured", label: "Test poses, not real camera evidence" };
  analysis.sessionId = id;
  analysis.source.type = "upload";
  return { id, analysisAt: "2026-09-27T10:00:00Z", performedDate: "2026-09-26", notes: "", analysisRevision: null, analysis };
}
function storage() {
  let raw: string | null = null;
  return { getItem: (key: string) => key === LOG_KEY ? raw : null, setItem: (_key: string, value: string) => { raw = value; } };
}
test("save survives serialization, updates metadata once, and retains exact analysis", () => {
  const db = storage(), input = record();
  saveSet(db, input); saveSet(db, { ...input, notes: "Paused at the top", performedDate: "2026-09-25" });
  const reopened = readLog(db.getItem(LOG_KEY));
  assert.equal(reopened.sets.length, 1);
  assert.deepEqual(reopened.sets[0].analysis, input.analysis);
  assert.equal(reopened.sets[0].performedDate, "2026-09-25");
  assert.equal(reopened.sets[0].notes, "Paused at the top");
});
test("reanalyzing updates an explicit chosen set and cannot silently add duplicate activity", () => {
  const db = storage(), first = record(); saveSet(db, first);
  const next = { ...record("new-analysis"), id: first.id };
  assert.throws(() => saveSet(db, next), /Update saved set/);
  saveSet(db, next, true);
  assert.equal(readLog(db.getItem(LOG_KEY)).sets.length, 1);
  assert.equal(readLog(db.getItem(LOG_KEY)).sets[0].analysis.sessionId, "new-analysis");
  assert.throws(() => saveSet(db, { ...next, id: "another" }), /already saved/);
  assert.throws(() => saveSet(db, record("deleted"), true), /no longer exists/);
  saveSet(db, record("explicit-new"));
  assert.equal(readLog(db.getItem(LOG_KEY)).sets.length, 2);
});
test("replacement cannot change exercise or source", () => {
  const db = storage(), first = record(); saveSet(db, first);
  const next = structuredClone(first); next.analysis.source.type = "live";
  assert.throws(() => saveSet(db, next, true), /doesn’t match/);
  next.analysis.source.type = "upload"; next.analysis.exercise!.id = "lat-pulldown";
  assert.throws(() => saveSet(db, next, true), /doesn’t match/);
});
test("zero and unknown counts retain independent movement observations", () => {
  const db = storage(), zero = record("zero", observation as AnalysisResponse);
  zero.analysis.status = "partial";
  saveSet(db, zero);
  const unknown = structuredClone(zero); unknown.id = "unknown"; unknown.analysis.sessionId = "unknown";
  unknown.analysis.status = "insufficient_data"; unknown.analysis.summary.totalReps = null;
  saveSet(db, unknown);
  const loaded = readLog(db.getItem(LOG_KEY));
  assert.equal(loaded.sets.length, 2);
  assert.deepEqual(loaded.sets[1].analysis.movementObservations, unknown.analysis.movementObservations);
  assert.deepEqual(activity(loaded.sets), { sets: 2, days: 1, reps: 0, unknown: 1, partial: 1 });
  assert.equal(activity([unknown]).reps, null);
});
test("save failure leaves the previous log unchanged and never claims success", () => {
  const db = storage(); saveSet(db, record()); const before = db.getItem(LOG_KEY);
  assert.throws(() => saveSet({ getItem: db.getItem, setItem: () => { throw new Error("QuotaExceededError"); } }, record("b")), /Set not saved/);
  assert.equal(db.getItem(LOG_KEY), before);
  assert.match(readLog(STORAGE_UNAVAILABLE).error!, /unavailable/);
});
test("invalid envelope remains untouched and incompatible records do not break valid history", () => {
  const db = storage(); db.setItem(LOG_KEY, "bad JSON");
  assert.equal(readLog(db.getItem(LOG_KEY)).sets.length, 0);
  assert.throws(() => saveSet(db, record()), /kept unchanged/);
  assert.equal(db.getItem(LOG_KEY), "bad JSON");
  assert.match(readLog('{"version":2,"sets":[]}').error!, /unsupported/);
  db.setItem(LOG_KEY, JSON.stringify({ version: 1, sets: [{ legacy: true }, record()] }));
  saveSet(db, record("b"));
  assert.equal(readLog(db.getItem(LOG_KEY)).skipped, 1);
  assert.equal(readLog(db.getItem(LOG_KEY)).sets.length, 2);
  deleteSet(db, "set-a");
  assert.deepEqual(JSON.parse(db.getItem(LOG_KEY)!).sets[0], { legacy: true });
  assert.equal(readLog(db.getItem(LOG_KEY)).sets.length, 1);
});
test("duplicate IDs and session IDs in stored data appear once", () => {
  const a = record();
  const loaded = readLog(JSON.stringify({ version: 1, sets: [a, a, { ...a, id: "b" }] }));
  assert.equal(loaded.sets.length, 1); assert.equal(loaded.skipped, 2);
});
test("no video, blob URL, raw pose track or conversation is persisted", () => {
  const db = storage(), a = { ...record(), video: "private.mp4", poseTrack: { frames: [] }, url: "blob:private", chat: "private message" };
  saveSet(db, a);
  const raw = db.getItem(LOG_KEY)!;
  for (const text of ["private.mp4", "poseTrack", "blob:private", "private message"]) assert.ok(!raw.includes(text));
  const bad = record(); Object.assign(bad.analysis, { poseTrack: { frames: [] } });
  assert.throws(() => saveSet(db, bad), /not ready/);
});
test("synthetic, placeholder, unsupported, malformed and mismatched count results cannot save", () => {
  const db = storage();
  for (const kind of ["synthetic", "placeholder"] as const) { const a = record(); a.analysis.provenance.kind = kind; assert.throws(() => saveSet(db, a)); }
  const wrong = record(); wrong.analysis.summary.totalReps = 100; assert.throws(() => saveSet(db, wrong));
  const invalid = { ...record(), analysis: { summary: {} } };
  assert.equal(readLog(JSON.stringify({ version: 1, sets: [invalid] })).skipped, 1);
  assert.deepEqual(readLog(EMPTY_LOG), { sets: [], skipped: 0, error: null });
});
test("performed dates are real calendar dates, independent of analysis date", () => {
  assert.ok(validDate("2024-02-29"));
  for (const date of ["2026-02-29", "2026-13-01", "2026-9-01", "", null]) assert.equal(validDate(date), false);
  assert.throws(() => saveSet(storage(), { ...record(), performedDate: "2026-02-30" }));
});
test("timing and movement use actual values and keep unknowns and sides separate", () => {
  const a = record();
  const values = a.analysis.reps.map(rep => rep.measurements.durationMs!);
  assert.equal(timing(a).spread, Math.max(...values) - Math.min(...values));
  assert.equal(timing(a).median, [...values].sort((a, b) => a - b)[1]);
  assert.equal(movement(a)[0].label, "Left elbow range");
  a.analysis.reps = [];
  assert.deepEqual(timing(a), { median: null, spread: null }); assert.deepEqual(movement(a), []);
});
test("comparison excludes unknown analyzer versions, different exercise and source", () => {
  const a = record(), b = record("b"); assert.equal(comparable(a, b), false);
  a.analysisRevision = "v2"; b.analysisRevision = "v2"; assert.ok(comparable(a, b));
  b.analysisRevision = "v1"; assert.equal(comparable(a, b), false);
  b.analysisRevision = "v2"; b.analysis.source.type = "live"; assert.equal(comparable(a, b), false);
  b.analysis.source.type = a.analysis.source.type; b.analysis.exercise!.id = "lat-pulldown"; assert.equal(comparable(a, b), false);
});
