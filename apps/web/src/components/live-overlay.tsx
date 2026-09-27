"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import type { PoseFrame } from "@/lib/api/types";
import { drawPose } from "@/lib/pose/drawing";
import { DisplayPoseFilter } from "@/lib/pose/display-filter";
import { startLivePose, type TrackingStatus } from "@/lib/pose/live";

const messages: Record<TrackingStatus, string> = {
  loading: "Loading skeleton tracking…",
  tracking: "Tracking visible joints · estimated positions",
  "no-person": "Looking for one person. Step back so your body is visible.",
  "multiple-people": "More than one person detected. Keep one person in frame.",
  error: "Skeleton unavailable. Stop the camera and try again. If it persists, run npm run pose:setup in apps/web, then reload.",
};

export function LiveOverlay({ video, onFrame, onStatus }: {
  video: RefObject<HTMLVideoElement | null>;
  onFrame?: (frame: PoseFrame | null, width: number, height: number, capturedAt: number) => void;
  onStatus?: (status: TrackingStatus) => void;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<TrackingStatus>("loading");
  useEffect(() => {
    const player = video.current, surface = canvas.current;
    if (!player || !surface) return;
    const filter = new DisplayPoseFilter();
    return startLivePose(player,
      (frame, capturedAt) => {
        // Analysis receives the raw unmirrored frame, before display-only smoothing.
        onFrame?.(frame, player.videoWidth, player.videoHeight, capturedAt ?? performance.now());
        drawPose(surface, filter.update(frame), player.videoWidth, player.videoHeight);
      }, (next) => { setStatus(next); onStatus?.(next); });
  }, [video, onFrame, onStatus]);
  return <>
    <canvas ref={canvas} aria-hidden="true" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none", transform: "scaleX(-1)" }} />
    <p role="status" style={{ position: "absolute", bottom: 12, left: 12, right: 12, margin: 0, padding: "8px 12px", background: "#080d14e6", borderRadius: 8, fontSize: ".8rem" }}>{messages[status]}</p>
  </>;
}
