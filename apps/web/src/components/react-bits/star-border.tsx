// Adapted from React Bits StarBorder. See THIRD_PARTY_NOTICES.md.
import Link from "next/link";
import type { ReactNode } from "react";
export function StarBorder({ href, children, className = "" }: { href: string; children: ReactNode; className?: string }) {
  return <Link href={href} className={`star-border-container ${className}`}>
    <span className="border-gradient-bottom" aria-hidden="true" />
    <span className="border-gradient-top" aria-hidden="true" />
    <span className="star-inner-content">{children}</span>
  </Link>;
}
