"use client";

import { useEffect, useId, useRef, useState } from "react";
import { api } from "@/lib/api/client";
import type { AnalysisResponse, CoachRequest } from "@/lib/api/types";
import { CoachSession, initialCoachState } from "@/lib/coach/session";
import { describeEvidence } from "@/lib/coach/evidence";
import styles from "./coach-panel.module.css";

export function CoachPanel({ analysis, onSeek }: { analysis: AnalysisResponse; onSeek?: (ms: number) => void }) {
  const [state, setState] = useState(initialCoachState);
  const [question, setQuestion] = useState("");
  const session = useRef<CoachSession | null>(null);
  const conversation = useRef<HTMLDivElement>(null);
  const id = useId();
  useEffect(() => {
    if (conversation.current) conversation.current.scrollTop = conversation.current.scrollHeight;
  }, [state.exchanges]);
  useEffect(() => {
    const current = new CoachSession(analysis, (input, signal) => api.coach(input, signal), setState);
    session.current = current;
    return () => { current.dispose(); session.current = null; };
  }, [analysis]);
  function submit(mode: CoachRequest["mode"], prompt = question) {
    if (state.busy) return;
    void session.current?.submit(mode, prompt);
    if (mode === "qa" && prompt.trim()) setQuestion("");
  }
  return <section className={styles.panel} aria-labelledby={`${id}-heading`}>
    <div className="section-heading"><h2 id={`${id}-heading`}>Chat with your coach</h2><span className="outline-tag">About this set</span></div>
    <p className="muted small">Ask what changed, tell me how it felt, or plan your next set.</p>
    {analysis.provenance.kind !== "measured" && <p className={styles.notice}>You’re reviewing {analysis.provenance.kind} data.</p>}
    <div className={styles.actions} aria-label="Suggested questions">
      <button type="button" disabled={state.busy} onClick={() => submit("summary")}>How did my set go?</button>
      <button type="button" disabled={state.busy} onClick={() => submit("next_set")}>What should I focus on?</button>
      {analysis.status === "partial" && <button type="button" disabled={state.busy} onClick={() => submit("qa", "I think you missed some reps. What can we check?")}>You missed some reps</button>}
    </div>
    <div ref={conversation} className={styles.conversation} role="log" aria-label="Conversation with coach" tabIndex={0}>
      {state.exchanges.map((turn, index) => <div key={index} className={styles.exchange}>
        <p className={styles.question}><span className="sr-only">You: </span>{turn.question}</p>
        <div className={styles.answer}>
          <p className={styles.speaker}>{turn.response.provider === "openai" ? "AI coach" : "FormCoach · local"}</p>
          <p className={styles.message}>{turn.response.message}</p>
          <details><summary>Measurements behind this reply</summary>
            {turn.response.evidence.length === 0 ? <p className="muted small">No specific measurements cited.</p> : <ul>{turn.response.evidence.map((path, i) => {
              const item = describeEvidence(analysis, path);
              return <li key={`${path}-${i}`}><span>{item.label}: <strong>{item.text}</strong></span>{item.rep && onSeek && <button type="button" onClick={() => onSeek(item.rep!.startMs)}>View rep {item.rep.repNumber}</button>}</li>;
            })}</ul>}
            {turn.response.limitations.length > 0 && <div className={styles.limits}><ul>{turn.response.limitations.map((item, i) => <li key={i}>{item}</li>)}</ul></div>}
          </details>
        </div>
      </div>)}
    </div>
    <form onSubmit={(event) => { event.preventDefault(); submit("qa"); }}>
      <label htmlFor={`${id}-question`}>Message your coach</label>
      <div className={styles.composer}>
        <textarea id={`${id}-question`} value={question} onChange={(event) => setQuestion(event.target.value)} maxLength={1000} rows={2} placeholder="What changed during my set?" disabled={state.busy} />
        <button className="primary-action" type="submit" disabled={state.busy || !question.trim()}>Send</button>
      </div>
    </form>
    <div className={styles.feedback}><p role="status" className="small">{state.busy ? "Coach is thinking…" : ""}</p>{state.busy && <button type="button" onClick={() => session.current?.cancel()}>Cancel</button>}</div>
    {state.error && <p role="alert" className={styles.error}>{state.error}</p>}
    <p className="muted small">Based on this set’s measurements. Camera tracking can miss movement.</p>
  </section>;
}
