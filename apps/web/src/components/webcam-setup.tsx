"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { type ExerciseOption } from "@/lib/exercises";
import { CameraPreview, initialCameraState, type CameraState } from "@/lib/camera/preview";
import { api } from "@/lib/api/client";
import type { PoseFrame } from "@/lib/api/types";
import type { TrackingStatus } from "@/lib/pose/live";
import { LiveSession, initialLiveState } from "@/lib/live/session";
import { LiveSessionPanel } from "./live-session-panel";
import { SaveSet } from "./save-set";
import { AnalysisDetails } from "./analysis-details";
import { UploadedResults } from "./uploaded-results";
import { LiveOverlay } from "./live-overlay";
import styles from "./webcam-setup.module.css";

const labels: Record<CameraState["phase"], string> = {
  idle: "Camera is off",
  requesting: "Waiting for permission",
  starting: "Opening preview",
  live: "Camera preview on",
  stopped: "Camera stopped",
  error: "Camera needs attention",
};

export function WebcamSetup({ exercise }: { exercise: ExerciseOption }) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewRef = useRef<CameraPreview | null>(null);
  const [state, setState] = useState(initialCameraState);
  const [liveState, setLiveState] = useState(initialLiveState);
  const [tracking, setTracking] = useState<TrackingStatus>("loading");
  useEffect(() => {
    if (liveState.phase === "finishing" || liveState.phase === "finished") previewRef.current?.stop();
  }, [liveState.phase]);
  const counterRef = useRef<LiveSession | null>(null);
  const handlePose = useCallback((frame: PoseFrame | null, width: number, height: number, capturedAt: number) => {
    counterRef.current?.capture(frame, width, height, capturedAt);
  }, []);
  const handleTracking = useCallback((status: TrackingStatus) => {
    setTracking(status);
    if (status === "error") counterRef.current?.finish("Skeleton tracking stopped. Review the final available observations before starting again.");
  }, []);

  useEffect(() => {
    if (!videoRef.current) return;
    const counter = new LiveSession((batch, signal) => api.analyzeLiveBatch(batch, signal), setLiveState);
    counterRef.current = counter;
    const pulse = window.setInterval(() => counter.pulse(), 250);
    const onVisibility = () => { if (document.hidden) counter.finish("The page became hidden. This set ended with the available observations."); };
    document.addEventListener("visibilitychange", onVisibility);
    const preview = new CameraPreview(videoRef.current, () => navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    }), (next) => {
      setState(next);
      if (next.phase !== "live") setTracking("loading");
      if (next.phase === "stopped" || next.phase === "error") counter.finish("The camera stopped. This set ended with the available observations.");
    });
    previewRef.current = preview;
    const onPageHide = () => { counter.reset(); preview.stop(); };
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
      window.clearInterval(pulse);
      document.removeEventListener("visibilitychange", onVisibility);
      counter.dispose();
      counterRef.current = null;
      preview.dispose();
      previewRef.current = null;
    };
  }, []);

  function enableCamera() {
    if (!window.isSecureContext) {
      setState({ phase: "error", message: "Camera access needs a secure page. Open this app on localhost or an HTTPS address, then try again." });
      return;
    }
    if (!navigator.mediaDevices?.getUserMedia) {
      setState({ phase: "error", message: "This browser does not support camera access here. Try a current browser such as Chrome or Safari." });
      return;
    }
    void previewRef.current?.start();
  }

  const busy = state.phase === "requesting" || state.phase === "starting";
  const live = state.phase === "live";

  const finished = liveState.phase === "finished";
  function downloadCapture() {
    const batch = counterRef.current?.snapshot();
    if (!batch) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(batch)], { type: "application/json" }));
    const anchor = document.createElement("a");
    anchor.href = url; anchor.download = `formcoach-live-${batch.sessionId}.json`; anchor.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  return (
    <div className={finished || liveState.phase === "capturing" || liveState.phase === "finishing" ? styles.finishedLayout : styles.layout}>
      <div className={styles.reviewColumn}>
      <section hidden={finished} className={styles.cameraPanel} aria-labelledby="preview-heading">
        <header className={styles.panelHeader}>
          <h2 id="preview-heading">{exercise.name}</h2>
          <span className="outline-tag">Live skeleton</span>
        </header>
        <div className={styles.viewport}>
          <video ref={videoRef} autoPlay muted playsInline aria-label="Mirrored live camera preview" className={live ? styles.video : `${styles.video} ${styles.hiddenVideo}`} />
          {live && <LiveOverlay video={videoRef} onFrame={handlePose} onStatus={handleTracking} />}
          {!live && (
            <div className={styles.placeholder}>
              <svg viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="7" y="13" width="26" height="23" rx="6" /><path d="m33 20 9-5v19l-9-5" /><path d="M17 24h6m-3-3v6" /></svg>
              <h3>{labels[state.phase]}</h3>
              <p>{busy ? "Look for the permission prompt near your browser’s address bar." : "Make room for your next move."}</p>
            </div>
          )}
          {live && <span className={styles.previewLabel}>Mirrored preview · not recording</span>}
        </div>
        <div className={styles.controls} hidden={live && exercise.backendHint === "push-up"}>
          <div className={styles.status} role={state.phase === "error" ? "alert" : "status"} aria-atomic="true">
            <p className={state.phase === "error" ? styles.errorTitle : styles.statusTitle}>{labels[state.phase]}</p>
            <p>{state.message}</p>
          </div>
          <div className={styles.actions}>
            <button className="primary-action" onClick={enableCamera} disabled={busy || live}>
              {busy ? "Opening camera…" : live ? "Camera enabled" : state.phase === "error" ? "Try camera again" : "Enable camera"}
            </button>
            {(busy || live) && <button className={styles.secondaryButton} onClick={() => previewRef.current?.stop()}>{busy ? "Cancel" : "Stop camera"}</button>}
          </div>
          <p className={styles.privacyNote}>Skeleton tracking runs in this browser. Starting a push-up set sends joint coordinates for analysis. No video recording or microphone is used.</p>
        </div>
        {exercise.backendHint === "push-up" && (live || liveState.phase !== "idle") && <LiveSessionPanel state={liveState} canStart={live && tracking === "tracking"}
          onStart={() => { if (videoRef.current) counterRef.current?.start(videoRef.current.videoWidth, videoRef.current.videoHeight); }}
          onStop={() => previewRef.current?.stop()}
          onFinish={() => { counterRef.current?.finish(); previewRef.current?.stop(); }} onReset={() => counterRef.current?.reset()} onRetry={() => counterRef.current?.retryFinal()} />}
      </section>
      {finished && liveState.result && <>
        <div className={styles.resultActions}>
          <button className="primary-action" onClick={() => { counterRef.current?.reset(); enableCamera(); }}>Start a new set</button>
          <details><summary>Count look wrong?</summary><p>Save joint positions from this set so we can replay the counter. No video or API key is included. Keep this file private.</p><button className={styles.secondaryButton} onClick={downloadCapture}>Download troubleshooting data</button></details>
        </div>
        <UploadedResults key={liveState.result.sessionId} analysis={liveState.result} canSeek={false} onSeek={() => {}} />
        <SaveSet analysis={liveState.result} logId={liveState.result.sessionId} />
        <AnalysisDetails analysis={liveState.result} />
      </>}
      </div>

      <aside hidden={finished || liveState.phase === "capturing" || liveState.phase === "finishing"} className={styles.guidance} aria-labelledby="framing-heading">
        <section className="panel"><p className="eyebrow">Before you begin</p><h2 id="framing-heading">A little room to move.</h2><p className={styles.setupCue}>{exercise.framingText}</p><details><summary>More setup tips</summary><p className="muted small">Use a stable surface and even lighting. Keep one person in view. The skeleton shows estimated positions, not a form assessment.</p></details><Link className="text-link" href={`/upload?exercise=${exercise.slug}`}>Have a video? Upload your set →</Link></section>
      </aside>
    </div>
  );
}
