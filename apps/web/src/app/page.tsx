import Link from "next/link";
import { BackendStatus } from "@/components/backend-status";
import { AppIcon } from "@/components/app-navigation";
import { exercises } from "@/lib/exercises";
import styles from "./page.module.css";

export default function Home() {
  return <main id="main-content">
    <section className={styles.welcome}>
      <div><p className="eyebrow">Your training, in focus</p><h1>Ready for your next set?</h1><p className="muted">A clear view of your movement. A little more intention in every rep.</p><div className="action-row"><Link className="primary-action" href="/camera?exercise=push-up"><AppIcon name="live" />Start live push-ups</Link><Link className="secondary-action" href="/upload"><AppIcon name="upload" />Upload a video</Link></div></div>
      <div className={styles.welcomeMark} aria-hidden="true"><svg viewBox="0 0 200 130" fill="none" stroke="currentColor" strokeWidth="5" strokeLinecap="round" strokeLinejoin="round"><path d="M20 107h160M30 94l63-42 52 8 17 34M93 52l12 42h20"/><circle cx="160" cy="47" r="12"/><circle cx="93" cy="52" r="5" fill="currentColor"/></svg><span>Make room for your next move.</span></div>
    </section>
    <section className={styles.activity}><div className="section-heading"><h2>Your workout log</h2><span className="muted small">Saved on this device</span></div><div className={styles.empty}><span className={styles.emptyIcon}><AppIcon name="dashboard" /></span><h3>Your story starts with a set.</h3><p className="muted">Review a video or finish a live set, then save it here.<br />Your actual reps and observations, all in one place.</p><Link className="text-link" href="/upload">Review your first set →</Link></div></section>
    <section className={styles.lineup}><div className="section-heading"><h2>Bring your gym set</h2><span className="muted small">Choose an exercise to upload</span></div><div className={styles.exerciseGrid}>{exercises.filter(e => e.group === "gym").map((exercise, index) => <Link className={styles.exerciseCard} href={`/upload?exercise=${exercise.slug}`} key={exercise.slug}><span className={styles.exerciseNumber}>0{index + 1}</span><div><h3>{exercise.name}</h3><p className="muted small">{exercise.equipment}</p></div><AppIcon name="arrow" /></Link>)}</div></section>
    <BackendStatus /><footer><span>FormCoach · HelloHacks 2026</span><span>Movement feedback, grounded in your set.</span></footer>
  </main>;
}
