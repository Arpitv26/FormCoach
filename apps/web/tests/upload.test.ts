import assert from "node:assert/strict";
import test from "node:test";
import { ApiError } from "../src/lib/api/client";
import type { AnalysisResponse } from "../src/lib/api/types";
import { emptyUploadState, MAX_VIDEO_BYTES, UploadSession, uploadError, validateMetadata, validateVideo } from "../src/lib/video/upload-session";
const clip = (name = "push-ups.mp4") => new File(["video"], name);
function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
function setup(analyze: (file: File, signal: AbortSignal) => Promise<AnalysisResponse>) {
  let state = emptyUploadState;
  let changes = 0;
  let urls = 0;
  const revoked: string[] = [];
  const session = new UploadSession(analyze, (next) => { state = next; changes++; }, {
    createObjectURL: () => `blob:${++urls}`, revokeObjectURL: (url) => revoked.push(url),
  });
  return { session, revoked, get state() { return state; }, get changes() { return changes; } };
}
test("video extension, size, duration and resolution limits", () => {
  assert.match(validateVideo({ name: "a.mp4", size: 0 })!, /empty/);
  assert.match(validateVideo({ name: "a.png", size: 10 })!, /MP4/);
  assert.match(validateVideo({ name: "a.mp4", size: MAX_VIDEO_BYTES + 1 })!, /250/);
  assert.equal(validateVideo({ name: "a.MOV", size: MAX_VIDEO_BYTES }), null);
  assert.match(validateMetadata(121, 1920, 1080)!, /two minutes/);
  assert.match(validateMetadata(60, 4096, 2160)!, /4K/);
  assert.match(validateMetadata(60, 5000, 100)!, /4096/);
  assert.equal(validateMetadata(120, 2160, 3840), null);
});
test("duplicate submits blocked; replacing file ignores stale response", async () => {
  const pending = deferred<AnalysisResponse>();
  let calls = 0;
  let signal: AbortSignal | undefined;
  const app = setup(async (_file, nextSignal) => { calls++; signal = nextSignal; return pending.promise; });
  app.session.select(clip());
  const first = app.session.submit();
  await app.session.submit();
  assert.equal(calls, 1);
  app.session.select(clip("other.mov"));
  assert.equal(signal?.aborted, true);
  assert.deepEqual(app.revoked, ["blob:1"]);
  pending.resolve({ sessionId: "old" } as AnalysisResponse);
  await first;
  assert.equal(app.state.result, null);
  assert.equal(app.state.selection?.file.name, "other.mov");
  app.session.dispose();
  assert.deepEqual(app.revoked, ["blob:1", "blob:2"]);
});
test("cancel protects a new request from late failure", async () => {
  const old = deferred<AnalysisResponse>();
  const next = deferred<AnalysisResponse>();
  let calls = 0;
  const app = setup(() => ++calls === 1 ? old.promise : next.promise);
  app.session.select(clip());
  const first = app.session.submit();
  app.session.cancel();
  assert.match(app.state.message!, /server may still/);
  const second = app.session.submit();
  old.reject(new Error("old failure"));
  await first;
  assert.equal(app.state.phase, "analyzing");
  const response = { sessionId: "new" } as AnalysisResponse;
  next.resolve(response);
  await second;
  assert.equal(app.state.result, response);
  app.session.dispose();
});
test("dispose releases URL and prevents late updates", async () => {
  const pending = deferred<AnalysisResponse>();
  const app = setup(() => pending.promise);
  app.session.select(clip());
  const request = app.session.submit();
  app.session.dispose();
  const changes = app.changes;
  pending.resolve({} as AnalysisResponse);
  await request;
  app.session.select(clip());
  assert.equal(app.changes, changes);
  assert.deepEqual(app.revoked, ["blob:1"]);
});
test("metadata blocks invalid clips, ignores old clips; failed preview permits upload", async () => {
  let calls = 0;
  const app = setup(async () => { calls++; throw new ApiError(501, "Not implemented", "VIDEO_ANALYSIS_NOT_IMPLEMENTED"); });
  app.session.select(clip());
  app.session.metadata("blob:1", 130, 1920, 1080);
  await app.session.submit();
  assert.equal(calls, 0);
  app.session.select(clip("second.mov"));
  app.session.metadata("blob:1", 130, 1920, 1080);
  assert.equal(app.state.validationError, null);
  app.session.previewFailed("blob:2");
  await app.session.submit();
  assert.equal(calls, 1);
  assert.equal(app.state.preview, "unplayable");
  assert.equal(app.state.result, null);
  assert.match(app.state.message!, /updated backend-cv/);
  app.session.select(null);
  assert.equal(app.state.message, null);
  assert.equal(app.state.selection, null);
});
test("busy, setup and timeout errors explain next action", () => {
  assert.match(uploadError(new ApiError(503, "busy", "VIDEO_PROCESSOR_BUSY")), /Wait/);
  assert.match(uploadError(new ApiError(503, "setup", "VIDEO_SETUP_REQUIRED")), /pose model/);
  assert.match(uploadError(new ApiError(0, "timeout", "REQUEST_TIMEOUT")), /server may still/);
});
