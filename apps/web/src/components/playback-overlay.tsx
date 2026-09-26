"use client";

import { useEffect, useRef, type RefObject } from "react";
import type { PoseTrack } from "@/lib/api/types";
import { drawPose, frameAt } from "@/lib/pose/drawing";

export function PlaybackOverlay({ video, track, enabled }: {
  video: RefObject<HTMLVideoElement | null>; track: PoseTrack | null; enabled: boolean;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const player = video.current, surface = canvas.current;
    if (!player || !surface) return;
    let animation = 0;
    const render = () => {
      const aspectMatches = track && player.videoWidth > 0 &&
        Math.abs(player.videoWidth / player.videoHeight - track.imageWidth / track.imageHeight) < 0.01;
      drawPose(surface, enabled && track && aspectMatches && !player.seeking && player.readyState >= 2
        ? frameAt(track.frames, player.currentTime * 1000) : null,
      track?.imageWidth ?? 1, track?.imageHeight ?? 1);
      animation = requestAnimationFrame(render);
    };
    render();
    return () => { cancelAnimationFrame(animation); drawPose(surface, null, 1, 1); };
  }, [video, track, enabled]);
  return <canvas ref={canvas} aria-hidden="true" style={{ position: "absolute", inset: 0, width: "100%", height: "100%", pointerEvents: "none" }} />;
}
