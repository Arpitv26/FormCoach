"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Upload, Video, ArrowUpRight, Activity, Pause, Play } from "lucide-react";
import { motion } from "motion/react";
import { useDesignMotion } from "./design/motion-provider";
export function AppIcon({ name }: { name: "dashboard" | "upload" | "live" | "arrow" }) {
  const Icon = { dashboard: LayoutDashboard, upload: Upload, live: Video, arrow: ArrowUpRight }[name];
  return <Icon size={21} strokeWidth={1.7} aria-hidden="true" />;
}
export function AppNavigation() {
  const path = usePathname();
  const { enabled, locked, toggle } = useDesignMotion();
  return <><a className="skip-link" href="#main-content">Skip to content</a><header className="site-header" data-home={path === "/"}>
    <Link className="brand" href="/" aria-label="FormCoach dashboard"><span className="brand-mark"><Activity size={27} aria-hidden="true" /></span>FormCoach<span className="brand-dot">.</span></Link>
    <nav className="app-nav" aria-label="Main navigation">
      {([{ href: "/", label: "Dashboard", icon: "dashboard" }, { href: "/upload", label: "Upload", icon: "upload" }, { href: "/camera?exercise=push-up", label: "Live", icon: "live" }] as const).map(item => {
        const active = item.href === "/" ? path === "/" || path.startsWith("/sets/") : path === item.href.split("?")[0];
        return <Link key={item.label} href={item.href} aria-current={active ? "page" : undefined}>
          {active && <motion.span className="nav-active-pill" layoutId="navigation-pill" transition={{ type: "spring", stiffness: 400, damping: 34 }} />}
          <AppIcon name={item.icon} /><span>{item.label}</span>
        </Link>;
      })}
    </nav>
    <button className="motion-toggle" disabled={locked} onClick={toggle} aria-label={locked ? "Motion disabled for reduced motion or live camera" : enabled ? "Pause decorative motion" : "Enable decorative motion"} aria-pressed={!enabled} title={enabled ? "Pause motion" : "Enable motion"}>{enabled ? <Pause size={16} /> : <Play size={16} />}<span>Motion {enabled ? "on" : "off"}</span></button>
  </header></>;
}
