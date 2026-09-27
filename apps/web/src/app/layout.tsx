import type { Metadata } from "next";
import "./globals.css";
import { DesignMotionProvider } from "@/components/design/motion-provider";
import { AppNavigation } from "@/components/app-navigation";

export const metadata: Metadata = {
  title: "FormCoach | HelloHacks 2026",
  description: "Review your movement, understand your reps, and keep a personal workout log.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body><DesignMotionProvider><AppNavigation />{children}</DesignMotionProvider></body></html>;
}
