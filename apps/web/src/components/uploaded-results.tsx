"use client";

import { useId, useState, type KeyboardEvent } from "react";
import { CoachPanel } from "./coach-panel";
import { RepOverview } from "./rep-overview";
import { Check, ArrowUpRight, Minus, ChevronDown, Play } from "lucide-react";
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
  const groups = [
    { kind: "positive", title: "Keep it up", icon: Check },
    { kind: "adjustment", title: "Try next set", icon: ArrowUpRight },
    { kind: "observation", title: "Worth noticing", icon: Minus },
  ] as const;
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
  return <section ref={root} className={styles.results} aria-labelledby={`${id}-heading`}>
    <div className={styles.resultHeader}><p className="eyebrow">{live ? "Live set" : "Video review"}</p><h2 id={`${id}-heading`} data-results-heading>Your set, in focus.</h2></div>
    {!measured && <p className={styles.notice}>{analysis.provenance.label} · {analysis.provenance.kind} data. Playback is disabled.</p>}
    <dl className={styles.summary}><div><dd>{analysis.summary.totalReps ?? "—"}</dd><dt>{analysis.summary.totalReps === null ? "Count unavailable" : "Detected reps"}</dt></div><div><dd>{seconds(analysis.source.durationMs)}</dd><dt>{live ? "Sample coverage" : "Clip length"}</dt></div></dl>
    {analysis.reps.length === 0 && <p className="muted small">{analysis.summary.totalReps === 0 ? "No complete movements met the counting rules. Movement observations can still be useful." : "There wasn’t enough information to count completed reps reliably."}</p>}
    <div className={styles.tabs} role="tablist" aria-label="Set review">{tabs.map((name, index) => <button key={name} type="button" role="tab" id={`${id}-tab-${name}`} aria-selected={tab === name} aria-controls={`${id}-panel-${name}`} tabIndex={tab === name ? 0 : -1} onKeyDown={event => changeTab(event, index)} onClick={() => setTab(name)}>{name}{name === "Reps" && analysis.reps.length > 0 ? ` · ${analysis.reps.length}` : ""}</button>)}</div>
    <div role="tabpanel" id={`${id}-panel-Overview`} aria-labelledby={`${id}-tab-Overview`} hidden={tab !== "Overview"} tabIndex={0}>
      <div className={styles.takeaways}>
        {findings.length > 0 && <p className={styles.reviewSource}>AI review · Quick takeaways</p>}
        {groups.map(({ kind, title, icon: Icon }) => {
          const items = findings.filter(finding => finding.kind === kind);
          if (!items.length) return null;
          return <section key={kind} className={styles.takeawayGroup} aria-label={title}>
            <h3><span className={styles.takeawayIcon}><Icon size={17} aria-hidden="true" /></span>{title}</h3>
            <ul>{items.map((finding, index) => <li key={index}>
              <p>{finding.phase === "setup" && <span className={styles.phase}>Before your reps · </span>}{finding.phase === "finish" && <span className={styles.phase}>After the set · </span>}{finding.observation}</p>
              {finding.cue.trim() !== finding.observation.trim() && <p className={styles.takeawayCue}><span>{kind === "positive" ? "Keep doing this:" : kind === "adjustment" ? "Next time:" : "Takeaway:"}</span> {finding.cue}</p>}
              {seekEnabled && <button type="button" className={styles.watchLink} aria-label={`Watch moment: ${finding.observation}`} onClick={() => onSeek(finding.evidenceTimestampsMs[0])}><Play size={13} aria-hidden="true" />Watch</button>}
            </li>)}</ul>
          </section>;
        })}
        {(analysis.issues.length > 0 || !!analysis.movementObservations?.length) && <section className={styles.takeawayGroup} aria-label="Movement to review">
          <h3><span className={styles.takeawayIcon}><Minus size={17} aria-hidden="true" /></span>Movement to review</h3>
          <ul>{analysis.issues.map(issue => <li key={issue.id}><p>{issue.shortCue || issue.title}</p>{seekEnabled && <button type="button" className={styles.watchLink} aria-label={`Watch moment: ${issue.title}`} onClick={() => onSeek(issue.startMs)}><Play size={13} aria-hidden="true" />Watch</button>}</li>)}
            {!!analysis.movementObservations?.length && <li><p>Your body line bent during this clip. These may include setup; review the moments in context.</p>{seekEnabled && <button type="button" className={styles.watchLink} aria-label="Watch moment: body line bend" onClick={() => onSeek(analysis.movementObservations![0].startMs)}><Play size={13} aria-hidden="true" />Watch</button>}</li>}
          </ul>
        </section>}
        {visual?.status === "unavailable" && <p className="muted small">AI review is unavailable for this set. Your measured results are in Reps.</p>}
        {!findings.length && !analysis.issues.length && !analysis.movementObservations?.length && <p className={styles.emptyTakeaways}>{analysis.reps.length ? "Explore your rep timing and measurements, or ask your trainer about this set." : "There aren’t enough observations for a set overview yet."}</p>}
      </div>
    </div>
    <div role="tabpanel" id={`${id}-panel-Reps`} aria-labelledby={`${id}-tab-Reps`} hidden={tab !== "Reps"} tabIndex={0}>
      {analysis.reps.length === 0 && <p className="muted">No completed reps to display. Overview retains any movement observations.</p>}
      {analysis.reps.map((rep) => (
        <details className={styles.rep} key={rep.repNumber} id={`${id}-rep-${rep.repNumber}`}>
          <summary className={styles.repRow} onClick={(event) => { if (!(event.currentTarget.parentElement as HTMLDetailsElement).open && seekEnabled) onSeek(rep.startMs); }}><strong>Rep {rep.repNumber}</strong><span>{seconds(rep.startMs)} – {seconds(rep.endMs)}</span><span className={styles.repDuration}>{seconds(rep.measurements.durationMs)}</span><ChevronDown className={styles.repChevron} size={18} aria-hidden="true" /></summary>
          <div className={styles.repBody}>
          {!live && <div className={styles.repHeading}><span className="small muted">Rep breakdown</span><button type="button" disabled={!seekEnabled} onClick={() => onSeek(rep.startMs)}>Replay rep <Play size={14} aria-hidden="true" /></button></div>}
          <dl className={styles.measurements}>
            {(["Elbow", "Shoulder"] as const).map((joint) => (["Left", "Right"] as const).filter((side) => rep.measurements[`minSmoothed${side}${joint}AngleDeg`] != null).map((side) => (
              <div key={`${side}-${joint}`}><dt>{side} {joint.toLowerCase()} · min / max</dt><dd>{angle(rep.measurements[`minSmoothed${side}${joint}AngleDeg`])} / {angle(rep.measurements[`maxSmoothed${side}${joint}AngleDeg`])}</dd><dt>Observed angle range</dt><dd>{angle(rep.measurements[`smoothed${side}${joint}ExcursionDeg`])}</dd></div>
            )))}
            <div><dt>Time to minimum angle</dt><dd>{seconds(rep.measurements.timeToMinElbowAngleMs ?? rep.measurements.timeToMinShoulderAngleMs)}</dd><dt>Time after minimum angle</dt><dd>{seconds(rep.measurements.timeFromMinElbowAngleMs ?? rep.measurements.timeFromMinShoulderAngleMs)}</dd></div>
            {(["Left", "Right"] as const).filter((side) => `min${side}TorsoTiltDeg` in rep.measurements).map((side) => (
              <div key={`${side}-torso`}><dt>Torso tilt · min / max</dt><dd>{angle(rep.measurements[`min${side}TorsoTiltDeg`])} / {angle(rep.measurements[`max${side}TorsoTiltDeg`])}</dd><dt>Observed torso angle range</dt><dd>{angle(rep.measurements[`${side.toLowerCase()}TorsoTiltRangeDeg`])}</dd></div>
            ))}
          </dl>
          {(["Left", "Right"] as const).filter(side => rep.measurements[`median${side}ShoulderHipAnkleAngleDeg`] != null).map(side => <p key={side} className="small muted">{side} median shoulder–hip–ankle angle (2D): {angle(rep.measurements[`median${side}ShoulderHipAnkleAngleDeg`])}.</p>)}
          {referenceComparisons(rep).map((item) => <p key={item.label} className={styles.comparison}><strong>{item.label}: {item.current}</strong><span>Reference median ({item.reference}): {item.baseline} · Change: {item.change}</span></p>)}
          {!live && <div className={styles.moments}>{rep.keyMoments.map((moment, index) => <button type="button" key={`${moment.type}-${index}`} disabled={!seekEnabled} onClick={() => onSeek(moment.timestampMs)}>{moment.label} · {seconds(moment.timestampMs)}</button>)}</div>}
          </div>
        </details>
      ))}
      {analysis.reps.length > 1 && <details className={styles.evidence}><summary>Compare rep measurements</summary><RepOverview reps={analysis.reps} idPrefix={id} onSeek={seekEnabled ? onSeek : undefined} onShowDetails={() => { document.querySelectorAll<HTMLDetailsElement>(`[id^="${id}-rep-"]`).forEach(item => { item.open = true; }); }} /></details>}
    </div>
    <div role="tabpanel" id={`${id}-panel-Coach`} aria-labelledby={`${id}-tab-Coach`} hidden={tab !== "Coach"} tabIndex={0}><CoachPanel key={analysis.sessionId} analysis={analysis} onSeek={seekEnabled ? onSeek : undefined} /></div>
  </section>;
}
