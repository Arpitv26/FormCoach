"use client";
// Adapted from React Bits SpotlightCard. See THIRD_PARTY_NOTICES.md.
import { useRef, type PropsWithChildren, type MouseEventHandler } from "react";
export function SpotlightCard({ children, className = "" }: PropsWithChildren<{ className?: string }>) {
  const divRef = useRef<HTMLDivElement>(null);
  const handleMouseMove: MouseEventHandler<HTMLDivElement> = e => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    divRef.current.style.setProperty("--mouse-x", `${e.clientX - rect.left}px`);
    divRef.current.style.setProperty("--mouse-y", `${e.clientY - rect.top}px`);
  };
  return <div ref={divRef} onMouseMove={handleMouseMove} className={`card-spotlight ${className}`}>{children}</div>;
}
