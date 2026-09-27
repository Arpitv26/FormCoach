"use client";
import { createContext, useContext, useState, useSyncExternalStore, type ReactNode } from "react";
import { MotionConfig } from "motion/react";
import { usePathname } from "next/navigation";
const MotionContext = createContext({ enabled: true, locked: false, toggle: () => {} });
const reducedQuery = "(prefers-reduced-motion: reduce)";
const subscribe = (notify: () => void) => {
  const query = window.matchMedia(reducedQuery);
  query.addEventListener("change", notify);
  return () => query.removeEventListener("change", notify);
};
const snapshot = () => window.matchMedia(reducedQuery).matches;
const serverSnapshot = () => false;
export function DesignMotionProvider({ children }: { children: ReactNode }) {
  const [paused, setPaused] = useState(false);
  const reduce = useSyncExternalStore(subscribe, snapshot, serverSnapshot);
  const path = usePathname();
  const enabled = !paused && !reduce && path !== "/camera";
  return <MotionContext.Provider value={{ enabled, locked: reduce || path === "/camera", toggle: () => setPaused(value => !value) }}>
    <MotionConfig reducedMotion={enabled ? "user" : "always"}><div className="app-shell" data-motion={enabled ? "on" : "off"}>{children}</div></MotionConfig>
  </MotionContext.Provider>;
}
export const useDesignMotion = () => useContext(MotionContext);
