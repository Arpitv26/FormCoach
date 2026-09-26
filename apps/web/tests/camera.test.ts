import assert from "node:assert/strict";
import test from "node:test";
import { CameraPreview, type CameraState } from "../src/lib/camera/preview";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<T>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}

function fakeStream() {
  const track = Object.assign(new EventTarget(), {
    readyState: "live",
    stop() { this.readyState = "ended"; },
  });
  const stream = { getTracks: () => [track], getVideoTracks: () => [track] } as unknown as MediaStream;
  return { stream, track };
}

function setup(getMedia: () => Promise<MediaStream>, play = async () => {}) {
  const states: CameraState[] = [];
  const video = { srcObject: null as HTMLVideoElement["srcObject"], play, pause() {} };
  const preview = new CameraPreview(video, getMedia, (state) => states.push(state));
  return { preview, states, video };
}

test("preview starts, stops its tracks, and can restart", async () => {
  let source = fakeStream();
  const { preview, states, video } = setup(async () => source.stream);
  await preview.start();
  assert.equal(states.at(-1)?.phase, "live");
  assert.equal(video.srcObject, source.stream);
  preview.stop();
  assert.equal(source.track.readyState, "ended");
  assert.equal(video.srcObject, null);
  source = fakeStream();
  await preview.start();
  assert.equal(states.at(-1)?.phase, "live");
  preview.dispose();
  assert.equal(source.track.readyState, "ended");
  assert.equal(video.srcObject, null);
});

for (const action of ["stop", "dispose"] as const) {
  test(`permission granted after ${action} immediately releases the stream`, async () => {
    const request = deferred<MediaStream>();
    const source = fakeStream();
    const { preview, states, video } = setup(() => request.promise);
    const pending = preview.start();
    preview[action]();
    const count = states.length;
    request.resolve(source.stream);
    await pending;
    assert.equal(source.track.readyState, "ended");
    assert.equal(video.srcObject, null);
    assert.equal(states.length, count);
  });
}

test("repeated start while waiting does not request a second camera", async () => {
  const request = deferred<MediaStream>();
  let requests = 0;
  const { preview } = setup(() => { requests++; return request.promise; });
  const pending = preview.start();
  await preview.start();
  assert.equal(requests, 1);
  preview.stop();
  request.resolve(fakeStream().stream);
  await pending;
});

test("an old permission failure cannot replace a newer live preview", async () => {
  const first = deferred<MediaStream>();
  const source = fakeStream();
  let requests = 0;
  const { preview, states, video } = setup(() => ++requests === 1 ? first.promise : Promise.resolve(source.stream));
  const pending = preview.start();
  preview.stop();
  await preview.start();
  first.reject(new DOMException("Denied", "NotAllowedError"));
  await pending;
  assert.equal(states.at(-1)?.phase, "live");
  assert.equal(video.srcObject, source.stream);
  preview.dispose();
});

test("stopping during playback startup cannot return to live", async () => {
  const source = fakeStream();
  const playing = deferred<void>();
  const { preview, states } = setup(async () => source.stream, () => playing.promise);
  const pending = preview.start();
  await Promise.resolve();
  assert.equal(states.at(-1)?.phase, "starting");
  preview.stop();
  playing.resolve();
  await pending;
  assert.equal(states.at(-1)?.phase, "stopped");
  assert.equal(source.track.readyState, "ended");
});

test("playback rejection releases the camera and reports a retryable error", async () => {
  const source = fakeStream();
  const { preview, states, video } = setup(async () => source.stream, async () => { throw new Error("play failed"); });
  await preview.start();
  assert.equal(states.at(-1)?.phase, "error");
  assert.match(states.at(-1)!.message, /preview could not play/);
  assert.equal(source.track.readyState, "ended");
  assert.equal(video.srcObject, null);
});

test("camera loss detaches the preview and reports disconnection", async () => {
  const source = fakeStream();
  const { preview, states, video } = setup(async () => source.stream);
  await preview.start();
  source.track.dispatchEvent(new Event("ended"));
  assert.equal(states.at(-1)?.phase, "error");
  assert.match(states.at(-1)!.message, /disconnected/);
  assert.equal(source.track.readyState, "ended");
  assert.equal(video.srcObject, null);
});

for (const [name, message] of [["NotAllowedError", /access was blocked/], ["NotFoundError", /No camera/], ["NotReadableError", /Close other apps/]] as const) {
  test(`${name} is actionable and permits retry`, async () => {
    let fail = true;
    const source = fakeStream();
    const { preview, states } = setup(async () => {
      if (fail) throw new DOMException("Device error", name);
      return source.stream;
    });
    await preview.start();
    assert.equal(states.at(-1)?.phase, "error");
    assert.match(states.at(-1)!.message, message);
    fail = false;
    await preview.start();
    assert.equal(states.at(-1)?.phase, "live");
    preview.dispose();
  });
}
