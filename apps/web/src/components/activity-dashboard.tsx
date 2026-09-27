"use client";
import Link from "next/link";
import { useState, useSyncExternalStore } from "react";
import { CalendarDays, Layers3, MoveUpRight, Activity } from "lucide-react";
import { motion } from "motion/react";
import { useWorkoutLog } from "@/lib/log/browser";
import { localDate } from "@/lib/log/store";
import { activitySeries } from "@/lib/log/activity-series";
import { SpotlightCard } from "./react-bits/spotlight-card";
import { BlurFade } from "./magicui/blur-fade";
import { useDesignMotion } from "./design/motion-provider";
const subscribe = () => () => {};
const getToday = () => localDate(new Date());
const noToday = () => "";
export function ActivityDashboard() {
  const log = useWorkoutLog();
  const today = useSyncExternalStore(subscribe, getToday, noToday);
  const [days, setDays] = useState(7);
  const [selected, setSelected] = useState<string | null>(null);
  const { enabled } = useDesignMotion();
  const series = today ? activitySeries(log.sets, today, days) : [];
  const total = series.reduce((sum, day) => sum + day.sets, 0);
  const loggedDays = series.filter(day => day.sets > 0).length;
  const knownReps = series.filter(day => day.reps !== null);
  const reps = knownReps.length ? knownReps.reduce((sum, day) => sum + day.reps!, 0) : null;
  const max = Math.max(1, ...series.map(day => day.sets));
  const focus = series.find(day => day.date === selected);
  const shortDate = (date: string) => new Date(`${date}T12:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return <section id="activity" className="activity-dashboard" aria-labelledby="activity-title">
    <BlurFade><div className="section-heading activity-heading"><div><p className="eyebrow">THE BIG PICTURE</p><h2 id="activity-title">Your momentum.</h2><p className="muted small">Small steps. A clearer picture.</p></div><div className="period-switch" aria-label="Activity period">{[7, 28].map(value => <button key={value} aria-pressed={days === value} onClick={() => { setDays(value); setSelected(null); }}>{value === 7 ? "Week" : "4 weeks"}</button>)}</div></div></BlurFade>
    {!log.ready || !today ? <p role="status" className="muted">Opening your activity…</p> : log.error ? <p className="error" role="alert">{log.error}</p> : <>
      <div className="dashboard-stats">{[{ label: "Saved sets", value: total, icon: Layers3, note: `Last ${days} days` }, { label: "Logged days", value: loggedDays, icon: CalendarDays, note: "Days with saved sets" }, { label: "Detected reps", value: reps ?? "—", icon: Activity, note: "From known counts" }].map((stat, index) => <BlurFade key={stat.label} delay={index * .06}><SpotlightCard className="stat-card"><div className="stat-top"><span>{stat.label}</span><stat.icon size={19} /></div><strong>{stat.value}</strong><p className="muted small">{stat.note}</p></SpotlightCard></BlurFade>)}</div>
      <BlurFade delay={.08}><SpotlightCard className="activity-chart-card"><div className="section-heading"><div><h3>Saved sets</h3><p className="muted small">Saved sets · {shortDate(series[0].date)} – {shortDate(today)}</p></div><span className="chart-key"><span /> Daily activity</span></div>
        <div className="activity-chart" style={{ gridTemplateColumns: `repeat(${days}, minmax(44px, 1fr))` }} aria-label="Saved sets by performed date">{series.map((day, index) => <button key={day.date} className={`activity-bar ${day.date === today ? "today" : ""}`} aria-pressed={selected === day.date} aria-label={`${shortDate(day.date)}: ${day.sets} saved sets`} onClick={() => setSelected(day.date)}><span className="bar-value">{day.sets || ""}</span><span className="activity-bar-track"><motion.span initial={false} animate={{ height: day.sets ? `${Math.max(8, day.sets / max * 100)}%` : "3px" }} transition={{ duration: enabled ? .65 : 0, delay: enabled ? index * .018 : 0 }} className={day.sets ? "has-sets" : "no-sets"} /></span><span className="bar-day">{days === 7 ? new Date(`${day.date}T12:00:00`).toLocaleDateString(undefined, { weekday: "narrow" }) : index % 7 === 0 || index === days - 1 ? day.date.slice(8) : ""}</span></button>)}</div>
        <div className="chart-detail" aria-live="polite">{focus ? <><strong>{shortDate(focus.date)}</strong><span>{focus.sets} saved {focus.sets === 1 ? "set" : "sets"} · {focus.reps === null ? "No known rep count" : `${focus.reps} detected reps`}{focus.unknown ? ` · ${focus.unknown} unknown counts excluded` : ""}</span></> : <><strong>{total ? `${loggedDays} logged days` : "Your next set starts the story."}</strong><span>{total ? "Select a day to explore your activity." : "Save a reviewed set to light up your activity."}</span></>}</div>
        <details className="chart-note"><summary>About this activity</summary><p className="muted small">Performed dates are entered by you. Partial tracking can leave reps uncounted; unknown counts are excluded.</p></details>
      </SpotlightCard></BlurFade>
      <BlurFade><Link className="dashboard-next" href="/upload"><span><strong>One more set. One more perspective.</strong><span className="muted small">Upload a clip and see what stood out.</span></span><MoveUpRight size={22} /></Link></BlurFade>
    </>}
  </section>;
}
