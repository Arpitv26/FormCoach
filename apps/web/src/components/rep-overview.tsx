"use client";

import { useState } from "react";
import type { RepAnalysis } from "@/lib/api/types";
import { formatMetric, repMetric, type RepMetric } from "@/lib/results/measurements";
import styles from "./video-upload.module.css";

export function RepOverview({ reps, onSeek, onShowDetails, idPrefix }: { reps: RepAnalysis[]; onSeek?: (ms: number) => void; onShowDetails?: () => void; idPrefix: string }) {
  const [metric, setMetric] = useState<RepMetric>("duration");
  if (reps.length === 0) return null;
  const max = Math.max(1, ...reps.map((rep) => repMetric(rep, metric) ?? 0));
  return <section className={styles.overview} aria-label="Rep measurement comparison">
    <div className="section-heading"><h3>Your set at a glance</h3><div className={styles.metricSwitch} role="group" aria-label="Chart measurement"><button type="button" aria-pressed={metric === "duration"} onClick={() => setMetric("duration")}>Counted time</button><button type="button" aria-pressed={metric === "range"} onClick={() => setMetric("range")}>Elbow range</button></div></div>
    <p className="muted small">{metric === "duration" ? "Time per completed rep, including pauses and confirmation delay." : "Observed 2D elbow range in this camera view."} Longer bars do not mean better form.</p>
    <div className={styles.barList}>
      {reps.map((rep) => {
        const value = repMetric(rep, metric);
        const content = <><span>Rep {rep.repNumber}</span><span className={styles.barTrack} aria-hidden="true"><span style={{ width: value === null ? 0 : `${value / max * 100}%` }} /></span><strong>{formatMetric(value, metric)}</strong></>;
        const label = `Rep ${rep.repNumber}: ${formatMetric(value, metric)}. ${onSeek ? "View video" : "Go to details"}`;
        return onSeek ? <button className={styles.barRow} aria-label={label} key={rep.repNumber} type="button" onClick={() => onSeek(rep.startMs)}>{content}</button> : <a className={styles.barRow} aria-label={label} key={rep.repNumber} href={`#${idPrefix}-rep-${rep.repNumber}`} onClick={onShowDetails}>{content}</a>;
      })}
    </div>
  </section>;
}
