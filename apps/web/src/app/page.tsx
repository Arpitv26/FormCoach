import { BackendStatus } from "@/components/backend-status";
import { SessionResults } from "@/components/session-results";
import { getMockAnalysis } from "@/lib/api/mock";

export default function Home() {
  const analysis = getMockAnalysis();
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to results</a>
      <header className="site-header">
        <a className="brand" href="#overview" aria-label="FormCoach overview"><span className="brand-mark" aria-hidden="true">f<span>c</span></span>FormCoach<span className="brand-dot">.</span></a>
        <nav aria-label="Session navigation"><a href="#overview">Overview</a><a href="#reps">Your reps</a><a href="#details">Details</a></nav>
        <span className="header-caption">MOVE WITH INTENTION</span>
      </header>
      <main id="main-content">
        <div className="page-heading"><p>YOUR MOVEMENT, IN FOCUS</p><span>Session review <span aria-hidden="true">↙</span></span></div>
        <SessionResults analysis={analysis} />
        <BackendStatus />
        <footer><span>FormCoach · HelloHacks 2026</span><span>Small insights. More intentional movement.</span></footer>
      </main>
    </>
  );
}
