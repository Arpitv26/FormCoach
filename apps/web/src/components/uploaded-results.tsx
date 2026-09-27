"use client";

import { useId, useState, type KeyboardEvent } from "react";
import { CoachPanel } from "./coach-panel";
import { RepOverview } from "./rep-overview";
import { MovementObservations } from "./movement-observations";
import { useReviewMotion } from "@/lib/results/use-review-motion";
import { referenceComparisons } from "@/lib/results/measurements";
import type { AnalysisResponse } from "@/lib/api/types";
import styles from "./video-upload.module.css";

function seconds(value: number | null | undefined) { return value == null ? "Unavailable" : `${(value / 1000).toFixed(2)} s`; }
function angle(value: number | null | undefined) { return value == null ? "Unavailable" : `${value.toFixed(1)}°`; }
const tabs = ["Overview", "Reps", "Coach"] as const;
type ReviewTab = (typeof tabs)[number];

export function UploadedResults({ analysis, canSeek, onSeek }: {
  analysis: AnalysisResponse; canSeek: boolean; onSeek: (timestampMs: number) => void;
}) {
  const id = useId();
  const root = useReviewMotion(analysis.sessionId);
  const [tab, setTab] = useState<ReviewTab>("Overview");
  const live = analysis.source.type === "live";
  const measured = analysis.provenance.kind === "measured";
  const seekEnabled = canSeek && measured && !live;
  const visual = analysis.visualReview;
  const findings = visual?.findings ?? [];
  const highlights = findings.filter(finding => !finding.phase || finding.phase === "exercise").slice(0, 2);
  const visibleIssues = analysis.issues.slice(0, Math.max(0, 2 - highlights.length));
  const showMovement = highlights.length + visibleIssues.length < 2;
  function changeTab(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    let next = index;
    if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
    else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
    else if (event.key === "Home") next = 0;
    else if (event.key === "End") next = tabs.length - 1;
    else return;
    event.preventDefault(); setTab(tabs[next]);
    document.getElementById(`${id}-tab-${tabs[next]}`)?.focus();
  }
  function visualCard(finding: (typeof findings)[number], index: number) {
    return <article key={index} className={styles.finding}>
      <div className="section-heading"><span className={styles.findingLabel}>AI visual observation</span><span className="muted small">{finding.phase === "setup" ? "Setup" : finding.phase === "finish" ? "After the set" : finding.kind === "positive" ? "What looked consistent" : finding.kind === "adjustment" ? "Something to try" : "During your set"}</span></div>
      <h3>{finding.observation}</h3><p>{finding.cue}</p>
      {seekEnabled && <button type="button" className={styles.secondary} onClick={() => onSeek(finding.evidenceTimestampsMs[0])}>Watch moment · {seconds(finding.evidenceTimestampsMs[0])} ↗</button>}
      <details><summary>Evidence timestamps</summary><div className={styles.moments}>{finding.evidenceTimestampsMs.map(time => seekEnabled ? <button key={time} onClick={() => onSeek(time)}>{seconds(time)}</button> : <span key={time}>{seconds(time)}</span>)}</div></details>
    </article>;
  }
  return <section ref={root} className={styles.results} aria-labelledby={`${id}-heading`}>
    <div className={styles.resultHeader}><p className="eyebrow">{live ? "Live set" : "Video review"}</p><h2 id={`${id}-heading`} data-results-heading>Your set, in focus.</h2></div>
    {!measured && <p className={styles.notice}>{analysis.provenance.label} · {analysis.provenance.kind} data. Playback is disabled.</p>}
    <dl className={styles.summary}><div><dd>{analysis.summary.totalReps ?? "—"}</dd><dt>{analysis.summary.totalReps === null ? "Count unavailable" : "Detected reps"}</dt></div><div><dd>{seconds(analysis.source.durationMs)}</dd><dt>{live ? "Sample coverage" : "Clip length"}</dt></div></dl>
    {analysis.status === "partial" && <p className={styles.notice}>Some movement may be uncounted. <a className="text-link" href={`#${id}-limits`} onClick={() => { const details = document.getElementById(`${id}-limits`) as HTMLDetailsElement | null; if (details) details.open = true; }}>See tracking details</a></p>}
    {analysis.reps.length === 0 && <p className="muted small">{analysis.summary.totalReps === 0 ? "No complete movements met the counting rules. Movement observations can still be useful." : "There wasn’t enough information to count completed reps reliably."}</p>}
    <div className={styles.tabs} role="tablist" aria-label="Set review">{tabs.map((name, index) => <button key={name} type="button" role="tab" id={`${id}-tab-${name}`} aria-selected={tab === name} aria-controls={`${id}-panel-${name}`} tabIndex={tab === name ? 0 : -1} onKeyDown={event => changeTab(event, index)} onClick={() => setTab(name)}>{name}{name === "Reps" && analysis.reps.length > 0 ? ` · ${analysis.reps.length}` : ""}</button>)}</div>
    <div role="tabpanel" id={`${id}-panel-Overview`} aria-labelledby={`${id}-tab-Overview`} hidden={tab !== "Overview"} tabIndex={0}>
      {highlights.map(visualCard)}
      {visual?.status === "unavailable" && <p className={styles.notice}>AI visual review couldn’t finish. Your measured results are still available.</p>}
      {!highlights.length && !visibleIssues.length && !analysis.movementObservations?.length && <div className={styles.finding}><span className={styles.findingLabel}>Measured movement</span><h3>{analysis.reps.length ? "Take a closer look at your reps." : "Your available observations"}</h3><p>{analysis.reps.length ? "Explore the timing and available joint angles in Reps, or ask your coach about this set." : "A missing count doesn’t establish that no movement happened. Tracking details explain what could be measured."}</p>{visual?.status === "complete" && !findings.length && <p className="muted small">No clear visual findings were established from the sampled frames.</p>}</div>}
      {showMovement && <MovementObservations observations={analysis.movementObservations} onSeek={seekEnabled ? onSeek : undefined} />}
      {visibleIssues.map(issue => <article className={styles.finding} key={issue.id}><span className={styles.findingLabel}>Measured change</span><h3>{issue.title}</h3><p>{issue.shortCue}</p>{seekEnabled && <button className={styles.secondary} onClick={() => onSeek(issue.startMs)}>Watch moment · {seconds(issue.startMs)} ↗</button>}<details><summary>Why this was flagged</summary><p>{issue.explanation}</p><p className="small muted">Review priority: {issue.severity} · Confidence: {issue.confidence === null ? "Unknown" : `${Math.round(issue.confidence * 100)}%`}</p></details></article>)}
      {(findings.length > highlights.length || analysis.issues.length > visibleIssues.length || (!showMovement && !!analysis.movementObservations?.length)) && <details className={styles.evidence}><summary>All observations</summary>{!showMovement && <MovementObservations observations={analysis.movementObservations} onSeek={seekEnabled ? onSeek : undefined} />}{findings.filter(f => !highlights.includes(f)).map(visualCard)}{analysis.issues.slice(visibleIssues.length).map(issue => <article className={styles.finding} key={issue.id}><span className={styles.findingLabel}>Measured change</span><h3>{issue.title}</h3><p>{issue.shortCue}</p><p>{issue.explanation}</p>{seekEnabled && <button onClick={() => onSeek(issue.startMs)} className={styles.secondary}>Watch moment · {seconds(issue.startMs)}</button>}</article>)}</details>}
      {visual && <details className={styles.evidence}><summary>About AI visual observations</summary><p className="muted small">Interpretation of {visual.sampledTimestampsMs.length} sampled video frames, separate from measured counts and angles.</p><ul>{visual.limitations.map((limit, index) => <li key={index}>{limit}</li>)}</ul></details>}
    </div>
    <div role="tabpanel" id={`${id}-panel-Reps`} aria-labelledby={`${id}-tab-Reps`} hidden={tab !== "Reps"} tabIndex={0}>
      <p className={styles.timingNote}>{analysis.exercise?.id === "incline-dumbbell-bench-press" ? "Counted time runs from bent arms to extension, including pauses. Lowering prepares the next rep." : analysis.exercise?.id === "cable-lateral-raise" ? "Counted time runs from the lowered arm to the raised zone. Angles describe projected hip–shoulder–elbow geometry." : "Counted time includes pauses and confirmation delay. Angles describe this 2D camera view."}</p>
      {analysis.reps.length === 0 && <p className="muted">No completed reps to display. Overview retains any movement observations.</p>}
      {analysis.reps.map((rep) => (
        <details className={styles.rep} key={rep.repNumber} id={`${id}-rep-${rep.repNumber}`}>
          <summary className={styles.repRow} onClick={(event) => { if (!(event.currentTarget.parentElement as HTMLDetailsElement).open && seekEnabled) onSeek(rep.startMs); }}><strong>Rep {rep.repNumber}</strong><span>{seconds(rep.startMs)} – {seconds(rep.endMs)}</span><span>{seconds(rep.measurements.durationMs)}</span></summary>
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
          {(["Left", "Right"] as const).filter(side => rep.measurements[`median${side}ShoulderHipAnkleAngleDeg`] != null).map(side => <p key={side} className="small muted">{side} median shoulder–hip–ankle angle (2D): {angle(rep.measurements[`median${side}ShoulderHipAnkleAngleDeg`])}. This cannot distinguish hips dropping from hips rising or assess your spine.</p>)}
          {rep.measurements.torsoSampleCount != null && <p className="muted small">Torso tilt measures the shoulder–hip line against vertical in the video. It doesn’t assess rotation, momentum or form quality.</p>}
          {referenceComparisons(rep).map((item) => <p key={item.label} className={styles.comparison}><strong>{item.label}: {item.current}</strong><span>Reference median ({item.reference}): {item.baseline} · Change: {item.change}</span></p>)}
          {!live && <div className={styles.moments}>{rep.keyMoments.map((moment, index) => <button type="button" key={`${moment.type}-${index}`} disabled={!seekEnabled} onClick={() => onSeek(moment.timestampMs)}>{moment.label} · {seconds(moment.timestampMs)}</button>)}</div>}

        </details>
      ))}
      {analysis.reps.length > 1 && <details className={styles.evidence}><summary>Compare rep measurements</summary><RepOverview reps={analysis.reps} idPrefix={id} onSeek={seekEnabled ? onSeek : undefined} onShowDetails={() => { document.querySelectorAll<HTMLDetailsElement>(`[id^="${id}-rep-"]`).forEach(item => { item.open = true; }); }} /></details>}
    </div>
    <div role="tabpanel" id={`${id}-panel-Coach`} aria-labelledby={`${id}-tab-Coach`} hidden={tab !== "Coach"} tabIndex={0}><CoachPanel key={analysis.sessionId} analysis={analysis} onSeek={seekEnabled ? onSeek : undefined} /></div>
    <details id={`${id}-limits`} className={styles.evidence}><summary>Tracking & measurement details</summary><p className="muted small">Angles depend on the camera view. Only sufficiently visible joints are measured. Exercise selection does not confirm detection.</p><p className="muted small">Full body visible: {analysis.cameraQuality.fullBodyVisible === null ? "Unknown" : analysis.cameraQuality.fullBodyVisible ? "Yes" : "No"}. Camera quality: {analysis.cameraQuality.score ?? "Unavailable"}.</p><ul>{[...analysis.cameraQuality.issues, ...analysis.limitations].map((item, index) => <li key={index}>{item}</li>)}</ul></details>
  </section>;
}
