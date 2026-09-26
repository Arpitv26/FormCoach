import Link from "next/link";
import { BackendStatus } from "@/components/backend-status";
import { exercises } from "@/lib/exercises";
import styles from "./page.module.css";

export default function Home() {
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to exercises</a>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="FormCoach home"><span className="brand-mark" aria-hidden="true">f<span>c</span></span>FormCoach<span className="brand-dot">.</span></Link>
        <nav aria-label="Main navigation"><a href="#live-demo">Live demo</a><a href="#gym">Gym exercises</a></nav>
        <Link className="camera-entry" href="/camera?exercise=push-up">Use camera <span aria-hidden="true">↗</span></Link>
      </header>
      <main id="main-content">
        <div className="page-heading"><p>YOUR MOVEMENT, IN FOCUS</p><span>Choose your session <span aria-hidden="true">↙</span></span></div>
        <section className={styles.hero} id="live-demo" aria-labelledby="live-heading">
          <div className={styles.heroCopy}>
            <p className="eyebrow">The live demo starts here</p>
            <h1 id="live-heading">Your next rep.<br /><span>A little more intention.</span></h1>
            <p>Start with push-ups. Set your camera beside your mat and find a clear view of your movement.</p>
            <Link className="primary-action" href="/camera?exercise=push-up">Set up push-ups <span aria-hidden="true">↗</span></Link>
            <p className={styles.availability}>Camera preview is available. Tracking and scoring are still to come.</p>
          </div>
          <div className={styles.featuredExercise}>
            <span className={styles.exerciseNumber} aria-hidden="true">01</span>
            <span className="provenance-badge">Live demo focus</span>
            <h2>Push-ups</h2>
            <p>Bodyweight. A little floor space.<br />A side view of every move.</p>
            <div className={styles.featuredFooter}><span>CAMERA SETUP</span><span aria-hidden="true">↗</span></div>
          </div>
        </section>

        <section id="gym" className={styles.gymSection} aria-labelledby="gym-heading">
          <div className="section-heading"><div><p className="eyebrow">Take it to the gym</p><h2 id="gym-heading">Your gym lineup</h2></div><span className="outline-tag">Analysis planned</span></div>
          <p className={styles.sectionIntro}>Choose an exercise to check your camera framing. These exercises do not produce analysis yet.</p>
          <div className={styles.exerciseGrid}>
            {exercises.filter((exercise) => exercise.group === "gym").map((exercise, index) => (
              <article className={styles.exerciseCard} key={exercise.slug}>
                <span className={styles.cardNumber} aria-hidden="true">0{index + 2}</span>
                <p className="eyebrow">{exercise.equipment}</p>
                <h3>{exercise.name}</h3>
                <p>{exercise.framingText}</p>
                <Link href={`/camera?exercise=${exercise.slug}`} aria-label={`Preview framing for ${exercise.name}`}>Preview framing <span aria-hidden="true">↗</span></Link>
              </article>
            ))}
          </div>
        </section>

        <aside className={styles.progressNote} aria-label="Current capabilities">
          <span aria-hidden="true">✦</span>
          <div><h2>Set up first. Measure next.</h2><p>The camera screen is a local preview. Exercise selection does not detect movement, and no rep counts or scores are generated yet.</p></div>
        </aside>
        <BackendStatus />
        <footer><span>FormCoach · HelloHacks 2026</span><span>Small insights. More intentional movement.</span></footer>
      </main>
    </>
  );
}
