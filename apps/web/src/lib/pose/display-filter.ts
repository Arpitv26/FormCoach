import type { PoseFrame } from "../api/types";
import { visibleJoint } from "./drawing";

/** Light smoothing for live display only. Never reuse this output for measurements. */
export class DisplayPoseFilter {
  private previous: PoseFrame | null = null;

  update(frame: PoseFrame | null): PoseFrame | null {
    if (!frame) { this.previous = null; return null; }
    const elapsed = this.previous ? frame.timestampMs - this.previous.timestampMs : Infinity;
    const prior = new Map(elapsed > 0 && elapsed <= 150
      ? this.previous?.landmarks.map((joint) => [joint.index, joint]) : []);
    const alpha = 1 - Math.exp(-elapsed / 70);
    const result: PoseFrame = { ...frame, landmarks: frame.landmarks.filter(visibleJoint).map((joint) => {
      const old = prior.get(joint.index);
      // Large changes may be reacquisition or a different person; never slide between bodies.
      if (!old || Math.hypot(joint.x - old.x, joint.y - old.y) > 0.15) return { ...joint };
      return { ...joint, x: old.x + alpha * (joint.x - old.x), y: old.y + alpha * (joint.y - old.y) };
    }) };
    this.previous = result;
    return result;
  }
}
