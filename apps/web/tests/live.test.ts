import assert from "node:assert/strict";
import test from "node:test";
import fixture from "../../../contracts/examples/pushup-analysis.json";
import type { AnalysisResponse, LiveBatchRequest, PoseFrame } from "../src/lib/api/types";
import { LiveSession, initialLiveState, LIVE_LIMIT_MS } from "../src/lib/live/session";
const flush = async () => { await Promise.resolve(); await Promise.resolve(); await Promise.resolve(); };
const pose = (): PoseFrame => ({ frameIndex: 80, timestampMs: 99999, landmarks: [{ index: 11, name: "left_shoulder", x: .123, y: .4, z: null, visibility: .9 }] });
function result(batch: LiveBatchRequest, count: number | null = 1): AnalysisResponse {
  return { ...fixture, sessionId: batch.sessionId, source: { type: "live", durationMs: batch.frames.at(-1)?.timestampMs ?? null }, summary: { ...fixture.summary, totalReps: count }, status: batch.isFinal ? "complete" : "partial" } as AnalysisResponse;
}
function setup(request?: (batch: LiveBatchRequest, signal: AbortSignal) => Promise<AnalysisResponse>) {
  let clock = 5000, ids = 0, state = initialLiveState;
  const requests: LiveBatchRequest[] = [];
  const signals: AbortSignal[] = [];
  const session = new LiveSession((batch, signal) => { requests.push(batch); signals.push(signal); return request ? request(batch, signal) : Promise.resolve(result(batch)); }, (next) => { state = next; }, () => clock, () => `set-${++ids}`);
  return { session, requests, signals, get state() { return state; }, time: (ms: number) => { clock = ms; } };
}

test("live snapshots are cumulative, counts replace, timestamps reset and raw coordinates survive", async () => {
  const app = setup((batch) => Promise.resolve(result(batch, batch.frames.length)));
  app.session.start(1280, 720);
  const raw = pose();
  app.session.capture(raw, 1280, 720);
  raw.landmarks[0].x = .999;
  app.time(5100); app.session.capture(pose(), 1280, 720);
  app.time(6000); app.session.pulse(); await flush();
  assert.equal(app.requests[0].frames[0].timestampMs, 0);
  assert.equal(app.requests[0].frames[0].landmarks[0].x, .123);
  assert.equal(app.requests[0].exerciseHint, "push-up");
  assert.equal(app.state.result?.summary.totalReps, 2);
  app.time(6100); app.session.capture(pose(), 1280, 720);
  app.time(7000); app.session.pulse(); await flush();
  assert.equal(app.requests[0].frames.length, 2);
  assert.equal(app.requests[1].frames.length, 3);
  assert.equal(app.state.result?.summary.totalReps, 3);
  app.session.finish(); await flush();
  assert.equal(app.requests[2].isFinal, true);
  assert.equal(app.state.phase, "finished");
  app.session.reset(); app.session.start(640, 480); app.session.capture(pose(), 640, 480);
  app.time(8000); app.session.pulse(); await flush();
  assert.equal(app.requests[3].sessionId, "set-2");
  assert.equal(app.requests[3].frames[0].timestampMs, 0);
  assert.equal(app.requests[3].imageWidth, 640);
});

test("finish queues behind one pending request and freezes the final snapshot", async () => {
  let resolve!: (value: AnalysisResponse) => void;
  const app = setup((batch) => batch.isFinal ? Promise.resolve(result(batch)) : new Promise((done) => { resolve = done; }));
  app.session.start(1280, 720); app.session.capture(pose(), 1280, 720);
  app.time(6000); app.session.pulse();
  app.time(6100); app.session.capture(pose(), 1280, 720);
  app.time(7000); app.session.pulse(); app.session.finish(); app.session.finish();
  app.session.capture(pose(), 1280, 720);
  assert.equal(app.requests.length, 1);
  assert.equal(app.state.phase, "finishing");
  resolve(result(app.requests[0])); await flush();
  assert.equal(app.requests.length, 2);
  assert.equal(app.requests[1].isFinal, true);
  assert.equal(app.requests[1].frames.length, 2);
  assert.equal(app.state.phase, "finished");
});

