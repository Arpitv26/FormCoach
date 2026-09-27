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
    setPlaybackMessage(`Paused at ${(player.currentTime).toFixed(2)} seconds. Press play to review.`);
  }

  const busy = state.phase === "analyzing";
  const selection = state.selection;
  return (
    <>
      <div className={styles.intro}><p className="eyebrow">{exercise.name} · video analysis</p><h1>Capture your set.<br /><span>Understand each rep.</span></h1><p className="muted">Record a short set on your phone, then review counted reps and measured movement.</p></div>
      <div className={styles.workspace}>
        <div className={styles.reviewColumn}>
        <section className={styles.uploadPanel} aria-labelledby="clip-heading">
          <div className="section-heading"><h2 id="clip-heading">Your exercise clip</h2><span className="outline-tag">01 / UPLOAD</span></div>
          <label className={styles.fileLabel} htmlFor="upload-exercise">Exercise</label>
          <select id="upload-exercise" value={exercise.slug} onChange={(event) => router.push(`/upload?exercise=${event.target.value}`)}>{exercises.filter((item) => item.backendHint).map((item) => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select>
          <label className={styles.fileLabel} htmlFor="video-file">{selection ? "Choose a different video" : "Choose your video"}</label>
          <button ref={chooser} type="button" className={styles.secondary} onClick={() => input.current?.click()}>{selection ? "Replace clip" : "Choose file"}</button>
          <input tabIndex={-1} ref={input} id="video-file" className={styles.fileInput} type="file" accept=".mp4,.mov,.webm,video/mp4,video/quicktime,video/webm" aria-describedby="file-help" onChange={(event) => {
            const file = event.currentTarget.files?.[0];
            if (file) { session.current?.select(file); setPlaybackMessage(""); }
            event.currentTarget.value = "";
          }} />
          <p id="file-help" className="muted small">MP4, MOV or WebM · up to 250 MiB · 2 minutes · 4K maximum</p>
          {selection ? (
            <>
              <div className={styles.fileInfo}><span>{selection.file.name}</span><span>{(selection.file.size / 1024 / 1024).toFixed(1)} MiB</span></div>
              <div className={styles.playerStage}>
              <video key={selection.url} ref={video} className={styles.player} src={selection.url} controls playsInline preload="metadata" aria-label={`Preview of ${selection.file.name}`} onLoadedMetadata={(event) => {
                const player = event.currentTarget;
                session.current?.metadata(selection.url, player.duration, player.videoWidth, player.videoHeight);
              }} onError={() => session.current?.previewFailed(selection.url)} />
              <PlaybackOverlay video={video} track={state.poseTrack} enabled={showSkeleton && state.preview === "ready" && state.result?.provenance.kind === "measured"} />
              </div>
              {state.poseTrack && state.preview === "ready" && <label className={styles.overlayToggle}><input type="checkbox" checked={showSkeleton} onChange={(event) => setShowSkeleton(event.target.checked)} /> Show skeleton · estimated visible joints</label>}
              {state.preview === "loading" && <p className="muted small" role="status">Loading video preview… You can still submit it if your browser cannot read the metadata.</p>}
              {state.preview === "unplayable" && <p className={styles.notice}>This browser cannot preview this codec. You can still try analysis, but timestamp playback is unavailable. For playback, export an H.264 MP4 and analyze that same export.</p>}
              <p className="small" role="status">{playbackMessage}</p>
            </>
          ) : <div className={styles.emptyPreview}><span aria-hidden="true">↥</span><h3>A clearer view of your movement.</h3><p>Choose a clip to preview it here.<br />It stays local until you select Analyze video.</p></div>}
          {state.validationError && <p className={styles.error} role="alert">{state.validationError}</p>}
          <div className={styles.actions}>
            <button className="primary-action" type="button" disabled={!selection || !!state.validationError || busy} onClick={() => { setPlaybackMessage(""); void session.current?.submit(); }}>{busy ? "Analyzing video…" : state.phase === "error" ? "Try analysis again" : "Analyze video"}<span aria-hidden="true">↗</span></button>
            {busy ? <button className={styles.secondary} type="button" onClick={() => session.current?.cancel()}>Stop waiting</button> : selection && <button className={styles.secondary} type="button" onClick={() => { session.current?.select(null); setPlaybackMessage(""); chooser.current?.focus(); }}>Remove clip</button>}
          </div>
          <div role="status" aria-live="polite">
            {busy && <p className={styles.notice}>Analyzing your uploaded video. This can take a few minutes. Keep this page open; no need to submit again.</p>}
            {state.message && <p className={state.phase === "error" ? styles.error : styles.notice}>{state.message}</p>}
            {state.phase === "complete" && <p className={styles.notice}>Response received. Your results are below.</p>}
          </div>
          <p className="muted small">Analyze sends this video to the FormCoach backend. When AI visual review is enabled, timestamped frames are also sent to OpenAI for technique feedback.</p>
        </section>
        {state.result && <UploadedResults analysis={state.result} canSeek={state.preview === "ready"} onSeek={seek} />}
        </div>
        <aside className={styles.guide} aria-labelledby="guide-heading"><p className="eyebrow">A little setup goes a long way</p><h2 id="guide-heading">Make every rep visible.</h2><ol><li><strong>{exercise.framingTitle}</strong><span>{exercise.framingText}</span></li><li><strong>Keep the phone still.</strong><span>Use a stable surface and good lighting. Avoid people crossing in front of you.</span></li><li><strong>Keep it short.</strong><span>A clear clip of 3–6 reps is a good place to start.</span></li></ol><div className={styles.guideNote}><span aria-hidden="true">✦</span><p>Counted reps and timestamps first. Scores stay unavailable when the backend cannot measure them.</p></div></aside>
      </div>
    </>
  );
}
