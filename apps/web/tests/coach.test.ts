import assert from "node:assert/strict";
import test from "node:test";
import fixture from "../../../contracts/examples/pushup-comparison-analysis.json";
import type { AnalysisResponse, CoachRequest, CoachResponse } from "../src/lib/api/types";
import { CoachSession, initialCoachState } from "../src/lib/coach/session";
import { describeEvidence, evidenceValue } from "../src/lib/coach/evidence";

const analysis = fixture as AnalysisResponse;
const response = (mode: CoachRequest["mode"] = "summary"): CoachResponse => ({ contractVersion: "1.0", sessionId: analysis.sessionId, mode, provider: "fallback", message: "Demo data only", evidence: ["reps.2.measurements.durationMs"], limitations: ["No form score"] });

test("coach sends current analysis in all modes and rejects blank/long QA", async () => {
  const requests: CoachRequest[] = [];
  let state = initialCoachState;
  const session = new CoachSession(analysis, async (input) => { requests.push(input); return response(input.mode); }, (next) => { state = next; });
  await session.submit("summary");
  await session.submit("next_set");
  await session.submit("qa", " How long did rep 3 take? ");
  assert.deepEqual(requests.map((r) => r.mode), ["summary", "next_set", "qa"]);
  assert.equal(requests[2].question, "How long did rep 3 take?");
  assert.equal(requests[0].analysis, analysis);
  assert.equal(state.result?.provider, "fallback");
  await session.submit("qa", "  ");
  assert.match(state.error!, /Enter a question/);
  await session.submit("qa", "x".repeat(1001));
  assert.equal(requests.length, 3);
});

test("duplicate coach requests blocked; disposed analysis cannot deliver late response", async () => {
  let resolve!: (r: CoachResponse) => void;
  let signal!: AbortSignal;
  let calls = 0, changes = 0;
  const session = new CoachSession(analysis, (_input, nextSignal) => { calls++; signal = nextSignal; return new Promise((done) => { resolve = done; }); }, () => { changes++; });
  const request = session.submit("summary");
  await session.submit("next_set");
  assert.equal(calls, 1);
  session.dispose();
  assert.equal(signal.aborted, true);
  const before = changes;
  resolve(response()); await request;
  assert.equal(changes, before);
});

test("cancel and mismatched responses cannot show unrelated evidence; retry is explicit", async () => {
  let state = initialCoachState;
  const session = new CoachSession(analysis, async () => ({ ...response(), sessionId: "wrong" }), (next) => { state = next; });
  await session.submit("summary");
  assert.equal(state.result, null);
  assert.match(state.error!, /did not match/);
  session.cancel();
  assert.match(state.error!, /Stopped waiting/);
});

test("evidence resolves zero-based reps, preserves unknowns and blocks prototype paths", () => {
  const item = describeEvidence(analysis, "reps.2.measurements.durationMs");
  assert.equal(item.rep?.repNumber, 3);
  assert.equal(item.text, "3.20 s");
  assert.equal(evidenceValue(analysis, "summary.overallScore"), null);
  assert.equal(describeEvidence(analysis, "summary.overallScore").text, "Unavailable");
  for (const path of ["__proto__.toString", "constructor.name", "reps.100.score", "reps.-1", "reps.0.measurements.__proto__"]) assert.equal(evidenceValue(analysis, path), undefined);
  assert.equal(describeEvidence({ ...analysis, summary: { ...analysis.summary, totalReps: 0 } }, "summary.totalReps").text, "0");
});

test("conversation sends bounded successful history and cancellation does not add a turn", async () => {
  const requests: CoachRequest[] = [];
  let state = initialCoachState;
  const session = new CoachSession(analysis, async (input) => { requests.push(input); return response(input.mode); }, (next) => { state = next; });
  await session.submit("summary");
  await session.submit("qa", "I actually did five. Why did you miss some?");
  assert.equal(requests[1].responseStyle, "conversation");
  assert.deepEqual(requests[1].history?.map((turn) => turn.role), ["user", "assistant"]);
  assert.equal(requests[1].history?.[0].content, "How did my set go?");
  assert.equal(state.exchanges.length, 2);
  for (let i = 0; i < 7; i++) await session.submit("qa", "And that one?");
  assert.equal(requests.at(-1)?.history?.length, 12);
  assert.equal(state.exchanges.length, 6);
  session.cancel();
  assert.equal(state.exchanges.length, 6);
});
