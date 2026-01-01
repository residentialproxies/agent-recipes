import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { SiteHeader } from "@/components/site-header";
import { SiteFooter } from "@/components/site-footer";

const inter = Inter({ subsets: ["latin"] });
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;

export const metadata: Metadata = {
  metadataBase: siteUrl ? new URL(siteUrl) : undefined,
  title: "Agent Navigator - Discover LLM Agents",
  description:
    "Discover and explore 100+ production-ready LLM agent examples with AI-powered recommendations.",
  keywords: [
    "LLM",
    "AI agents",
    "LangChain",
    "CrewAI",
    "AutoGen",
    "agent examples",
  ],
  openGraph: {
    title: "Agent Navigator - Discover LLM Agents",
    description:
      "Discover and explore production-ready LLM agent examples with AI-powered recommendations.",
    type: "website",
    url: "/",
    siteName: "Agent Navigator",
  },
  twitter: {
    card: "summary",
    title: "Agent Navigator - Discover LLM Agents",
    description:
      "Discover and explore production-ready LLM agent examples with AI-powered recommendations.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={cn(inter.className, "antialiased")}>
        <div className="min-h-screen flex flex-col">
          <SiteHeader />
          <div className="flex-1">{children}</div>
          <SiteFooter />
        </div>
      </body>
    </html>
  );
}
