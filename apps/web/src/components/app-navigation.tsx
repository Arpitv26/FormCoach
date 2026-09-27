"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function AppIcon({ name }: { name: "dashboard" | "upload" | "live" | "arrow" }) {
  return <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {name === "dashboard" ? <><rect x="3" y="3" width="7" height="7" rx="2" /><rect x="14" y="3" width="7" height="7" rx="2" /><rect x="3" y="14" width="7" height="7" rx="2" /><rect x="14" y="14" width="7" height="7" rx="2" /></> : name === "upload" ? <><path d="M12 16V3m-5 5 5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4" /></> : name === "live" ? <><rect x="3" y="6" width="12" height="12" rx="3" /><path d="m15 10 6-3v10l-6-3" /></> : <path d="M5 12h14m-6-6 6 6-6 6" />}
  </svg>;
}

export function AppNavigation() {
  const path = usePathname();
  return <>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <header className="site-header">
      <Link className="brand" href="/" aria-label="FormCoach dashboard"><span className="brand-mark" aria-hidden="true"><svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"><path d="M5 17V7h6M5 12h5m4-5h5m-5 0v10h5" /></svg></span>FormCoach<span className="brand-dot">.</span></Link>
      <nav className="app-nav" aria-label="Main navigation">
        {([{ href: "/", label: "Dashboard", icon: "dashboard" }, { href: "/upload", label: "Upload", icon: "upload" }, { href: "/camera?exercise=push-up", label: "Live", icon: "live" }] as const).map((item) => <Link key={item.label} href={item.href} aria-current={(item.href === "/" ? path === "/" || path.startsWith("/sets/") : path === item.href.split("?")[0]) ? "page" : undefined}><AppIcon name={item.icon} /><span>{item.label}</span></Link>)}
      </nav>
      <span className="header-caption">A little more intention.</span>
    </header>
  </>;
}
