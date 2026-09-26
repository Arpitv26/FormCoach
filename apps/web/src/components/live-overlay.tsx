"use client";

import { useEffect, useRef, useState, type RefObject } from "react";
import { drawPose } from "@/lib/pose/drawing";
import { startLivePose, type TrackingStatus } from "@/lib/pose/live";

const messages: Record<TrackingStatus, string> = {
  loading: "Loading skeleton tracking…",
  tracking: "Tracking visible joints · estimated positions",
  "no-person": "Looking for one person. Step back so your body is visible.",
  "multiple-people": "More than one person detected. Keep one person in frame.",
  error: "Skeleton unavailable. Stop the camera and try again. If it persists, run npm run pose:setup in apps/web, then reload.",
};

export function LiveOverlay({ video }: { video: RefObject<HTMLVideoElement | null> }) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const [status, setStatus] = useState<TrackingStatus>("loading");
  useEffect(() => {
    const player = video.current, surface = canvas.current;
    if (!player || !surface) return;
    return startLivePose(player,
      (frame) => drawPose(surface, frame, player.videoWidth, player.videoHeight), setStatus);
  }, [video]);
  return <>
    <canvas ref={canvas} aria-hidden="true" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none", transform: "scaleX(-1)" }} />
    <p role="status" style={{ position: "absolute", bottom: 12, left: 12, right: 12, margin: 0, padding: "8px 12px", background: "#080d14e6", borderRadius: 8, fontSize: ".8rem" }}>{messages[status]}</p>
  </>;
}
