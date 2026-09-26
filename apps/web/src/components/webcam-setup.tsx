"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { exercises, type ExerciseOption } from "@/lib/exercises";
import { CameraPreview, initialCameraState, type CameraState } from "@/lib/camera/preview";
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

  useEffect(() => {
    if (!videoRef.current) return;
    const preview = new CameraPreview(videoRef.current, () => navigator.mediaDevices.getUserMedia({
      audio: false,
      video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
    }), setState);
    previewRef.current = preview;
    const onPageHide = () => preview.stop();
    window.addEventListener("pagehide", onPageHide);
    return () => {
      window.removeEventListener("pagehide", onPageHide);
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
    previewRef.current?.stop();
    router.push(`/camera?exercise=${slug}`);
  }

  return (
    <div className={styles.layout}>
      <section className={styles.cameraPanel} aria-labelledby="preview-heading">
        <header className={styles.panelHeader}>
          <h2 id="preview-heading">{exercise.name}</h2>
          <span className="outline-tag">Preview only</span>
        </header>
        <div className={styles.viewport}>
          <video ref={videoRef} autoPlay muted playsInline aria-label="Mirrored live camera preview" className={live ? styles.video : `${styles.video} ${styles.hiddenVideo}`} />
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
          <p className={styles.privacyNote}>Video stays in this browser preview. This screen does not record, upload, or use your microphone.</p>
        </div>
      </section>

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
          <h2 id="next-heading">Preview comes first.</h2>
          <p>{exercise.group === "live" ? "For push-up analysis, upload a recorded video. Live tracking is not connected yet." : "Analysis for this gym exercise is planned. Its supported camera angle still needs to be verified."} Camera access alone does not check your framing, count reps, or produce scores.</p>
          {exercise.group === "live" && <Link href="/upload">Analyze a push-up video →</Link>}
          <Link href="/" className={styles.demoLink}>Choose another exercise <span aria-hidden="true">↗</span></Link>
        </section>
      </aside>
    </div>
  );
}
