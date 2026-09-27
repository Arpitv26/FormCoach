import type { CSSProperties } from "react";
import type { AnalysisResponse } from "@/lib/api/types";

const statusLabels: Record<AnalysisResponse["status"], string> = {
  complete: "Session complete",
  partial: "Partial evidence · completed reps only",
  insufficient_data: "Not enough information to analyze this set",
  not_implemented: "Movement analysis is not available yet",
};

const metrics = [
  ["rangeOfMotion", "Range of motion", "Movement through each rep"],
  ["symmetry", "Symmetry", "Left and right comparison"],
  ["tempo", "Tempo", "The pace of your movement"],
  ["stability", "Stability", "Control throughout the set"],
  ["consistency", "Consistency", "How your reps compare"],
] as const;

function seconds(milliseconds: number) {
  return `${Number((milliseconds / 1000).toFixed(1))}s`;
}

export function SessionResults({ analysis }: { analysis: AnalysisResponse }) {
  const isDemo = analysis.provenance.kind === "synthetic";
  const score = analysis.summary.overallScore;
  const lowestRep = analysis.reps.reduce<AnalysisResponse["reps"][number] | undefined>(
    (lowest, rep) => rep.score !== null && (!lowest || rep.score < lowest.score!) ? rep : lowest,
    undefined,
  );

  return (
    <div className="session-results">
      <section id="overview" className="overview-panel" aria-labelledby="session-heading">
        <div className="overview-copy">
          <p className="eyebrow"><span className="status-dot" /> {statusLabels[analysis.status]}</p>
          <h1 id="session-heading">Every rep.<br /><span>A little more insight.</span></h1>
          <p className="session-headline">{analysis.summary.headline}</p>
          <div className="session-tags">
            <span className="exercise-tag">{analysis.exercise?.name ?? "Exercise not selected"}</span>
            <span className="provenance-badge">
              {isDemo ? "Demo data" : analysis.provenance.kind === "measured" ? "Measured data" : "Analysis unavailable"}
            </span>
          </div>
          <p className="provenance-note">{analysis.provenance.label}</p>
          <a className="primary-action" href="#reps">Explore your reps <span aria-hidden="true">↗</span></a>
        </div>

        <div className="score-panel">
          <div className="score-orbit" style={{ "--score-angle": `${(score ?? 0) * 3.6}deg` } as CSSProperties}>
            <div className="score-center">
              <span className="eyebrow">{isDemo ? "Example score" : "Overall score"}</span>
              {score === null ? <strong className="unavailable-value">Not available</strong> : <><strong className="overall-score">{score}</strong><span className="muted">out of 100</span></>}
            </div>
          </div>
          <dl className="session-stats">
            <div><dt>{isDemo ? "Example reps" : "Completed reps"}</dt><dd>{analysis.summary.totalReps ?? "Not available"}</dd></div>
            <div><dt>Sample duration</dt><dd>{analysis.source.durationMs === null ? "Not available" : seconds(analysis.source.durationMs)}</dd></div>
          </dl>
        </div>
      </section>

      <section className="metrics-section" aria-labelledby="metrics-heading">
        <div className="section-heading"><div><p className="eyebrow">The bigger picture</p><h2 id="metrics-heading">Your movement breakdown</h2></div><span className="muted small">{isDemo ? "Example scores" : "Available scores"} · out of 100</span></div>
        <dl className="metric-grid">
          {metrics.map(([key, label, description], index) => {
            const value = analysis.metrics[key];
            return (
              <div className="metric-card" key={key}>
                <dt><span className="metric-number" aria-hidden="true">0{index + 1}</span>{label}</dt>
                <dd className={value === null ? "metric-value unavailable-value" : "metric-value"}>{value ?? "Not available"}</dd>
                <dd className="metric-description"><div className="metric-track" aria-hidden="true"><span style={{ width: `${value ?? 0}%` }} /></div><p>{description}</p></dd>
              </div>
            );
          })}
        </dl>
      </section>

      <div className="results-grid">
        <section id="reps" className="panel rep-panel" aria-labelledby="reps-heading">
          <div className="section-heading"><div><p className="eyebrow">Rep by rep</p><h2 id="reps-heading">Find your rhythm</h2></div><span className="outline-tag">{isDemo ? "Demo set" : "Current set"}</span></div>
          <p className="muted small">Select a rep below to see its timing and reported cues.</p>
          {analysis.reps.length === 0 ? <p className="empty-state">No completed reps are available yet. Check the result limitations below.</p> : (
            <>
              <div className="rep-chart" aria-label="Rep score comparison">
                {analysis.reps.map((rep) => (
                  <a className={`chart-column${lowestRep?.repNumber === rep.repNumber ? " lowest" : ""}`} href={`#rep-${rep.repNumber}`} key={rep.repNumber} aria-label={`Rep ${rep.repNumber}: ${rep.score === null ? "score not available" : `${rep.score} out of 100`}${lowestRep?.repNumber === rep.repNumber ? ", lowest score" : ""}. Go to details.`}>
                    <span className="chart-value">{rep.score ?? "N/A"}</span>
                    <span className="chart-track" aria-hidden="true"><span style={{ height: `${rep.score ?? 0}%` }} /></span>
                    <span className="chart-label">Rep {rep.repNumber}</span>
                  </a>
                ))}
              </div>
              {lowestRep && <p className="chart-caption"><span className="legend-dot" /> Rep {lowestRep.repNumber} has the lowest available score in this set.</p>}
              <div className="rep-list">
                {analysis.reps.map((rep) => (
                  <details className="rep-detail" id={`rep-${rep.repNumber}`} key={rep.repNumber}>
                    <summary><span>Rep {rep.repNumber}</span><span className="rep-timing">{seconds(rep.startMs)} – {seconds(rep.endMs)}</span><strong>{rep.score ?? "Not available"}</strong><span className="expand-icon" aria-hidden="true">+</span></summary>
                    <div className="rep-detail-content">
                      <p>{rep.issues.length ? "Reported cues" : "No issues reported for this rep. This does not confirm every aspect of form was evaluated."}</p>
                      {rep.issues.map((issue) => <p key={issue.id}><strong>{issue.title}</strong> · {issue.shortCue}</p>)}
                      <p className="muted">{isDemo ? "These timings belong to the synthetic example. No matching video is attached." : "Timing is relative to the start of this set."}</p>
                    </div>
                  </details>
                ))}
              </div>
            </>
          )}
        </section>

        <section className="panel insight-panel" aria-labelledby="insight-heading">
          <p className="eyebrow"><span aria-hidden="true">✦</span> In focus</p>
          <h2 id="insight-heading">A closer look</h2>
          {analysis.issues.length === 0 ? <p className="muted">No issues reported. Available measurements and limitations describe what could be evaluated.</p> : analysis.issues.map((issue) => (
            <article className="issue-card" key={issue.id}>
              <div className="issue-meta"><span className="outline-tag">{issue.severity} priority</span><span>{seconds(issue.startMs)} – {seconds(issue.endMs)}</span></div>
              <h3>{issue.title}</h3>
              <p className="issue-cue">{issue.shortCue}</p>
              <p className="muted small">{issue.explanation}</p>
              <p className="confidence-label">{isDemo ? "Example confidence" : "Reported confidence"}: {issue.confidence === null ? "Not available" : `${Math.round(issue.confidence * 100)}%`}</p>
            </article>
          ))}
          <div className="camera-note"><span className="eyebrow">Camera context</span><p>{analysis.cameraQuality.fullBodyVisible === null ? "Full-body visibility has not been evaluated." : analysis.cameraQuality.fullBodyVisible ? `${isDemo ? "The example indicates" : "The analysis reports"} the full body is visible.` : "Some of the body is outside the usable view."}</p>{analysis.cameraQuality.issues.map((issue, index) => <p key={index}>{issue}</p>)}</div>
        </section>
      </div>

      <section id="details" className="panel limitations-panel" aria-labelledby="limitations-heading">
        <div><p className="eyebrow">Context matters</p><h2 id="limitations-heading">Behind the numbers</h2><p className="muted small">General movement feedback. Scores are uncalibrated heuristics.</p></div>
        <ul>{analysis.limitations.map((limitation, index) => <li key={index}>{limitation}</li>)}</ul>
      </section>
    </div>
  );
}
