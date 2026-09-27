import type { AnalysisResponse } from "@/lib/api/types";
import styles from "./video-upload.module.css";

const seconds = (ms: number) => `${(ms / 1000).toFixed(2)} s`;

/** Kept outside the review card so supporting evidence has one quiet home. */
export function AnalysisDetails({ analysis }: { analysis: AnalysisResponse }) {
  const visual = analysis.visualReview;
  return <details className={styles.analysisDetails}>
    <summary>About this analysis</summary>
    <div className={styles.detailContent}>
      <section>
        <h3>Tracking & measurements</h3>
        {analysis.status === "partial" && <p>Some movement may be uncounted.</p>}
        <p>Angles depend on the camera view. Only sufficiently visible joints are measured. Exercise selection does not confirm detection.</p>
        <p>Full body visible: {analysis.cameraQuality.fullBodyVisible === null ? "Unknown" : analysis.cameraQuality.fullBodyVisible ? "Yes" : "No"}. Camera quality: {analysis.cameraQuality.score ?? "Unavailable"}.</p>
        <p>{analysis.exercise?.id === "incline-dumbbell-bench-press" ? "Counted time runs from bent arms to extension, including pauses. Lowering prepares the next rep." : analysis.exercise?.id === "cable-lateral-raise" ? "Counted time runs from the lowered arm to the raised zone. Angles describe projected hip–shoulder–elbow geometry." : "Counted time includes pauses and confirmation delay. Angles describe this 2D camera view."}</p>
        {analysis.reps.some(rep => rep.measurements.torsoSampleCount != null) && <p>Torso tilt measures the shoulder–hip line against vertical in the video. It doesn’t assess rotation, momentum or form quality.</p>}
        {analysis.reps.some(rep => ["Left", "Right"].some(side => rep.measurements[`median${side}ShoulderHipAnkleAngleDeg`] != null)) && <p>Shoulder–hip–ankle angles cannot distinguish hips dropping from hips rising or assess your spine.</p>}
        <ul>{[...new Set([...analysis.cameraQuality.issues, ...analysis.limitations])].map(item => <li key={item}>{item}</li>)}</ul>
      </section>
      {visual && <section>
        <h3>AI review & supporting moments</h3>
        <p>{visual.status === "complete" ? `Interpretation of ${visual.sampledTimestampsMs.length} sampled video frames, separate from measured counts and angles.` : "No completed AI visual review is attached to this set."}</p>
        {visual.findings.map((finding, index) => <div className={styles.detailFinding} key={index}>
          <p><strong>{finding.phase === "setup" ? "Setup" : finding.phase === "finish" ? "After the set" : "During the set"}</strong> · {finding.kind}</p>
          <p>{finding.observation}</p><p>{finding.cue}</p>
          <p>Evidence: {finding.evidenceTimestampsMs.map(seconds).join(" · ")}</p>
        </div>)}
        <ul>{visual.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul>
      </section>}
      {analysis.issues.length > 0 && <section><h3>Measured changes</h3>{analysis.issues.map(issue => <div className={styles.detailFinding} key={issue.id}><h4>{issue.title}</h4><p>{issue.explanation}</p><p>{seconds(issue.startMs)} · Review priority: {issue.severity} · Confidence: {issue.confidence === null ? "Unknown" : `${Math.round(issue.confidence * 100)}%`}</p></div>)}</section>}
      {!!analysis.movementObservations?.length && <section><h3>Body-line observations</h3>
        <p>A sustained bend between the shoulder, hip and ankle in the image may include setup. This cannot tell hips dropping from hips rising, or assess your spine. Camera view affects the estimate.</p>
        <ul>{analysis.movementObservations.map(item => <li key={item.startMs}>{seconds(item.startMs)}–{seconds(item.endMs)}: {item.side} side, typical angle {item.medianAngleDeg.toFixed(1)}° across {item.sampleCount} samples. Straight is 180°; the provisional review threshold is below {item.thresholdAngleDeg}° for at least half a second.</li>)}</ul>
      </section>}
    </div>
  </details>;
}
