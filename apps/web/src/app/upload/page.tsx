import type { Metadata } from "next";
import Link from "next/link";
import { VideoUpload } from "@/components/video-upload";

export const metadata: Metadata = { title: "Analyze push-ups | FormCoach" };

export default function UploadPage() {
  return (
    <>
      <a className="skip-link" href="#main-content">Skip to video upload</a>
      <header className="site-header">
        <Link className="brand" href="/" aria-label="FormCoach home"><span className="brand-mark" aria-hidden="true">f<span>c</span></span>FormCoach<span className="brand-dot">.</span></Link>
        <nav aria-label="Main navigation"><Link href="/">Exercises</Link><Link href="/upload" aria-current="page">Video analysis</Link><Link href="/camera?exercise=push-up">Camera setup</Link></nav>
      </header>
      <main id="main-content">
        <VideoUpload />
        <footer><span>FormCoach · HelloHacks 2026</span><span>General movement feedback. Visibility matters.</span></footer>
      </main>
    </>
  );
}
