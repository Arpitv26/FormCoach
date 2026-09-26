import { BackendStatus } from "@/components/backend-status";
import { getMockAnalysis } from "@/lib/api/mock";

export default function Home() {
  const analysis = getMockAnalysis();
  return (
    <main>
      <p className="eyebrow">UBC BizTech HelloHacks 2026 · Foundation</p>
      <h1>FormCoach</h1>
      <p>Movement coaching grounded in measured evidence.</p>
      <section aria-labelledby="demo-heading">
        <h2 id="demo-heading">Mock squat session</h2>
        <p><strong>{analysis.provenance.label}</strong></p>
        <p>{analysis.summary.headline}</p>
        <p>Example overall score: {analysis.summary.overallScore ?? "Unknown"}/100 · {analysis.summary.totalReps ?? "Unknown"} reps</p>
        <ol className="reps" aria-label="Example rep scores">
          {analysis.reps.map((rep) => <li key={rep.repNumber}>Rep {rep.repNumber}: <strong>{rep.score ?? "Unknown"}</strong></li>)}
        </ol>
        <p className="muted">Camera tracking, video analysis, and the results dashboard are next steps.</p>
      </section>
      <BackendStatus />
      <footer>General movement feedback. Camera visibility and confidence matter.</footer>
    </main>
  );
}
