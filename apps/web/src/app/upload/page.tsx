import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { findExercise } from "@/lib/exercises";
import { VideoUpload } from "@/components/video-upload";

export const metadata: Metadata = { title: "Video analysis | FormCoach" };

export default async function UploadPage({ searchParams }: { searchParams: Promise<{ exercise?: string | string[] }> }) {
  const { exercise: slug = "push-up" } = await searchParams;
  const exercise = typeof slug === "string" ? findExercise(slug) : undefined;
  if (!exercise?.backendHint) notFound();
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to video upload</a>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="FormCoach home"><span className="brand-mark" aria-hidden="true">f<span>c</span></span>FormCoach<span className="brand-dot">.</span></Link>
        <nav aria-label="Main navigation"><Link href="/">Exercises</Link><Link href="/upload" aria-current="page">Video analysis</Link><Link href="/camera?exercise=push-up">Camera setup</Link></nav>
      </header>
      <main id="main-content">
        <VideoUpload key={exercise.slug} exercise={exercise} />
        <footer><span>FormCoach · HelloHacks 2026</span><span>General movement feedback. Visibility matters.</span></footer>
      </main>
    </>
  );
}
