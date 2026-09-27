import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
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
  if (exercise.slug !== "push-up") redirect(`/upload?exercise=${exercise.slug}`);
  return (
    <>
      <main id="main-content">
        <div className={styles.intro}>
          <p className="eyebrow">Live workspace · push-ups</p>
          <h1>Make room for your next set.</h1>
          <p className="muted">Check your camera and find a comfortable place to move.</p>
        </div>
        <WebcamSetup key={exercise.slug} exercise={exercise} />
        <footer><span>FormCoach · HelloHacks 2026</span><span>General movement feedback. Camera visibility matters.</span></footer>
      </main>
    </>
  );
}
