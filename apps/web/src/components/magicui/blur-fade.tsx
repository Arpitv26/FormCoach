"use client";
// Adapted from Magic UI BlurFade. See THIRD_PARTY_NOTICES.md.
import { useRef, type ReactNode } from "react";
import { motion, useInView } from "motion/react";
import { useDesignMotion } from "../design/motion-provider";
export function BlurFade({ children, className, delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "0px 0px -24px 0px" });
  const { enabled } = useDesignMotion();
  return <motion.div ref={ref} className={`scroll-reveal ${className ?? ""}`} initial={false}
    animate={inView || !enabled ? "visible" : "hidden"}
    variants={{ hidden: { y: 18, opacity: 0.35 }, visible: { y: 0, opacity: 1 } }}
    transition={{ duration: enabled ? 0.5 : 0, delay: enabled ? delay : 0, ease: "easeOut" }}>
    {children}
  </motion.div>;
}
