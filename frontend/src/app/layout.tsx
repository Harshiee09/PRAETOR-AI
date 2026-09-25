import type { Metadata } from "next";
import "@fontsource-variable/manrope";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/noto-sans-devanagari";
import "./globals.css";
import "@/components/ui/effects.css";
import "./monochrome.css";
import "./document.css";
import { ResearchProvider } from "@/components/research-provider";
import { AppShell } from "@/components/app-shell";

export const metadata: Metadata = {
  title: {
    default: "PRAETOR AI — Indian law, in context",
    template: "%s · PRAETOR AI",
  },
  description:
    "An informational research workspace for Indian central Acts and Supreme Court judgments. Answers grounded in cited sources. Not legal advice.",
  robots: { index: false, follow: false },
};
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-scroll-behavior="smooth" suppressHydrationWarning>
      <body>
        <ResearchProvider>
          <AppShell>{children}</AppShell>
        </ResearchProvider>
      </body>
    </html>
  );
}
