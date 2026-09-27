import type { PoseFrame } from "../api/types";
import { LANDMARK_NAMES } from "./names";

type RawPoint = { x: number; y: number; z?: number; visibility?: number };
export interface PoseDetector {
  detectForVideo(video: HTMLVideoElement, timestamp: number): { landmarks: RawPoint[][] };
  close(): void;
}
export type TrackingStatus = "loading" | "tracking" | "no-person" | "multiple-people" | "error";

export function mapBrowserPose(poses: RawPoint[][], frameIndex: number, timestampMs: number): PoseFrame {
  const single = poses.length === 1 && poses[0].length === 33 ? poses[0] : [];
  return { frameIndex, timestampMs, landmarks: single.map((point, index) => ({
    index, name: LANDMARK_NAMES[index], x: point.x, y: point.y,
    z: point.z ?? null, visibility: point.visibility ?? null,
  })) };
}

export async function loadPoseDetector(): Promise<PoseDetector> {
  const { FilesetResolver, PoseLandmarker } = await import("@mediapipe/tasks-vision");
  const model = await fetch("/pose/pose_landmarker_lite.task", { signal: AbortSignal.timeout(30_000) });
  if (!model.ok) throw new Error("Browser pose model is missing");
  const vision = await FilesetResolver.forVisionTasks("/pose/wasm");
  return PoseLandmarker.createFromOptions(vision, {
    baseOptions: { modelAssetBuffer: new Uint8Array(await model.arrayBuffer()), delegate: "CPU" },
    runningMode: "VIDEO", numPoses: 2, outputSegmentationMasks: false,
  });
}

/** Coordinates remain unmirrored; the video and canvas are mirrored together in CSS. */
export function startLivePose(
  video: HTMLVideoElement,
  onFrame: (frame: PoseFrame | null, capturedAt?: number) => void,
  onStatus: (status: TrackingStatus) => void,
  load: () => Promise<PoseDetector> = loadPoseDetector,
) {
  let stopped = false, detector: PoseDetector | null = null, animation = 0;
  let lastInference = -Infinity, lastVideoTime = -1, frameIndex = 0;
  let lastStatus: TrackingStatus | undefined;
  const start = performance.now();
  const status = (next: TrackingStatus) => {
    if (next !== lastStatus && !stopped) { lastStatus = next; onStatus(next); }
  };
  const stop = () => {
    if (stopped) return;
    stopped = true; cancelAnimationFrame(animation); detector?.close(); detector = null; onFrame(null);
  };
  const tick = (now: number) => {
    if (stopped || !detector) return;
    if (document.hidden || video.readyState < 2 || video.paused || now - lastInference > 300) onFrame(null);
    if (!document.hidden && !video.paused && video.readyState >= 2 && video.currentTime !== lastVideoTime && now - lastInference >= 100) {
      try {
        const result = detector.detectForVideo(video, now);
        lastVideoTime = video.currentTime; lastInference = now;
        const frame = mapBrowserPose(result.landmarks, frameIndex++, Math.round(now - start));
        onFrame(frame, now);
        status(result.landmarks.length > 1 ? "multiple-people" : frame.landmarks.length ? "tracking" : "no-person");
      } catch {
        status("error"); stop(); return;
      }
    }
    animation = requestAnimationFrame(tick);
  };
  status("loading");
  void load().then((ready) => {
    if (stopped) { ready.close(); return; }
    detector = ready; animation = requestAnimationFrame(tick);
  }).catch(() => { status("error"); stop(); });
  return stop;
}
