import Link from "next/link";
import { ArrowDown, ArrowUpRight, ScanLine, Radio, Dumbbell } from "lucide-react";
import { WorkoutLog } from "@/components/workout-log";
import { BackendStatus } from "@/components/backend-status";
import { SpotlightCard } from "@/components/react-bits/spotlight-card";
import ShinyText from "@/components/react-bits/shiny-text";
import { StarBorder } from "@/components/react-bits/star-border";
import { BlurFade } from "@/components/magicui/blur-fade";
import { BorderBeam } from "@/components/magicui/border-beam";
import { ScrollProgress } from "@/components/design/scroll-progress";
import { ActivityDashboard } from "@/components/activity-dashboard";
import { exercises } from "@/lib/exercises";
import styles from "./page.module.css";
export default function Home() {
  return <main id="main-content"><ScrollProgress />
    <BlurFade><section className={styles.welcome}>
      <div className={styles.welcomeCopy}><p className="eyebrow"><span className="status-dot" /> YOUR MOVEMENT. YOUR MOMENTUM.</p><h1>Every rep.<br /><ShinyText text="More intention." /></h1><p className="muted">See your movement. Find your rhythm.<br />Build a practice that moves with you.</p>
        <div className="action-row"><StarBorder href="/upload"><ScanLine size={20} /> Analyze your set <ArrowUpRight size={18} /></StarBorder><Link className="text-action" href="/camera?exercise=push-up"><Radio size={18} /> Go live</Link></div>
        <a className={styles.scrollCue} href="#activity"><ArrowDown size={16} /> Your training, at a glance</a>
      </div>
      <SpotlightCard className={styles.startCard}><BorderBeam /><div className={styles.cardTop}><span className="eyebrow">NEXT UP</span><ScanLine size={22} /></div><div className={styles.startIcon}><Dumbbell size={64} strokeWidth={1.2} /></div><div><span className="outline-tag">One set is all it takes</span><h2>Meet your movement.</h2><p className="muted">Your video. Your reps. Feedback you can actually see.</p></div><Link href="/upload" className={styles.startLink}>Start a video review <ArrowUpRight size={24} /></Link></SpotlightCard>
    </section></BlurFade>
    <ActivityDashboard />
    <BlurFade><WorkoutLog /></BlurFade>
    <BlurFade><section className={styles.lineup}><div className="section-heading"><div><p className="eyebrow">PICK YOUR MOVEMENT</p><h2>Bring your gym set.</h2></div><span className="muted small">Three ways to find your rhythm</span></div><div className={styles.exerciseGrid}>{exercises.filter(e => e.group === "gym").map((exercise, index) => <SpotlightCard key={exercise.slug}><Link className={styles.exerciseCard} href={`/upload?exercise=${exercise.slug}`}><div className={styles.exerciseCardTop}><span className={styles.exerciseNumber}>0{index + 1}</span><ArrowUpRight size={22} /></div><Dumbbell className={styles.exerciseIcon} size={34} strokeWidth={1.3} /><div><h3>{exercise.name}</h3><p className="muted small">{exercise.equipment}</p></div><span className={styles.exerciseFooter}>Upload & analyze <ArrowUpRight size={16} /></span></Link></SpotlightCard>)}</div></section></BlurFade>
    <BackendStatus /><footer><span>FormCoach · HelloHacks 2026</span><span>A little more intention. Every day.</span></footer>
  </main>;
}
