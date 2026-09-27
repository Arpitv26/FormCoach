"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { changeLog, useWorkoutLog } from "@/lib/log/browser";
import { deleteSet } from "@/lib/log/store";
import { UploadedResults } from "./uploaded-results";
import { SaveSet } from "./save-set";

export function SavedSetReview({ id }: { id: string }) {
  const log = useWorkoutLog(), router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const record = log.sets.find(set => set.id === id);
  async function remove() {
    setBusy(true); setError("");
    try { await changeLog(storage => deleteSet(storage, id)); router.push("/"); }
    catch (error) { setError(error instanceof Error ? error.message : "Could not delete this set."); setBusy(false); }
  }
  if (!log.ready) return <p role="status">Opening saved set…</p>;
  if (!record) return <section className="panel"><h1>Set unavailable</h1><p>{log.error ?? "This set isn’t saved in this browser, or it was deleted."}</p><Link className="text-link" href="/">Back to workout log</Link></section>;
  return <>
    <div className="page-intro"><Link className="text-link small" href="/">← Workout log</Link><h1>{record.analysis.exercise?.name}</h1><p className="muted">Saved on this device · {record.analysis.source.type === "live" ? "Live" : "Upload"}</p></div>
    <div className="saved-review-layout"><aside><section className="panel missing-video"><h2>{record.analysis.source.type === "live" ? "This live set wasn’t recorded." : "Your video isn’t stored here."}</h2><p className="muted">Your analysis and observations are saved. Playback and skeleton seeking are unavailable.</p>{record.analysis.source.type === "upload" && <><p className="small muted">Reselect and analyze the original clip to get matching playback. Its new analysis can update this saved set.</p><Link className="secondary-action" href={`/upload?exercise=${encodeURIComponent(record.analysis.exercise!.id)}&replace=${encodeURIComponent(id)}`}>Reselect & reanalyze video</Link></>}</section><SaveSet analysis={record.analysis} logId={id} /><details className="delete-set"><summary>Manage saved set</summary><p className="muted small">Analyzed {new Date(record.analysisAt).toLocaleString()}. Deleting removes this summary from this device.</p><button className="secondary-action" disabled={busy} onClick={() => void remove()}>{busy ? "Deleting…" : "Delete saved set"}</button></details>{error && <p className="error" role="alert">{error}</p>}</aside><UploadedResults analysis={record.analysis} canSeek={false} onSeek={() => {}} /></div>
  </>;
}
