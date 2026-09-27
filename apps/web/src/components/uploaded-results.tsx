"use client";

import { useId } from "react";
import { CoachPanel } from "./coach-panel";
import { RepOverview } from "./rep-overview";
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
  complete: "Analysis complete", partial: "Analysis complete · partial evidence",
  insufficient_data: "Not enough visible movement", not_implemented: "Analysis unavailable",
};

export function UploadedResults({ analysis, canSeek, onSeek }: {
  analysis: AnalysisResponse; canSeek: boolean; onSeek: (timestampMs: number) => void;
}) {
  const id = useId();
  const live = analysis.source.type === "live";
  const measured = analysis.provenance.kind === "measured";
  const seekEnabled = canSeek && measured && analysis.source.type === "upload";
  return (
    <section className={styles.results} aria-labelledby={`${id}-heading`}>
      <div className="section-heading"><div><p className="eyebrow">{live ? "Your live set, reviewed" : "Your video, reviewed"}</p><h2 id={`${id}-heading`} data-results-heading>{statuses[analysis.status]}</h2></div><span className="outline-tag">{analysis.provenance.label}</span></div>
      {!measured && <p className={styles.notice}>This response is {analysis.provenance.kind} data, not verified measurements from your movement. Timestamp playback is disabled.</p>}
      <p>{analysis.summary.headline}</p>
      <dl className={styles.summary}>
        <div><dt>Counted reps</dt><dd>{analysis.summary.totalReps ?? "Unavailable"}</dd></div>
        <div><dt>{live ? "Sample coverage" : "Video duration"}</dt><dd>{seconds(analysis.source.durationMs)}</dd></div>
        {analysis.summary.overallScore != null && <div><dt>Form score</dt><dd>{analysis.summary.overallScore}/100</dd></div>}
      </dl>
      {analysis.summary.overallScore == null && <p className="muted small">No form score was returned. Elbow measurements describe observed movement; they are not a quality rating.</p>}
      {analysis.status === "partial" && <p className={styles.notice}>This is the final response for this set. Some evidence or a rep may be incomplete; check the limitations below.</p>}
      {analysis.reps.length === 0 && <p className={styles.notice}>No complete rep details were returned. Try a short side-view set with your full body visible.</p>}
      <RepOverview reps={analysis.reps} onSeek={seekEnabled ? onSeek : undefined} idPrefix={id} />
      <section className={styles.changes} aria-labelledby={`${id}-changes`}>
        <div className="section-heading"><h3 id={`${id}-changes`}>Changes to review</h3><span className="outline-tag">{analysis.issues.length} reported</span></div>
        {analysis.issues.length === 0 ? <p className="muted small">No changes were flagged. Comparisons need two preceding reps and usable tracking; eligibility depends on the measurement. No flags does not establish good form.</p> : analysis.issues.map((issue) => (
          <article key={issue.id} className={styles.changeCard}>
            <h4>{issue.title}</h4><p>{issue.explanation}</p><p className="small">{issue.shortCue}</p>
            <p className="muted small">Review priority: {issue.severity} · Confidence: {issue.confidence == null ? "Unknown" : `${Math.round(issue.confidence * 100)}%`}</p>
            {seekEnabled && <button type="button" className={styles.secondary} onClick={() => onSeek(issue.startMs)}>Review at {seconds(issue.startMs)} ↗</button>}
          </article>
        ))}
      </section>
      {analysis.reps.map((rep) => (
        <article className={styles.rep} key={rep.repNumber} id={`${id}-rep-${rep.repNumber}`}>
          <div className={styles.repHeading}><h3>Rep {rep.repNumber}</h3>{!live && <button type="button" disabled={!seekEnabled} onClick={() => onSeek(rep.startMs)}>View at {seconds(rep.startMs)} <span aria-hidden="true">↗</span></button>}</div>
          <p className="muted small">{seconds(rep.startMs)} – {seconds(rep.endMs)} · Counted duration: {seconds(rep.measurements.durationMs)}</p>
          <dl className={styles.measurements}>
            {(["Left", "Right"] as const).filter((side) => rep.measurements[`minSmoothed${side}ElbowAngleDeg`] != null).map((side) => (
              <div key={side}><dt>{side} elbow · min / max</dt><dd>{angle(rep.measurements[`minSmoothed${side}ElbowAngleDeg`])} / {angle(rep.measurements[`maxSmoothed${side}ElbowAngleDeg`])}</dd><dt>Observed angle range</dt><dd>{angle(rep.measurements[`smoothed${side}ElbowExcursionDeg`])}</dd></div>
            ))}
            <div><dt>Time to minimum angle</dt><dd>{seconds(rep.measurements.timeToMinElbowAngleMs)}</dd><dt>Time after minimum angle</dt><dd>{seconds(rep.measurements.timeFromMinElbowAngleMs)}</dd></div>
          </dl>
          {referenceComparisons(rep).map((item) => <p key={item.label} className={styles.comparison}><strong>{item.label}: {item.current}</strong><span>Reference median ({item.reference}): {item.baseline} · Change: {item.change}</span></p>)}
          {!live && <div className={styles.moments}>{rep.keyMoments.map((moment, index) => <button type="button" key={`${moment.type}-${index}`} disabled={!seekEnabled} onClick={() => onSeek(moment.timestampMs)}>{moment.label} · {seconds(moment.timestampMs)}</button>)}</div>}

        </article>
      ))}
      <p className="muted small">Angles are smoothed 2D observations and depend on the camera view. Timing can include pauses and rep confirmation; it does not identify lifting or lowering phases.</p>
      <p className="muted small">Only visible, sufficiently tracked joints are measured. Full-body visibility and camera angle are not verified.</p>
      <details className={styles.evidence}>
        <summary>How these measurements work · visibility &amp; limitations</summary>
        <p>Full body visible: {analysis.cameraQuality.fullBodyVisible === null ? "Unknown" : analysis.cameraQuality.fullBodyVisible ? "Yes" : "No"}. Camera quality: {analysis.cameraQuality.score ?? "Unavailable"}.</p>
        <p className="muted small">Push-ups are your selected exercise. Selection alone does not confirm exercise detection.</p>
        {[...analysis.cameraQuality.issues, ...analysis.limitations].length > 0 && <ul>{[...analysis.cameraQuality.issues, ...analysis.limitations].map((item, index) => <li key={index}>{item}</li>)}</ul>}

      </details>
      <CoachPanel key={analysis.sessionId} analysis={analysis} onSeek={seekEnabled ? onSeek : undefined} />
    </section>
  );
}
