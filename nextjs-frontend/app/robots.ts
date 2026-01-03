import type { MetadataRoute } from "next";

export const dynamic = "force-static";

function siteUrl(): string {
  const raw =
    process.env.SITE_URL ||
    process.env.NEXT_PUBLIC_SITE_URL ||
    "http://localhost:3000";
  return raw.endsWith("/") ? raw.slice(0, -1) : raw;
}

export default function robots(): MetadataRoute.Robots {
  const baseUrl = siteUrl();
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/workers$", "/consult"],
        disallow: ["/api/", "/_next/", "/static/"],
      },
      {
        userAgent: ["GPTBot", "ChatGPT-User", "CCBot", "Google-Extended"],
        disallow: ["/"],
      },
      {
        userAgent: ["Anthropic-ai", "Claude-Web"],
        disallow: ["/api/"],
      },
    ],
    sitemap: `${baseUrl}/sitemap.xml`,
    host: baseUrl,
  };
}
