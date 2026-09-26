import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FormCoach | HelloHacks 2026",
  description: "Movement coaching grounded in measured evidence. Hackathon foundation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
