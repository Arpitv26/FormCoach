"use client";

import { useId, useRef } from "react";
import { CoachPanel } from "./coach-panel";
import { RepOverview } from "./rep-overview";
import { MovementObservations } from "./movement-observations";
import { referenceComparisons } from "@/lib/results/measurements";
import type { AnalysisResponse } from "@/lib/api/types";
import styles from "./video-upload.module.css";

function seconds(value: number | null | undefined) {
  return value == null ? "Unavailable" : `${(value / 1000).toFixed(2)} s`;
}
function angle(value: number | null | undefined) {
  return value == null ? "Unavailable" : `${value.toFixed(1)}°`;
}
const statuses = {
  complete: "Analysis complete", partial: "Some movement may be missing",
  insufficient_data: "Not enough visible movement", not_implemented: "Analysis unavailable",
};

export function UploadedResults({ analysis, canSeek, onSeek }: {
  analysis: AnalysisResponse; canSeek: boolean; onSeek: (timestampMs: number) => void;
}) {
  const id = useId();
  const repDetails = useRef<HTMLDetailsElement>(null);
  const live = analysis.source.type === "live";
  const measured = analysis.provenance.kind === "measured";
  const seekEnabled = canSeek && measured && analysis.source.type === "upload";
  const heading = analysis.reps.length === 0 && analysis.movementObservations?.length ? "Movement reviewed" : statuses[analysis.status];
  return (
    <section className={styles.results} aria-labelledby={`${id}-heading`}>
      <div className="section-heading"><div><p className="eyebrow">{live ? "Your live set, reviewed" : "Your video, reviewed"}</p><h2 id={`${id}-heading`} data-results-heading>{heading}</h2></div></div>
      {!measured && <p className={styles.notice}>This response is {analysis.provenance.kind} data, not verified measurements from your movement. Timestamp playback is disabled.</p>}
      <p>{analysis.summary.totalReps == null ? "We couldn’t reliably count this set." : `We detected ${analysis.summary.totalReps} completed reps.`}</p>
      {analysis.exercise?.id === "incline-dumbbell-bench-press" && <p className="muted small">Rep times run from bent arms to extension, including pauses. Lowering prepares the next rep.</p>}
      {analysis.exercise?.id === "cable-lateral-raise" && <p className="muted small">Rep times run from a lowered arm to the raised zone. The measured angle is projected hip–shoulder–elbow geometry.</p>}
      <dl className={styles.summary}>
        <div><dt>Counted reps</dt><dd>{analysis.summary.totalReps ?? "Unavailable"}</dd></div>
        <div><dt>{live ? "Set length" : "Video duration"}</dt><dd>{seconds(analysis.source.durationMs)}</dd></div>
        {analysis.summary.overallScore != null && <div><dt>Form score</dt><dd>{analysis.summary.overallScore}/100</dd></div>}
      </dl>
      {analysis.status === "partial" && analysis.reps.length > 0 && <p className={styles.notice}>Some movement could not be fully counted. The detected count may be lower than the number you performed.</p>}
      {analysis.reps.length === 0 && <p className={styles.notice}>{analysis.summary.totalReps === 0 ? "No complete movements met the counting rules. That doesn’t mean no movement happened." : "There wasn’t enough information to count completed reps reliably."}</p>}
      <MovementObservations observations={analysis.movementObservations} onSeek={seekEnabled ? onSeek : undefined} />
      <CoachPanel key={analysis.sessionId} analysis={analysis} onSeek={seekEnabled ? onSeek : undefined} />
      <RepOverview reps={analysis.reps} onSeek={seekEnabled ? onSeek : undefined} idPrefix={id} onShowDetails={() => { if (repDetails.current) repDetails.current.open = true; }} />
      {(analysis.reps.length > 0 || analysis.issues.length > 0) && <section className={styles.changes} aria-labelledby={`${id}-changes`}>
        <div className="section-heading"><h3 id={`${id}-changes`}>Rep-to-rep changes</h3><span className="outline-tag">{analysis.issues.length} reported</span></div>
        {analysis.issues.length === 0 ? <p className="muted small">{analysis.exercise?.id !== "push-up" ? "Automatic change flags aren’t available for this exercise yet. Explore the rep times and angles below." : analysis.reps.length < 3 ? "We need at least three well-tracked reps to compare changes." : "No substantial changes were flagged in the reps we could compare."} This isn’t a form rating.</p> : analysis.issues.map((issue) => (
          <article key={issue.id} className={styles.changeCard}>
            <h4>{issue.title}</h4><p className="small">{issue.shortCue}</p>
            {seekEnabled && <button type="button" className={styles.secondary} onClick={() => onSeek(issue.startMs)}>Review at {seconds(issue.startMs)} ↗</button>}
            <details><summary>Why this was flagged</summary><p className="small">{issue.explanation}</p><p className="muted small">Review priority: {issue.severity} · Confidence: {issue.confidence == null ? "Unknown" : `${Math.round(issue.confidence * 100)}%`}</p></details>
          </article>
        ))}
      </section>}
      {analysis.reps.length > 0 && <details ref={repDetails} className={styles.evidence}><summary>Explore each rep’s measurements</summary>
      {analysis.reps.map((rep) => (
        <article className={styles.rep} key={rep.repNumber} id={`${id}-rep-${rep.repNumber}`}>
          <div className={styles.repHeading}><h3>Rep {rep.repNumber}</h3>{!live && <button type="button" disabled={!seekEnabled} onClick={() => onSeek(rep.startMs)}>View at {seconds(rep.startMs)} <span aria-hidden="true">↗</span></button>}</div>
          <p className="muted small">{seconds(rep.startMs)} – {seconds(rep.endMs)} · Counted duration: {seconds(rep.measurements.durationMs)}</p>
          <dl className={styles.measurements}>
            {(["Elbow", "Shoulder"] as const).map((joint) => (["Left", "Right"] as const).filter((side) => rep.measurements[`minSmoothed${side}${joint}AngleDeg`] != null).map((side) => (
              <div key={`${side}-${joint}`}><dt>{side} {joint.toLowerCase()} · min / max</dt><dd>{angle(rep.measurements[`minSmoothed${side}${joint}AngleDeg`])} / {angle(rep.measurements[`maxSmoothed${side}${joint}AngleDeg`])}</dd><dt>Observed angle range</dt><dd>{angle(rep.measurements[`smoothed${side}${joint}ExcursionDeg`])}</dd></div>
            )))}
            <div><dt>Time to minimum angle</dt><dd>{seconds(rep.measurements.timeToMinElbowAngleMs ?? rep.measurements.timeToMinShoulderAngleMs)}</dd><dt>Time after minimum angle</dt><dd>{seconds(rep.measurements.timeFromMinElbowAngleMs ?? rep.measurements.timeFromMinShoulderAngleMs)}</dd></div>
            {(["Left", "Right"] as const).filter((side) => `min${side}TorsoTiltDeg` in rep.measurements).map((side) => (
              <div key={`${side}-torso`}><dt>Torso tilt · min / max</dt><dd>{angle(rep.measurements[`min${side}TorsoTiltDeg`])} / {angle(rep.measurements[`max${side}TorsoTiltDeg`])}</dd><dt>Observed torso angle range</dt><dd>{angle(rep.measurements[`${side.toLowerCase()}TorsoTiltRangeDeg`])}</dd></div>
            ))}
          </dl>
          {rep.measurements.torsoSampleCount != null && <p className="muted small">Torso tilt measures the shoulder–hip line against vertical in the video. It doesn’t assess rotation, momentum or form quality.</p>}
          {referenceComparisons(rep).map((item) => <p key={item.label} className={styles.comparison}><strong>{item.label}: {item.current}</strong><span>Reference median ({item.reference}): {item.baseline} · Change: {item.change}</span></p>)}
          {!live && <div className={styles.moments}>{rep.keyMoments.map((moment, index) => <button type="button" key={`${moment.type}-${index}`} disabled={!seekEnabled} onClick={() => onSeek(moment.timestampMs)}>{moment.label} · {seconds(moment.timestampMs)}</button>)}</div>}

        </article>
      ))}
      </details>}
      <details className={styles.evidence}><summary>About these measurements</summary>
      <p className="muted small">Angles are smoothed 2D observations and depend on the camera view. Timing can include pauses and rep confirmation; it does not identify lifting or lowering phases.</p>
      <p className="muted small">Only visible, sufficiently tracked joints are measured. Full-body visibility and camera angle are not verified.</p>

        <p>Full body visible: {analysis.cameraQuality.fullBodyVisible === null ? "Unknown" : analysis.cameraQuality.fullBodyVisible ? "Yes" : "No"}. Camera quality: {analysis.cameraQuality.score ?? "Unavailable"}.</p>
        <p className="muted small">{analysis.exercise?.name ?? "This"} is your selected exercise. Selection alone does not confirm exercise detection.</p>
        {[...analysis.cameraQuality.issues, ...analysis.limitations].length > 0 && <ul>{[...analysis.cameraQuality.issues, ...analysis.limitations].map((item, index) => <li key={index}>{item}</li>)}</ul>}

      </details>
    </section>
  );
}
