"use client";

import Link from "next/link";
import { useId, useState } from "react";
import type { AnalysisResponse } from "@/lib/api/types";
import { changeLog, useWorkoutLog } from "@/lib/log/browser";
import { localDate, saveSet, type SavedSet } from "@/lib/log/store";

export function SaveSet({ analysis, logId, replacing = false, onSaved }: {
  analysis: AnalysisResponse; logId: string; replacing?: boolean; onSaved?: (id: string) => void;
}) {
  const log = useWorkoutLog();
  if (analysis.provenance.kind !== "measured" || analysis.status === "not_implemented") return null;
  if (!log.ready) return <p className="muted small">Opening your workout log…</p>;
  if (log.error) return <p role="alert" className="error">{log.error}</p>;
  const existing = log.sets.find(set => set.id === logId);
  return <SaveForm key={analysis.sessionId} analysis={analysis} logId={logId} existing={existing} replacing={replacing} onSaved={onSaved} />;
}

function SaveForm({ analysis, logId, existing, replacing, onSaved }: {
  analysis: AnalysisResponse; logId: string; existing?: SavedSet; replacing: boolean; onSaved?: (id: string) => void;
}) {
  const id = useId();
  const [performedDate, setDate] = useState(existing?.performedDate ?? localDate());
  const [notes, setNotes] = useState(existing?.notes ?? "");
  const [analysisAt] = useState(() => existing?.analysis.sessionId === analysis.sessionId ? existing.analysisAt : new Date().toISOString());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const saved = existing?.analysis.sessionId === analysis.sessionId && existing.notes === notes && existing.performedDate === performedDate;
  async function save(asNew = false) {
    if (busy) return;
    setBusy(true); setError("");
    try {
      const record = await changeLog(storage => saveSet(storage, {
        id: asNew ? crypto.randomUUID() : logId, analysis, analysisAt, performedDate, notes,
        analysisRevision: existing?.analysis.sessionId === analysis.sessionId ? existing.analysisRevision : null,
      }, !asNew && (!!existing || replacing)));
      onSaved?.(record.id);
    } catch (error) { setError(error instanceof Error ? error.message : "Set not saved. Please try again."); }
    finally { setBusy(false); }
  }
  return <section className="save-set" aria-label="Save to workout log">
    <div className="section-heading"><div><h3>{saved ? "Added to your workout log" : "Keep this set"}</h3><p className="muted small">Saved on this device · summaries only</p></div><button className={saved ? "secondary-action" : "primary-action"} disabled={busy || saved} onClick={() => void save()}>{busy ? "Saving…" : saved ? "Saved ✓" : existing || replacing ? "Update saved set" : "Save set"}</button></div>
    <details><summary>Performed date & notes</summary><p className="muted small">Choose when you performed this set. An upload’s analysis date may be different.</p><label htmlFor={`${id}-date`}>Performed date</label><input id={`${id}-date`} type="date" required value={performedDate} onChange={event => setDate(event.target.value)} /><label htmlFor={`${id}-notes`}>Notes (optional)</label><textarea id={`${id}-notes`} maxLength={1000} rows={2} value={notes} placeholder="Anything you’d like to remember?" onChange={event => setNotes(event.target.value)} /></details>
    {!saved && (existing || replacing) && existing?.analysis.sessionId !== analysis.sessionId && <button className="secondary-action" disabled={busy} onClick={() => void save(true)}>Save as another set</button>}
    <p role="status" className="small">{saved && <Link className="text-link" href="/">View workout log →</Link>}</p>
    {error && <p role="alert" className="error">{error}</p>}
  </section>;
}
