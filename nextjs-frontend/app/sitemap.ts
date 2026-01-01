import type { MetadataRoute } from "next";
import { headers } from "next/headers";
import { fetchWorkers } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const h = await headers();
  const host = h.get("x-forwarded-host") || h.get("host") || "localhost:3000";
  const proto = h.get("x-forwarded-proto") || "http";
  const baseUrl = `${proto}://${host}`;
  const now = new Date();
  const entries: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}/`,
      changeFrequency: "hourly",
      priority: 1.0,
      lastModified: now,
    },
    {
      url: `${baseUrl}/consult`,
      changeFrequency: "weekly",
      priority: 0.7,
      lastModified: now,
    },
  ];

  try {
    const pageSize = 200;
    const maxUrls = 5000; // hard cap to keep sitemap generation bounded
    const first = await fetchWorkers({ limit: String(pageSize), offset: "0" });

    const total = Math.max(0, Number(first.total || 0));
    const maxToFetch = Math.min(total, maxUrls);

    const addItems = (items: any[]) => {
      for (const w of items || []) {
        if (!w?.slug) continue;
        entries.push({
          url: `${baseUrl}/workers/${encodeURIComponent(w.slug)}`,
          changeFrequency: "weekly",
          priority: 0.6,
          lastModified: w.updated_at ? new Date(w.updated_at) : now,
        });
      }
    };

    addItems(first.items || []);

    for (let offset = pageSize; offset < maxToFetch; offset += pageSize) {
      const page = await fetchWorkers({
        limit: String(pageSize),
        offset: String(offset),
      });
      addItems(page.items || []);
    }
  } catch {
    // Keep sitemap valid even if the API is unavailable at build/runtime.
  }

  return entries;
}
