import "./globals.css";
import type { Metadata } from "next";

const siteUrl =
  process.env.SITE_URL ||
  process.env.NEXT_PUBLIC_SITE_URL ||
  "http://localhost:3000";

export const metadata: Metadata = {
  title: {
    default: "WebManus — AI Workers Directory",
    template: "%s | WebManus",
  },
  description:
    "Find AI workers to automate boring tasks. Filter by capability, pricing, and automation score. Discover the best AI agents, bots, and automation tools for your workflow.",
  keywords: [
    "AI workers",
    "AI agents",
    "automation tools",
    "AI directory",
    "chatbots",
    "AI assistants",
    "no-code AI",
    "LLM apps",
    "agent marketplace",
  ],
  authors: [{ name: "WebManus" }],
  creator: "WebManus",
  publisher: "WebManus",
  metadataBase: new URL(siteUrl),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    type: "website",
    siteName: "WebManus",
    title: "WebManus — AI Workers Directory",
    description:
      "Find AI workers to automate boring tasks. Filter by capability, pricing, and automation score.",
    url: siteUrl,
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "WebManus - AI Workers Directory",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    site: "@webmanus",
    creator: "@webmanus",
    title: "WebManus — AI Workers Directory",
    description:
      "Find AI workers to automate boring tasks. Filter by capability, pricing, and automation score.",
    images: ["/og-image.png"],
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  verification: {
    google: process.env.GOOGLE_SITE_VERIFICATION,
    yandex: process.env.YANDEX_VERIFICATION,
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const apiBase =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.API_URL ||
    "http://localhost:8000";
  const apiBaseClean = apiBase.endsWith("/") ? apiBase.slice(0, -1) : apiBase;
  const apiDocsUrl = `${apiBaseClean}/docs`;
  return (
    <html lang="en">
      <body>
        <div className="container">
          <div className="nav">
            <div className="brand">
              <span>WebManus</span>
              <span className="badge">Digital HR</span>
            </div>
            <div className="navlinks">
              <a href="/">Workers</a>
              <a href="/consult">Consult</a>
              <a href={apiDocsUrl} target="_blank" rel="noreferrer">
                API Docs
              </a>
            </div>
          </div>
          {children}
        </div>
      </body>
    </html>
  );
}
