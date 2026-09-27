"use client";
import { useEffect, useRef } from "react";
import { animate } from "motion";
import { useDesignMotion } from "@/components/design/motion-provider";
export function useReviewMotion(sessionId: string) {
  const root = useRef<HTMLElement>(null);
  const { enabled } = useDesignMotion();
  useEffect(() => {
    const heading = root.current?.querySelector<HTMLElement>("[data-results-heading]");
    if (!heading || !window.matchMedia || !enabled) return;
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (preference.matches) return;
    const animation = animate(heading, { opacity: [.5, 1], y: [10, 0] }, { duration: .4, ease: "easeOut" });
    const changed = () => { if (preference.matches) animation.complete(); };
    preference.addEventListener("change", changed);
    return () => { preference.removeEventListener("change", changed); animation.complete(); };
  }, [sessionId, enabled]);
  return root;
}
