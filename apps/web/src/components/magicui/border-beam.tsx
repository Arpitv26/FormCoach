"use client";
// Adapted from Magic UI BorderBeam. See THIRD_PARTY_NOTICES.md.
import { useRef } from "react";
import { motion, useInView } from "motion/react";
import { useDesignMotion } from "../design/motion-provider";
export function BorderBeam() {
  const ref = useRef(null);
  const inView = useInView(ref);
  const { enabled } = useDesignMotion();
  return <div ref={ref} className="border-beam" aria-hidden="true">
    <motion.div className="border-beam-light" style={{ offsetPath: "rect(0 auto auto 0 round 24px)" }}
      initial={false} animate={{ offsetDistance: enabled && inView ? ["0%", "100%"] : "0%" }}
      transition={{ duration: 7, repeat: enabled && inView ? Infinity : 0, ease: "linear" }} />
  </div>;
}
