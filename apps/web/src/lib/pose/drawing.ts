import type { PoseFrame, PoseLandmark } from "../api/types";

// Anatomical connections in our canonical 33-landmark format. No provider SDK in rendering.
export const CONNECTIONS = [
  [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
  [11, 23], [12, 24], [23, 24], [23, 25], [25, 27], [24, 26], [26, 28],
  [27, 29], [29, 31], [27, 31], [28, 30], [30, 32], [28, 32],
] as const;

export function visibleJoint(point: PoseLandmark): boolean {
  return (point.visibility ?? 0) >= 0.7 && Number.isFinite(point.x) && Number.isFinite(point.y)
    && point.x >= 0 && point.x <= 1 && point.y >= 0 && point.y <= 1;
}

/** Most recent observation, never a future frame; gaps and stale samples hide the skeleton. */
export function frameAt(frames: PoseFrame[], timestampMs: number): PoseFrame | null {
  let low = 0, high = frames.length - 1;
  while (low <= high) {
    const middle = (low + high) >>> 1;
    if (frames[middle].timestampMs <= timestampMs) low = middle + 1;
    else high = middle - 1;
  }
  const frame = frames[high];
  return frame && timestampMs - frame.timestampMs <= 150 ? frame : null;
}

export function containedRect(width: number, height: number, imageWidth: number, imageHeight: number) {
  const scale = Math.min(width / imageWidth, height / imageHeight);
  const w = imageWidth * scale, h = imageHeight * scale;
  return { x: (width - w) / 2, y: (height - h) / 2, width: w, height: h };
}

export function drawPose(canvas: HTMLCanvasElement, frame: PoseFrame | null, imageWidth: number, imageHeight: number) {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.round(width * ratio) || canvas.height !== Math.round(height * ratio)) {
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
  }
  const context = canvas.getContext("2d");
  if (!context) return;
  context.setTransform(ratio, 0, 0, ratio, 0, 0);
  context.clearRect(0, 0, width, height);
  if (!frame || imageWidth <= 0 || imageHeight <= 0) return;
  const rect = containedRect(width, height, imageWidth, imageHeight);
  const points = new Map(frame.landmarks.filter(visibleJoint).map((joint) => [joint.index, {
    x: rect.x + joint.x * rect.width, y: rect.y + joint.y * rect.height,
  }]));
  context.lineCap = "round";
  // Dark outline stays legible on bright gym walls. Colour indicates tracking, never form quality.
  for (const [colour, lineWidth] of [["#07131e", 6], ["#d9fc7b", 3]] as const) {
    context.strokeStyle = colour; context.lineWidth = lineWidth;
    for (const [from, to] of CONNECTIONS) {
      const a = points.get(from), b = points.get(to);
      if (!a || !b) continue;
      context.beginPath(); context.moveTo(a.x, a.y); context.lineTo(b.x, b.y); context.stroke();
    }
  }
  const bodyIndices = new Set<number>(CONNECTIONS.flat());
  for (const [index, point] of points) {
    if (!bodyIndices.has(index)) continue;
    context.beginPath(); context.arc(point.x, point.y, 4, 0, Math.PI * 2);
    context.fillStyle = "#f4fff2"; context.fill();
    context.strokeStyle = "#07131e"; context.lineWidth = 1.5; context.stroke();
  }
}
