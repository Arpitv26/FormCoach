"use client";

import { useEffect, useId, useRef, useState } from "react";
import { api } from "@/lib/api/client";
import type { AnalysisResponse, CoachRequest } from "@/lib/api/types";
import { CoachSession, initialCoachState } from "@/lib/coach/session";
import { describeEvidence } from "@/lib/coach/evidence";
import styles from "./coach-panel.module.css";

const modeLabels = { summary: "Set summary", next_set: "Next set", qa: "Your question" };
export function CoachPanel({ analysis, onSeek }: { analysis: AnalysisResponse; onSeek?: (ms: number) => void }) {
  const [state, setState] = useState(initialCoachState);
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const session = useRef<CoachSession | null>(null);
  const id = useId();
  useEffect(() => {
    const current = new CoachSession(analysis, (input, signal) => api.coach(input, signal), setState);
    session.current = current;
    return () => { current.dispose(); session.current = null; };
  }, [analysis]);
  function submit(mode: CoachRequest["mode"]) {
    if (state.busy) return;
    if (mode === "qa") setSubmittedQuestion(question.trim());
    void session.current?.submit(mode, question);
  }
  const result = state.result;
  return (
    <section className={styles.panel} aria-labelledby={`${id}-heading`}>
      <p className="eyebrow">An explanation you can trace</p>
      <div className="section-heading"><h2 id={`${id}-heading`}>Your set, explained.</h2><span aria-hidden="true" className={styles.spark}>✦</span></div>
      <p className="muted small">Explore the measurements from this set. The coach does not evaluate unmeasured form or create a score.</p>
      {analysis.provenance.kind !== "measured" && <p className={styles.notice}>{analysis.provenance.label} · This explanation uses {analysis.provenance.kind} data.</p>}
      <div className={styles.actions}>
        <button type="button" className="primary-action" disabled={state.busy} onClick={() => submit("summary")}>Explain my set</button>
        <button type="button" disabled={state.busy} onClick={() => submit("next_set")}>Next set</button>
        {state.busy && <button type="button" onClick={() => session.current?.cancel()}>Cancel explanation</button>}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); submit("qa"); }}>
        <label htmlFor={`${id}-question`}>Ask about your measurements</label>
        <textarea id={`${id}-question`} value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={1000} rows={2} placeholder="How long did rep 1 take?" aria-describedby={`${id}-help`} disabled={state.busy} />
        <div className={styles.questionFooter}><p id={`${id}-help`} className="muted small">Questions need the optional AI provider. Local coaching supports summaries and next-set guidance.</p><button type="submit" disabled={state.busy || !question.trim()}>Ask coach</button></div>
      </form>
      <p role="status" className="small">{state.busy ? "Preparing an explanation from the available evidence…" : result ? `${modeLabels[result.mode]} ready.` : ""}</p>
      {state.error && <p role="alert" className={styles.error}>{state.error}</p>}
      {result && <div className={styles.answer}>
        <div className="section-heading"><h3>{modeLabels[result.mode]}</h3><span className="outline-tag">{result.provider === "openai" ? "OpenAI · evidence selection" : "Local coach · fallback"}</span></div>
        {result.mode === "qa" && <p className="muted small">Question: {submittedQuestion}</p>}
        <p className={styles.message}>{result.message}</p>
        <details><summary>Supporting evidence ({result.evidence.length})</summary>
          {result.evidence.length === 0 ? <p className="muted small">No specific measurement references were returned.</p> : <ul>{result.evidence.map((path, index) => {
            const item = describeEvidence(analysis, path);
            return <li key={`${path}-${index}`}><span>{item.label}: <strong>{item.text}</strong></span>{item.rep && onSeek && <button type="button" onClick={() => onSeek(item.rep!.startMs)}>View rep {item.rep.repNumber}</button>}<code>{path}</code></li>;
          })}</ul>}
        </details>
        {result.limitations.length > 0 && <div className={styles.limits}><h3>What this explanation can tell you</h3><ul>{result.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul></div>}
      </div>}
    </section>
  );
}
