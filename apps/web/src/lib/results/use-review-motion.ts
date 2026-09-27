"use client";

import { useEffect, useRef } from "react";
import { animate, createScope } from "animejs";

/** One short entry reveal; no animation touches counts, player geometry, or skeletons. */
export function useReviewMotion(sessionId: string) {
  const root = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!root.current || !window.matchMedia) return;
    const preference = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (preference.matches) return;
    const scope = createScope({ root: root.current }).add(() => {
      animate("[data-results-heading]", { opacity: [.85, 1], translateY: [4, 0], duration: 180, ease: "out(2)" });
    });
    const changed = () => { if (preference.matches) scope.revert(); };
    preference.addEventListener("change", changed);
    return () => { preference.removeEventListener("change", changed); scope.revert(); };
  }, [sessionId]);
  return root;
}
