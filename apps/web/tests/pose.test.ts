import assert from "node:assert/strict";
import test from "node:test";
import type { PoseFrame, PoseLandmark, VideoAnalysisResponse } from "../src/lib/api/types";
import { containedRect, frameAt, visibleJoint } from "../src/lib/pose/drawing";
import { mapBrowserPose, startLivePose } from "../src/lib/pose/live";
import { UploadSession, emptyUploadState } from "../src/lib/video/upload-session";

test("playback seeks backwards, hides stale gaps and never uses a future sample", () => {
  const frames: PoseFrame[] = [0, 67, 500].map((timestampMs, frameIndex) => ({ timestampMs, frameIndex, landmarks: [] }));
  assert.equal(frameAt(frames, -1), null);
  assert.equal(frameAt(frames, 60), frames[0]);
  assert.equal(frameAt(frames, 500), frames[2]);
  assert.equal(frameAt(frames, 67), frames[1]);
  assert.equal(frameAt(frames, 300), null);
  assert.equal(frameAt([], 0), null);
});
test("letterboxing preserves portrait and landscape proportions", () => {
  assert.deepEqual(containedRect(400, 300, 1600, 900), { x: 0, y: 37.5, width: 400, height: 225 });
  assert.deepEqual(containedRect(400, 300, 900, 1600), { x: 115.625, y: 0, width: 168.75, height: 300 });
});
test("unknown, obscured and offscreen joints are hidden rather than clamped", () => {
  const point: PoseLandmark = { index: 11, name: "left_shoulder", x: .2, y: .4, visibility: .9 };
  assert.equal(visibleJoint(point), true);
  for (const patch of [{ visibility: null }, { visibility: .69 }, { x: -0.01 }, { y: 1.01 }, { x: NaN }])
    assert.equal(visibleJoint({ ...point, ...patch }), false);
});
test("browser adapter retains anatomical indices and unmirrored coordinates; rejects multiple people", () => {
  const points = Array.from({ length: 33 }, () => ({ x: .2, y: .4, z: -.1, visibility: .9 }));
  const frame = mapBrowserPose([points], 2, 100);
  assert.equal(frame.landmarks[11].name, "left_shoulder");
  assert.equal(frame.landmarks[11].x, .2);
  assert.equal(frame.timestampMs, 100);
  assert.deepEqual(mapBrowserPose([points, points], 3, 200).landmarks, []);
  assert.deepEqual(mapBrowserPose([], 4, 300).landmarks, []);
});
test("stopping during model initialization closes the late detector without drawing", async () => {
  let resolve!: (value: { detectForVideo: () => { landmarks: [] }; close: () => void }) => void;
  let closed = 0;
  const frames: (PoseFrame | null)[] = [];
  const oldCancel = globalThis.cancelAnimationFrame;
  globalThis.cancelAnimationFrame = () => {};
  try {
    const stop = startLivePose({} as HTMLVideoElement, (frame) => frames.push(frame), () => {},
      () => new Promise((done) => { resolve = done; }));
    stop(); stop();
    resolve({ detectForVideo: () => ({ landmarks: [] }), close: () => { closed++; } });
    await Promise.resolve();
    assert.equal(closed, 1);
    assert.deepEqual(frames, [null]);
  } finally { globalThis.cancelAnimationFrame = oldCancel; }
});
test("pose track is tied to its upload and cleared when another clip is selected", async () => {
  let state = emptyUploadState;
  const response = { analysis: { sessionId: "paired" }, poseTrack: { frames: [] } } as unknown as VideoAnalysisResponse;
  const session = new UploadSession(async () => response, (next) => { state = next; }, {
    createObjectURL: () => "blob:test", revokeObjectURL: () => {},
  });
  session.select(new File(["video"], "clip.mov")); await session.submit();
  assert.equal(state.result, response.analysis); assert.equal(state.poseTrack, response.poseTrack);
  session.select(new File(["next"], "other.mov"));
  assert.equal(state.poseTrack, null); assert.equal(state.result, null);
  session.dispose();
});

test("a display timeout never inserts a fake missing pose before the fresh observation", async () => {
  const previous = { raf: globalThis.requestAnimationFrame, cancel: globalThis.cancelAnimationFrame, document: globalThis.document };
  let tick!: FrameRequestCallback;
  let displayGaps = 0;
  const frames: (PoseFrame | null)[] = [];
  const video = { readyState: 2, paused: false, currentTime: 0 } as HTMLVideoElement;
  const points = Array.from({ length: 33 }, () => ({ x: .4, y: .4, visibility: .9 }));
  globalThis.requestAnimationFrame = (callback) => { tick = callback; return 1; };
  globalThis.cancelAnimationFrame = () => {};
  Object.defineProperty(globalThis, "document", { configurable: true, value: { hidden: false } });
  try {
    const stop = startLivePose(video, (frame) => frames.push(frame), () => {},
      async () => ({ detectForVideo: () => ({ landmarks: [points] }), close() {} }), () => { displayGaps++; });
    await Promise.resolve();
    tick(1000);
    video.currentTime = 1;
    tick(1400);
    assert.equal(displayGaps, 2);
    assert.equal(frames.length, 2);
    assert.ok(frames.every((frame) => frame?.landmarks.length === 33));
    stop();
  } finally {
    globalThis.requestAnimationFrame = previous.raf;
    globalThis.cancelAnimationFrame = previous.cancel;
    Object.defineProperty(globalThis, "document", { configurable: true, value: previous.document });
  }
});
