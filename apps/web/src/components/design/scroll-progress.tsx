"use client";
import { motion, useScroll, useSpring } from "motion/react";
import { useDesignMotion } from "./motion-provider";
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 180, damping: 30 });
  const { enabled } = useDesignMotion();
  return enabled ? <motion.div className="scroll-progress" aria-hidden="true" style={{ scaleX }} /> : null;
}
