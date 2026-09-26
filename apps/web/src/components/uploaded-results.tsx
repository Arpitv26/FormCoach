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
  const measured = analysis.provenance.kind === "measured";
  const seekEnabled = canSeek && measured && analysis.source.type === "upload";
  return (
    <section className={styles.results} aria-labelledby="results-heading">
      <div className="section-heading"><div><p className="eyebrow">Your video, reviewed</p><h2 id="results-heading">{statuses[analysis.status]}</h2></div><span className="outline-tag">{analysis.provenance.label}</span></div>
      {!measured && <p className={styles.notice}>This response is {analysis.provenance.kind} data, not measurements from your clip. Timestamp playback is disabled.</p>}
      <p>{analysis.summary.headline}</p>
      <dl className={styles.summary}>
        <div><dt>Counted reps</dt><dd>{analysis.summary.totalReps ?? "Unavailable"}</dd></div>
        <div><dt>Video duration</dt><dd>{seconds(analysis.source.durationMs)}</dd></div>
        <div><dt>Form score</dt><dd>{analysis.summary.overallScore == null ? "Unavailable" : `${analysis.summary.overallScore}/100`}</dd></div>
      </dl>
      {analysis.summary.overallScore == null && <p className="muted small">No form score was returned. Elbow measurements describe observed movement; they are not a quality rating.</p>}
      {analysis.status === "partial" && <p className={styles.notice}>This is the final response for this upload. Some evidence or a rep may be incomplete; check the limitations below.</p>}
      {analysis.reps.length === 0 && <p className={styles.notice}>No complete rep details were returned. Try a short side-view clip with your full body visible.</p>}
      {analysis.reps.map((rep) => (
        <article className={styles.rep} key={rep.repNumber}>
          <div className={styles.repHeading}><h3>Rep {rep.repNumber}</h3><button type="button" disabled={!seekEnabled} onClick={() => onSeek(rep.startMs)}>View at {seconds(rep.startMs)} <span aria-hidden="true">↗</span></button></div>
          <p className="muted small">{seconds(rep.startMs)} – {seconds(rep.endMs)} · Counted duration: {seconds(rep.measurements.durationMs)}</p>
          <dl className={styles.measurements}>
            {(["Left", "Right"] as const).map((side) => (
              <div key={side}><dt>{side} elbow · min / max</dt><dd>{angle(rep.measurements[`minSmoothed${side}ElbowAngleDeg`])} / {angle(rep.measurements[`maxSmoothed${side}ElbowAngleDeg`])}</dd><dt>Observed angle range</dt><dd>{angle(rep.measurements[`smoothed${side}ElbowExcursionDeg`])}</dd></div>
            ))}
            <div><dt>Time to minimum angle</dt><dd>{seconds(rep.measurements.timeToMinElbowAngleMs)}</dd><dt>Time after minimum angle</dt><dd>{seconds(rep.measurements.timeFromMinElbowAngleMs)}</dd></div>
          </dl>
          <div className={styles.moments}>{rep.keyMoments.map((moment, index) => <button type="button" key={`${moment.type}-${index}`} disabled={!seekEnabled} onClick={() => onSeek(moment.timestampMs)}>{moment.label} · {seconds(moment.timestampMs)}</button>)}</div>
          {rep.issues.map((issue) => <p key={issue.id}>{issue.title}: {issue.shortCue}</p>)}
        </article>
      ))}
      <p className="muted small">Angles are smoothed 2D observations and depend on the camera view. Timing can include pauses and rep confirmation; it does not identify lifting or lowering phases.</p>
      <div className={styles.evidence}>
        <h3>Visibility &amp; limitations</h3>
        <p>Full body visible: {analysis.cameraQuality.fullBodyVisible === null ? "Unknown" : analysis.cameraQuality.fullBodyVisible ? "Yes" : "No"}. Camera quality: {analysis.cameraQuality.score ?? "Unavailable"}.</p>
        <p className="muted small">Push-ups are your selected exercise. Selection alone does not confirm exercise detection.</p>
        {[...analysis.cameraQuality.issues, ...analysis.limitations].length > 0 && <ul>{[...analysis.cameraQuality.issues, ...analysis.limitations].map((item, index) => <li key={index}>{item}</li>)}</ul>}
        {analysis.issues.map((issue) => <p key={issue.id}>{issue.title}: {issue.explanation}</p>)}
      </div>
    </section>
  );
}
