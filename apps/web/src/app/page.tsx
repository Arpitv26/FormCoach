import Link from "next/link";
import { ArrowUpRight, Dumbbell } from "lucide-react";
import { VideoHero } from "@/components/video-hero";
import { WorkoutLog } from "@/components/workout-log";
import { BackendStatus } from "@/components/backend-status";
import { SpotlightCard } from "@/components/react-bits/spotlight-card";
import { BlurFade } from "@/components/magicui/blur-fade";
import { ScrollProgress } from "@/components/design/scroll-progress";
import { ActivityDashboard } from "@/components/activity-dashboard";
import { exercises } from "@/lib/exercises";
import styles from "./page.module.css";
export default function Home() {
  return <main id="main-content" className={styles.homeMain}><ScrollProgress />
    <VideoHero />
    <div className={styles.dashboardContent}>
    <ActivityDashboard />
    <BlurFade><WorkoutLog /></BlurFade>
    <BlurFade><section className={styles.lineup}><div className="section-heading"><div><p className="eyebrow">PICK YOUR MOVEMENT</p><h2>Bring your gym set.</h2></div><span className="muted small">Three ways to find your rhythm</span></div><div className={styles.exerciseGrid}>{exercises.filter(e => e.group === "gym").map((exercise, index) => <SpotlightCard key={exercise.slug}><Link className={styles.exerciseCard} href={`/upload?exercise=${exercise.slug}`}><div className={styles.exerciseCardTop}><span className={styles.exerciseNumber}>0{index + 1}</span><ArrowUpRight size={22} /></div><Dumbbell className={styles.exerciseIcon} size={34} strokeWidth={1.3} /><div><h3>{exercise.name}</h3><p className="muted small">{exercise.equipment}</p></div><span className={styles.exerciseFooter}>Upload & analyze <ArrowUpRight size={16} /></span></Link></SpotlightCard>)}</div></section></BlurFade>
    <BackendStatus /><footer><span>FormCoach · HelloHacks 2026</span><span>A little more intention. Every day.</span></footer></div>
  </main>;
}
