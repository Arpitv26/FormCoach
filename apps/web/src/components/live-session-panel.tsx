import type { LiveState } from "@/lib/live/session";
import styles from "./webcam-setup.module.css";

export function LiveSessionPanel({ state, canStart, onStart, onFinish, onReset, onRetry }: {
  state: LiveState; canStart: boolean; onStart: () => void; onFinish: () => void; onReset: () => void; onRetry: () => void;
}) {
  const active = state.phase === "capturing";
  const finishing = state.phase === "finishing";
  const seconds = Math.floor(state.elapsedMs / 1000);
  const result = state.result;
  return <section className={styles.liveSession} aria-labelledby="live-session-heading">
    <div className="section-heading"><h2 id="live-session-heading">Your live set</h2><span className="outline-tag">Push-ups · up to 2 minutes</span></div>
    <p className="muted small">Start sends joint coordinates to FormCoach for counting. Video and audio are not recorded or uploaded.</p>
    <dl className={styles.liveStats}>
      <div><dt>Counted reps</dt><dd aria-live="polite" aria-atomic="true">{result?.summary.totalReps ?? "—"}</dd></div>
      <div><dt>Set time</dt><dd>{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</dd></div>
      <div><dt>Analysis</dt><dd className={styles.analysisState}>{state.phase === "idle" ? "Not started" : state.phase === "error" ? "Paused" : finishing ? "Finishing…" : state.phase === "finished" ? "Final response" : state.inFlight ? "Updating…" : "Capturing"}</dd></div>
    </dl>
    {result?.provenance.kind && result.provenance.kind !== "measured" && <p className={styles.liveError}>{result.provenance.label} · {result.provenance.kind} response, not verified camera measurements.</p>}
    {active && <p className="muted small">{result?.status === "insufficient_data" ? "Not enough usable movement yet. Keep one elbow visible and pause at the straight-arm top position." : result?.summary.headline ?? "Waiting for the first analysis. A dash means unknown, not zero."}</p>}
    <div className={styles.actions}>
      {state.phase === "idle" && <button className="primary-action" type="button" disabled={!canStart} onClick={onStart}>Start set</button>}
      {active && <button className="primary-action" type="button" onClick={onFinish}>Finish set</button>}
      {state.phase === "error" && <button className="primary-action" type="button" onClick={onRetry}>Retry final analysis</button>}
      {state.phase !== "idle" && <button className={styles.secondaryButton} type="button" onClick={onReset}>{state.phase === "finished" ? "New set" : "Reset set"}</button>}
    </div>
    {state.phase === "idle" && !canStart && <p className="muted small">Enable the camera and wait for skeleton tracking to load, then start your set.</p>}
    <p className="small" role="status">{state.message}</p>
    {state.error && <p className={styles.liveError} role="alert">{state.error} Any displayed count is from the last successful response.</p>}
    <p className="muted small">Counting uses estimated visible joints. Tracking loss can leave a rep incomplete. Form scores are unavailable.</p>
  </section>;
}
