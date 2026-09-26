import { BackendStatus } from "@/components/backend-status";
import { SessionResults } from "@/components/session-results";
import { getMockAnalysis } from "@/lib/api/mock";

export default function Home() {
  const analysis = getMockAnalysis();
  return (
    <main>
      <header className="page-header">
        <p className="eyebrow">UBC BizTech HelloHacks 2026</p>
        <h1>FormCoach<span className="brand-dot">.</span></h1>
        <p className="page-intro">Understand your movement, one rep at a time.</p>
      </header>
      <SessionResults analysis={analysis} />
      <BackendStatus />
      <footer>General movement feedback. Camera visibility and confidence matter.</footer>
    </main>
  );
}
