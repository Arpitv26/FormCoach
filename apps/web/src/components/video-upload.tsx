"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { exercises, type ExerciseOption } from "@/lib/exercises";
import { api } from "@/lib/api/client";
import { emptyUploadState, UploadSession } from "@/lib/video/upload-session";
import { PlaybackOverlay } from "./playback-overlay";
import { UploadedResults } from "./uploaded-results";
import styles from "./video-upload.module.css";

export function VideoUpload({ exercise }: { exercise: Extract<ExerciseOption, { backendHint: string }> }) {
  const router = useRouter();
  const [state, setState] = useState(emptyUploadState);
  const session = useRef<UploadSession | null>(null);
  const video = useRef<HTMLVideoElement | null>(null);
  const chooser = useRef<HTMLButtonElement | null>(null);
  const input = useRef<HTMLInputElement | null>(null);
  const [showSkeleton, setShowSkeleton] = useState(true);
  const [playbackMessage, setPlaybackMessage] = useState("");
  useEffect(() => {
    const current = new UploadSession((file, signal) => api.analyzeVideoWithPose(file, exercise.backendHint, signal), setState);
    session.current = current;
    return () => { current.dispose(); session.current = null; };
  }, [exercise.backendHint]);

  function seek(timestampMs: number) {
    const player = video.current;
    if (!player || state.preview !== "ready") return;
    player.pause();
    const target = Math.max(0, timestampMs / 1000);
    player.currentTime = Number.isFinite(player.duration) ? Math.min(target, player.duration) : target;
    player.focus({ preventScroll: true });
    player.scrollIntoView({ behavior: "instant", block: "center" });
    setPlaybackMessage(`Paused at ${player.currentTime.toFixed(2)} seconds. Press play to review.`);
  }

  const busy = state.phase === "analyzing";
  const selection = state.selection;
  return <>
    <div className="page-intro"><p className="eyebrow">Upload workspace</p><h1>{state.result ? exercise.name : "Bring your set into focus."}</h1><p className="muted">{state.result ? "Watch your movement. Explore what stood out." : "Choose your exercise and a short video. We’ll take it from there."}</p></div>
    <ol className={styles.steps} aria-label="Upload progress">{["Choose", "Analyze", "Review"].map((label, index) => <li key={label} aria-current={(state.result ? 2 : busy ? 1 : 0) === index ? "step" : undefined}><span>{index + 1}</span>{label}</li>)}</ol>
    <div className={state.result ? styles.reviewWorkspace : styles.workspace}>
      <section className={styles.uploadPanel} aria-labelledby="clip-heading">
        <div className="section-heading"><h2 id="clip-heading">{state.result ? "Your video" : "Choose a video"}</h2>{selection && <button ref={chooser} className={styles.secondary} onClick={() => input.current?.click()}>Replace clip</button>}</div>
        <div className={styles.exerciseSelect}><label className={styles.fileLabel} htmlFor="upload-exercise">Exercise</label><select id="upload-exercise" value={exercise.slug} onChange={(event) => router.push(`/upload?exercise=${event.target.value}`)}>{exercises.map(item => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></div>
        <input tabIndex={-1} ref={input} id="video-file" className={styles.fileInput} type="file" accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm" aria-label="Choose your video" aria-describedby="file-help" onChange={event => { const file = event.currentTarget.files?.[0]; if (file) { session.current?.select(file); setPlaybackMessage(""); } event.currentTarget.value = ""; }} />
        {selection ? <>
          <div className={styles.fileInfo}><span>{selection.file.name}</span><span>{(selection.file.size / 1024 / 1024).toFixed(1)} MiB</span></div>
          <div className={styles.playerStage}><video key={selection.url} ref={video} className={styles.player} src={selection.url} controls playsInline preload="metadata" aria-label={`Preview of ${selection.file.name}`} onLoadedMetadata={event => { const player = event.currentTarget; session.current?.metadata(selection.url, player.duration, player.videoWidth, player.videoHeight); }} onError={() => session.current?.previewFailed(selection.url)} /><PlaybackOverlay video={video} track={state.poseTrack} enabled={showSkeleton && state.preview === "ready" && state.result?.provenance.kind === "measured"} /></div>
          {state.poseTrack && state.preview === "ready" && <label className={styles.overlayToggle}><input type="checkbox" checked={showSkeleton} onChange={event => setShowSkeleton(event.target.checked)} />Show skeleton <span className="muted">· estimated joints</span></label>}
          {state.preview === "loading" && <p className="muted small" role="status">Loading preview… Analysis can still run if your browser can’t read this clip.</p>}
          {state.preview === "unplayable" && <p className={styles.notice}>This browser can’t preview this codec. You can still analyze it. For playback, export an H.264 MP4 and analyze that same export.</p>}
          <p className="small" role="status">{playbackMessage}</p>
        </> : <button ref={chooser} type="button" className={styles.emptyPreview} onClick={() => input.current?.click()}><span aria-hidden="true">↥</span><strong>Choose your video</strong><span>A short set. A steady camera.<br />A clearer view of your movement.</span></button>}
        <p id="file-help" className="muted small">MP4, MOV or WebM · 250 MiB · 2 minutes · up to 4K</p>
        {state.validationError && <p className={styles.error} role="alert">{state.validationError}</p>}
        <div className={styles.actions}><button className={state.result ? styles.secondary : "primary-action"} disabled={!selection || !!state.validationError || busy} onClick={() => { setPlaybackMessage(""); void session.current?.submit(); }}>{busy ? "Analyzing…" : state.phase === "error" ? "Try analysis again" : state.result ? "Reanalyze video" : "Analyze video"}{!busy && <span aria-hidden="true"> ↗</span>}</button>{busy ? <button className={styles.secondary} onClick={() => session.current?.cancel()}>Stop waiting</button> : selection && <button className={styles.secondary} onClick={() => { session.current?.select(null); setPlaybackMessage(""); requestAnimationFrame(() => chooser.current?.focus()); }}>Remove clip</button>}</div>
        <div role="status" aria-live="polite">{busy && <p className={styles.notice}>Reviewing your video. This may take a few minutes. Keep this page open.</p>}{state.message && <p className={state.phase === "error" ? styles.error : styles.notice}>{state.message}</p>}{state.result && <p className="sr-only">Analysis received. Your review is ready.</p>}</div>
        {!state.result && <p className="muted small">Analyze sends your video to FormCoach. When AI visual review is enabled, sampled frames are also sent to OpenAI.</p>}
        <details className={styles.evidence}><summary>Filming tips</summary><p><strong>{exercise.framingTitle}.</strong> {exercise.framingText}</p><p className="muted small">Keep the camera still, use even lighting, and avoid people crossing in front of you.</p></details>
      </section>
      {state.result ? <UploadedResults key={state.result.sessionId} analysis={state.result} canSeek={state.preview === "ready"} onSeek={seek} /> : <aside className={styles.guide}><span className={styles.guideNumber}>01 — 03</span><h2>A little setup.<br />A useful perspective.</h2><ol><li><strong>Choose your exercise</strong><span>One workspace for your push-ups and supported gym sets.</span></li><li><strong>Analyze your clip</strong><span>Review counted reps and the movement we can observe.</span></li><li><strong>Make it yours</strong><span>Explore your reps, ask your coach, and save the set to your log.</span></li></ol></aside>}
    </div>
  </>;
}