test("reset aborts request; stale results and dispose cannot revive the old session", async () => {
  let resolve!: (value: AnalysisResponse) => void;
  const app = setup(() => new Promise((done) => { resolve = done; }));
  app.session.start(1280, 720); app.session.capture(pose(), 1280, 720);
  app.time(6000); app.session.pulse(); app.session.reset();
  assert.equal(app.signals[0].aborted, true);
  app.session.start(1280, 720);
  resolve(result(app.requests[0], 8)); await flush();
  assert.equal(app.state.result, null);
  assert.equal(app.state.sessionId, "set-2");
  app.session.dispose();
  app.time(10000); app.session.pulse(); app.session.finish();
  assert.equal(app.requests.length, 1);
});

test("tracking gaps stay empty; dimensions finalize before accepting a changed image", async () => {
  const app = setup();
  app.session.start(1280, 720); app.session.capture(pose(), 1280, 720);
  app.time(5050); app.session.capture(pose(), 1280, 720); // higher-rate samples omitted
  app.time(5100); app.session.capture(null, 1280, 720);
  app.time(5600); app.session.capture(pose(), 1280, 720);
  app.time(5700); app.session.capture(pose(), 720, 1280); await flush();
  assert.deepEqual(app.requests[0].frames.map((f) => f.timestampMs), [0, 100, 600]);
  assert.deepEqual(app.requests[0].frames[1].landmarks, []);
  assert.equal(app.requests[0].imageWidth, 1280);
  assert.equal(app.requests[0].isFinal, true);
  assert.match(app.state.message!, /dimensions changed/);
});

test("two minute bound auto-finalizes once, even without a detected person", async () => {
  const app = setup();
  app.session.start(1280, 720);
  for (let elapsed = 0; elapsed <= LIVE_LIMIT_MS; elapsed += 100) {
    app.time(5000 + elapsed); app.session.capture(null, 1280, 720);
  }
  await flush(); app.session.pulse();
  assert.equal(app.requests.length, 1);
  assert.equal(app.requests[0].isFinal, true);
  assert.equal(app.requests[0].frames.length, 1201);
  assert.ok(app.requests[0].frames.length <= 1800);
  assert.equal(app.requests[0].frames.at(-1)?.timestampMs, LIVE_LIMIT_MS);
  const empty = setup(); empty.session.start(1280, 720); empty.time(5000 + LIVE_LIMIT_MS + 5000); empty.session.pulse(); await flush();
  assert.deepEqual(empty.requests[0].frames, []);
  assert.equal(empty.state.elapsedMs, LIVE_LIMIT_MS);
});

test("backend failure freezes capture, avoids auto-retry and allows explicit final retry", async () => {
  let failing = true;
  const app = setup(async (batch) => { if (failing) throw new Error("Backend unavailable"); return result(batch, 0); });
  app.session.start(1280, 720); app.session.capture(pose(), 1280, 720);
  app.time(6000); app.session.pulse(); await flush();
  assert.equal(app.state.phase, "error");
  app.time(7000); app.session.capture(pose(), 1280, 720); app.session.pulse();
  assert.equal(app.requests.length, 1);
  failing = false; app.session.retryFinal(); await flush();
  assert.equal(app.requests[1].isFinal, true);
  assert.equal(app.requests[1].frames.length, 1);
  assert.equal(app.state.result?.summary.totalReps, 0);
  assert.equal(app.state.phase, "finished");
});

test("invalid dimensions and unrelated responses are rejected", async () => {
  const app = setup(async (batch) => ({ ...result(batch), sessionId: "other-set" }));
  app.session.start(0, 720);
  assert.equal(app.state.phase, "idle");
  assert.match(app.state.error!, /Wait for the camera/);
  app.session.start(1280, 720); app.session.finish(); await flush();
  assert.equal(app.state.result, null);
  assert.equal(app.state.phase, "error");
  assert.match(app.state.error!, /did not match/);
});
