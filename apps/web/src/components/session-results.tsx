import type { AnalysisResponse } from "@/lib/api/types";

const statusLabels: Record<AnalysisResponse["status"], string> = {
  complete: "Session complete",
  partial: "Set in progress · completed reps only",
  insufficient_data: "Not enough information to analyze this set",
  not_implemented: "Movement analysis is not available yet",
};

export function SessionResults({ analysis }: { analysis: AnalysisResponse }) {
  const isDemo = analysis.provenance.kind === "synthetic";

  return (
    <section className="session-results" aria-labelledby="session-heading">
      <header className="session-header">
        <div>
          <p className="eyebrow">Session overview</p>
          <h2 id="session-heading">
            {analysis.exercise ? `${analysis.exercise.name} session` : "Movement session"}
          </h2>
        </div>
        <span className="provenance-badge">
          {isDemo ? "Demo data" : analysis.provenance.kind === "measured" ? "Measured data" : "Analysis unavailable"}
        </span>
      </header>

      <p className="muted">{analysis.provenance.label}</p>
      <p className="session-status">{statusLabels[analysis.status]}</p>
      <p className="session-headline">{analysis.summary.headline}</p>

      <dl className="session-stats">
        <div className="session-stat session-stat-primary">
          <dt>{isDemo ? "Example overall score" : "Overall score"}</dt>
          <dd>
            {analysis.summary.overallScore === null ? (
              <span className="unavailable-value">Not available</span>
            ) : (
              <>{analysis.summary.overallScore}<span className="score-unit"> / 100</span></>
            )}
          </dd>
        </div>
        <div className="session-stat">
          <dt>{isDemo ? "Example completed reps" : "Completed reps"}</dt>
          <dd>
            {analysis.summary.totalReps ?? <span className="unavailable-value">Not available</span>}
          </dd>
        </div>
      </dl>

      {analysis.reps.length > 0 && (
        <div className="rep-summary">
          <h3>{isDemo ? "Example rep scores" : "Rep scores"}</h3>
          <ol className="reps" aria-label={isDemo ? "Example rep scores" : "Rep scores"}>
            {analysis.reps.map((rep) => (
              <li key={rep.repNumber}>
                <span className="muted">Rep {rep.repNumber}</span>
                <strong>{rep.score ?? "Not available"}</strong>
              </li>
            ))}
          </ol>
        </div>
      )}

      {analysis.limitations.length > 0 && (
        <aside className="session-limitations" aria-label="Result limitations">
          <h3>About these results</h3>
          <ul>
            {analysis.limitations.map((limitation, index) => (
              <li key={`${index}-${limitation}`}>{limitation}</li>
            ))}
          </ul>
        </aside>
      )}
    </section>
  );
}
