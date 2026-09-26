import assert from "node:assert/strict";
import test from "node:test";
import { runInNewContext } from "node:vm";
import { configurePoseRuntimeLogging } from "../scripts/pose-runtime-logging.mjs";
import { DisplayPoseFilter } from "../src/lib/pose/display-filter";
import type { PoseFrame } from "../src/lib/api/types";

test("native startup notice becomes info; other diagnostics and global console remain unchanged", () => {
  const info: unknown[][] = [], error: unknown[][] = [];
  const logging = { info: (...args: unknown[]) => info.push(args), error: (...args: unknown[]) => error.push(args) };
  const original = logging.error;
  const source = configurePoseRuntimeLogging("var err = console.error.bind(console);");
  const emit = runInNewContext(`${source}\nerr;`, { console: logging });
  const notice = "INFO: Created TensorFlow Lite XNNPACK delegate for CPU.";
  emit(notice); emit("Model failed"); emit(notice, "extra detail");
  assert.deepEqual(info, [[notice]]);
  assert.deepEqual(error, [["Model failed"], [notice, "extra detail"]]);
  assert.equal(logging.error, original);
  assert.throws(() => configurePoseRuntimeLogging("changed vendor runtime"), /Review/);
});

const frame = (timestampMs: number, x = .3, visibility = .9): PoseFrame => ({
  frameIndex: timestampMs, timestampMs,
  landmarks: [{ index: 11, name: "left_shoulder", x, y: .4, visibility }],
});
test("display smoothing reduces small jumps without modifying analysis input", () => {
  const filter = new DisplayPoseFilter();
  filter.update(frame(0));
  const input = frame(100, .35);
  const result = filter.update(input)!;
  assert.ok(result.landmarks[0].x > .3 && result.landmarks[0].x < .35);
  assert.equal(input.landmarks[0].x, .35);
  assert.equal(result.timestampMs, input.timestampMs);
});
test("display filter never bridges occlusion, tracking gaps, clock resets or large jumps", () => {
  for (const interruption of [null, { ...frame(100), landmarks: [] }, frame(100, .35, .2)]) {
    const filter = new DisplayPoseFilter(); filter.update(frame(0)); filter.update(interruption);
    assert.equal(filter.update(frame(140, .35))!.landmarks[0].x, .35);
  }
  for (const next of [frame(151, .35), frame(0, .35), frame(100, .9)]) {
    const filter = new DisplayPoseFilter(); filter.update(frame(0));
    assert.equal(filter.update(next)!.landmarks[0].x, next.landmarks[0].x);
  }
});
