import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { findExercise } from "@/lib/exercises";
import { VideoUpload } from "@/components/video-upload";

export const metadata: Metadata = { title: "Video analysis | FormCoach" };

export default async function UploadPage({ searchParams }: { searchParams: Promise<{ exercise?: string | string[]; replace?: string | string[] }> }) {
  const { exercise: slug = "push-up", replace } = await searchParams;
  const exercise = typeof slug === "string" ? findExercise(slug) : undefined;
  if (!exercise?.backendHint) notFound();
  return (
    <>
      <main id="main-content">
        <VideoUpload key={`${exercise.slug}-${typeof replace === "string" ? replace : ""}`} exercise={exercise} replaceId={typeof replace === "string" && /^[\w-]{1,100}$/.test(replace) ? replace : undefined} />
        <footer><span>FormCoach · HelloHacks 2026</span><span>General movement feedback. Visibility matters.</span></footer>
      </main>
    </>
  );
}
