import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { WebcamSetup } from "@/components/webcam-setup";
import { findExercise } from "@/lib/exercises";
import styles from "@/components/webcam-setup.module.css";

export const metadata: Metadata = { title: "Camera setup | FormCoach" };

export default async function CameraPage({ searchParams }: {
  searchParams: Promise<{ exercise?: string | string[] }>;
}) {
  const { exercise: slug = "push-up" } = await searchParams;
  const exercise = typeof slug === "string" ? findExercise(slug) : undefined;
  if (!exercise) notFound();
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to camera setup</a>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="FormCoach exercises"><span className="brand-mark" aria-hidden="true">f<span>c</span></span>FormCoach<span className="brand-dot">.</span></Link>
        <nav aria-label="Main navigation"><Link href="/">Exercises</Link><Link href={`/camera?exercise=${exercise.slug}`} aria-current="page">Camera setup</Link></nav>
        <span className="header-caption">MOVE WITH INTENTION</span>
      </header>
      <main id="main-content">
        <div className={styles.intro}>
          <p className="eyebrow">{exercise.group === "live" ? "Push-ups · live demo" : "Gym session · camera preview"}</p>
          <h1>Let’s get you <span>in frame.</span></h1>
          <p className="muted">Check your camera and find a comfortable place to move.</p>
        </div>
        <WebcamSetup key={exercise.slug} exercise={exercise} />
        <footer><span>FormCoach · HelloHacks 2026</span><span>General movement feedback. Camera visibility matters.</span></footer>
      </main>
    </>
  );
}
