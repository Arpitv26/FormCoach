"use client";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { ArrowUpRight, ScanLine, Video, NotebookPen, Pause, Play } from "lucide-react";
import { useDesignMotion } from "./design/motion-provider";
import styles from "./video-hero.module.css";
export function VideoHero() {
  const video = useRef<HTMLVideoElement>(null);
  const area = useRef<HTMLElement>(null);
  const inView = useInView(area);
  const { enabled } = useDesignMotion();
  const [paused, setPaused] = useState(false);
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    const element = video.current;
    if (!element) return;
    const sync = () => {
      if (enabled && inView && !paused && !document.hidden && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        void element.play().catch(() => { /* The poster stays available when autoplay is blocked. */ });
      } else element.pause();
    };
    sync(); document.addEventListener("visibilitychange", sync);
    return () => { document.removeEventListener("visibilitychange", sync); element.pause(); };
  }, [enabled, inView, paused]);
  return <section className={styles.hero} ref={area} aria-labelledby="hero-heading">
    <video ref={video} className={styles.video} muted loop playsInline preload="metadata" poster="/media/training-hero-poster.jpg" aria-hidden="true" tabIndex={-1} onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)}>
      <source src="/media/training-hero.mp4" type="video/mp4" />
    </video>
    <div className={styles.shade} aria-hidden="true" />
    <div className={styles.copy}><h1 id="hero-heading">See every rep clearly.</h1><p>Review your movement. Understand your set.<br className={styles.mobileBreak} /> Know what to work on next.</p><div className={styles.actions}><Link href="/upload" className={styles.primary}>Analyze your set <span><ArrowUpRight size={19} /></span></Link><Link href="/camera?exercise=push-up" className={styles.secondary}>Start live push-ups <ArrowUpRight size={18} /></Link></div></div>
    <div className={styles.bottom}><div className={styles.features}>
      <div><ScanLine size={22} /><div><h2>Your video, in focus</h2><p>Review reps and return to the moments that matter.</p></div></div>
      <div><Video size={22} /><div><h2>Move. See. Repeat.</h2><p>Count your push-ups live, with your camera.</p></div></div>
      <div><NotebookPen size={22} /><div><h2>Keep your perspective</h2><p>Save each set and build your personal workout log.</p></div></div>
    </div><button className={styles.videoControl} disabled={!enabled} onClick={() => { if (playing) setPaused(true); else { setPaused(false); void video.current?.play().catch(() => {}); } }} aria-label={!enabled ? "Background video paused by motion settings" : playing ? "Pause background video" : "Play background video"}>{playing ? <Pause size={15} /> : <Play size={15} />}<span>{playing ? "Pause video" : "Video paused"}</span></button></div>
  </section>;
}
