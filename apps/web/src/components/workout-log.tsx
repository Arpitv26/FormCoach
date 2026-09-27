"use client";

import Link from "next/link";
import { useState } from "react";
import { exercises } from "@/lib/exercises";
import { useWorkoutLog } from "@/lib/log/browser";
import { activity, movement, timing } from "@/lib/log/trackers";
import { AppIcon } from "./app-navigation";
import styles from "../app/page.module.css";

function dateLabel(value: string) { return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }); }

export function WorkoutLog() {
  const log = useWorkoutLog();
  const [exercise, setExercise] = useState("all");
  const [source, setSource] = useState("all");
  const filtered = log.sets.filter(set => (exercise === "all" || set.analysis.exercise?.id === exercise) && (source === "all" || set.analysis.source.type === source)).sort((a, b) => b.performedDate.localeCompare(a.performedDate) || b.analysisAt.localeCompare(a.analysisAt));
  const totals = activity(filtered);
  const dates = [...new Set(filtered.map(set => set.performedDate))];
  return <section className={styles.activity} aria-labelledby="log-heading">
    <div className="section-heading"><h2 id="log-heading">Your workout log</h2><span className="muted small">Saved on this device</span></div>
    {!log.ready ? <p className="muted" role="status">Opening your saved sets…</p> : log.error ? <p className="error" role="alert">{log.error}</p> : <>
      {log.skipped > 0 && <p className="notice">{log.skipped} unsupported or damaged entries couldn’t be displayed. They remain stored unchanged.</p>}
      {!log.sets.length ? <div className={styles.empty}><span className={styles.emptyIcon}><AppIcon name="dashboard" /></span><h3>Your story starts with a set.</h3><p className="muted">Review a video or finish a live set, then save it here.<br />Your actual reps and observations, all in one place.</p><div className="action-row"><Link className="secondary-action" href="/upload">Upload a video</Link><Link className="text-link" href="/camera?exercise=push-up">Start live push-ups →</Link></div></div> : <>
        <div className="log-filters"><label>Exercise<select value={exercise} onChange={event => { setExercise(event.target.value); setSource(event.target.value === "push-up" ? "live" : event.target.value === "all" ? "all" : "upload"); }}><option value="all">All exercises</option>{exercises.map(item => <option key={item.slug} value={item.slug}>{item.name}</option>)}</select></label><label>Source<select value={source} onChange={event => setSource(event.target.value)}><option value="all">All sources</option><option value="upload">Upload</option><option value="live">Live</option></select></label></div>
        <dl className="log-stats"><div><dd>{totals.sets}</dd><dt>Saved sets</dt></div><div><dd>{totals.days}</dd><dt>Logged days</dt></div><div><dd>{totals.reps ?? "—"}</dd><dt>Detected reps</dt></div></dl>
        {(totals.partial > 0 || totals.unknown > 0) && <p className="notice small">{totals.partial > 0 && `${totals.partial} sets have partial tracking; detected totals may be incomplete. `}{totals.unknown > 0 && `${totals.unknown} sets have unknown counts and are excluded from the rep total.`}</p>}
        {!filtered.length && <p className="notice">No saved sets match these filters.</p>}
        {dates.map(date => <section className="log-day" key={date} aria-label={dateLabel(date)}><h3>{dateLabel(date)}</h3><div className="log-list">{filtered.filter(set => set.performedDate === date).map(set => <Link className="log-row" key={set.id} href={`/sets/${encodeURIComponent(set.id)}`}><span className="log-source"><AppIcon name={set.analysis.source.type === "live" ? "live" : "upload"} /></span><div><h3>{set.analysis.exercise?.name}</h3><p className="muted small">{set.analysis.source.type === "live" ? "Live" : "Upload"} · {set.analysis.status === "partial" ? "Partial tracking" : set.analysis.summary.totalReps === null ? "Count unavailable" : "Analyzed set"}</p></div><span className="log-count"><strong>{set.analysis.summary.totalReps ?? "—"}</strong><span className="muted small">detected reps</span></span><AppIcon name="arrow" /></Link>)}</div></section>)}
        {filtered.length > 0 && <details className="tracker-details"><summary>Exercise breakdown & measurements</summary>
          <div className="exercise-breakdown">{exercises.map(item => { const sets = filtered.filter(set => set.analysis.exercise?.id === item.slug); return sets.length ? <p key={item.slug}><strong>{item.name}</strong><span>{sets.length} saved {sets.length === 1 ? "set" : "sets"}</span></p> : null; })}</div>
          {exercise === "all" || source === "all" ? <p className="muted small">Select one exercise and one source to explore its timing and movement measurements.</p> : <>
            <h3>Rep timing, set by set</h3><p className="muted small">Median counted time and within-set range (longest minus shortest). Includes pauses and confirmation delay; this is not workout duration or a form score.</p>
            <p className="notice">Analysis rule versions aren’t reported by this API. Measurements are shown separately; no progress trend is inferred. Camera view can also change 2D angles.</p>
            {filtered.map(set => { const time = timing(set); return <div className="tracker-row" key={set.id}><Link className="text-link" href={`/sets/${encodeURIComponent(set.id)}`}>{dateLabel(set.performedDate)} · {set.analysis.summary.totalReps ?? "Unknown"} reps</Link><p>Median: {time.median === null ? "Unavailable" : `${(time.median / 1000).toFixed(2)} s`} · Within-set range: {time.spread === null ? "Unavailable" : `${(time.spread / 1000).toFixed(2)} s`}</p>{movement(set).map(metric => <p className="muted small" key={metric.key}>{metric.label}, median: {metric.value.toFixed(1)}°</p>)}</div>; })}
          </>}
        </details>}
      </>}
    </>}
    <p className="muted small log-storage-note">Your browser can clear this log. Videos, skeleton tracks, and chat aren’t stored.</p>
  </section>;
}
