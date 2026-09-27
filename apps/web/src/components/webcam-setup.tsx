"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { exercises, type ExerciseOption } from "@/lib/exercises";
import { CameraPreview, initialCameraState, type CameraState } from "@/lib/camera/preview";
import { api } from "@/lib/api/client";
import type { PoseFrame } from "@/lib/api/types";
import type { TrackingStatus } from "@/lib/pose/live";
import { LiveSession, initialLiveState } from "@/lib/live/session";
import { LiveSessionPanel } from "./live-session-panel";
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
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const previewRef = useRef<CameraPreview | null>(null);
  const [state, setState] = useState(initialCameraState);
  const [liveState, setLiveState] = useState(initialLiveState);
  const [tracking, setTracking] = useState<TrackingStatus>("loading");
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

  function changeExercise(slug: string) {
    counterRef.current?.reset();
    previewRef.current?.stop();
    router.push(`/camera?exercise=${slug}`);
  }

  return (
    <div className={styles.layout}>
      <div className={styles.reviewColumn}>
      <section className={styles.cameraPanel} aria-labelledby="preview-heading">
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
        <div className={styles.controls}>
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
        {exercise.backendHint === "push-up" && <LiveSessionPanel state={liveState} canStart={live && tracking !== "loading" && tracking !== "error"}
          onStart={() => { if (videoRef.current) counterRef.current?.start(videoRef.current.videoWidth, videoRef.current.videoHeight); }}
          onFinish={() => counterRef.current?.finish()} onReset={() => counterRef.current?.reset()} onRetry={() => counterRef.current?.retryFinal()} />}
      </section>
      {liveState.phase === "finished" && liveState.result && <UploadedResults analysis={liveState.result} canSeek={false} onSeek={() => {}} />}
      </div>

      <aside className={styles.guidance} aria-labelledby="framing-heading">
        <section className={`panel ${styles.selection}`} aria-labelledby="exercise-heading">
          <h2 id="exercise-heading">Your session</h2>
          <label htmlFor="exercise">Selected exercise</label>
          <select id="exercise" value={exercise.slug} onChange={(event) => changeExercise(event.target.value)}>
            <optgroup label="Live demo"><option value="push-up">Push-ups</option></optgroup>
            <optgroup label="Gym exercises">{exercises.filter((option) => option.group === "gym").map((option) => <option key={option.slug} value={option.slug}>{option.name}</option>)}</optgroup>
          </select>
          <p>Changing exercises stops your camera. This is your selection, not an automatic detection.</p>
        </section>
        <section className="panel">
          <p className="eyebrow">Set yourself up</p>
          <h2 id="framing-heading">A little room to move.</h2>
          <ol className={styles.tips}>
            <li><span aria-hidden="true">01</span><div><h3>{exercise.framingTitle}</h3><p>{exercise.framingText}</p></div></li>
            <li><span aria-hidden="true">02</span><div><h3>Find steady ground</h3><p>Place your device on a stable surface. Keep the camera still and the floor clear.</p></div></li>
            <li><span aria-hidden="true">03</span><div><h3>Face the light</h3><p>Use even lighting so your body is easy to see. Avoid a bright window behind you.</p></div></li>
          </ol>
        </section>
        <section className={`${styles.nextStep} panel`} aria-labelledby="next-heading">
          <p className="eyebrow">One step at a time</p>
          <h2 id="next-heading">See how you move.</h2>
          <p>{exercise.group === "live" ? "Start a push-up set to count completed reps with the connected backend. For playback and timestamp review, upload a recorded video." : "Analysis for this gym exercise is planned. Its supported camera angle still needs to be verified."} The skeleton shows estimated joint positions, not an assessment of form. Camera angle and full-body visibility are not automatically verified.</p>
          {exercise.group === "live" && <Link href="/upload">Analyze a push-up video →</Link>}
          <Link href="/" className={styles.demoLink}>Choose another exercise <span aria-hidden="true">↗</span></Link>
        </section>
      </aside>
    </div>
  );
}
