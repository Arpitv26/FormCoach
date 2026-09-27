"use client";

import type { AnalysisResponse } from "@/lib/api/types";
import styles from "./video-upload.module.css";

export function MovementObservations({ observations, onSeek }: {
  observations: AnalysisResponse["movementObservations"];
  onSeek?: (ms: number) => void;
}) {
  if (!observations?.length) return null;
  return <section className={styles.changes} aria-label="Movement to review">
    <h3>Your body line bent here</h3>
    <p>Your tracked shoulder, hip and ankle formed a noticeable bend at these moments. You can review them even when no complete push-up was counted.</p>
    <p className="muted small">These moments may include setup. This is one camera-based observation, not a complete form assessment.</p>
    <div className={styles.moments}>{observations.slice(0, 1).map((item) => {
      const label = `${(item.startMs / 1000).toFixed(2)}–${(item.endMs / 1000).toFixed(2)} s`;
      return onSeek
        ? <button key={item.startMs} className={styles.secondary} type="button" onClick={() => onSeek(item.startMs)}>Review {label} ↗</button>
        : <span key={item.startMs} className="outline-tag">{label}</span>;
    })}</div>
    <details className={styles.evidence}><summary>All movement moments & evidence</summary>
      <p className="muted small">We look for a sustained bend between the shoulder, hip and ankle in the image. This cannot tell hips dropping from hips rising, or assess your spine. Camera view affects the estimate.</p>
      <ul>{observations.map((item) => <li key={item.startMs}>
        {onSeek && <button type="button" className={styles.secondary} onClick={() => onSeek(item.startMs)}>Watch moment · {(item.startMs / 1000).toFixed(2)} s</button>} {(item.startMs / 1000).toFixed(2)}–{(item.endMs / 1000).toFixed(2)} s: {item.side} side, typical angle {item.medianAngleDeg.toFixed(1)}° across {item.sampleCount} samples. Straight is 180°; our provisional review threshold is below {item.thresholdAngleDeg}° for at least half a second.
      </li>)}</ul>
    </details>
  </section>;
}
