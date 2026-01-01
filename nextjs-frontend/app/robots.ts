import type { MetadataRoute } from "next";
import { headers } from "next/headers";

export const dynamic = "force-dynamic";

export default async function robots(): Promise<MetadataRoute.Robots> {
  const h = await headers();
  const host = h.get("x-forwarded-host") || h.get("host") || "localhost:3000";
  const proto = h.get("x-forwarded-proto") || "http";
  const baseUrl = `${proto}://${host}`;
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
