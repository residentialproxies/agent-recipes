import type { MetadataRoute } from "next";
import { getAgents } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";

  const { items } = await getAgents({
    page: 1,
    page_size: 2000,
    sort: "name",
  }).catch(() => ({
    query: "",
    total: 0,
    page: 1,
    page_size: 2000,
    items: [],
  }));
  const now = new Date();

  return [
    {
      url: `${baseUrl}/`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 1,
    },
    {
      url: `${baseUrl}/agents`,
      lastModified: now,
      changeFrequency: "daily",
      priority: 0.9,
    },
    ...items.map((a) => ({
      url: `${baseUrl}/agents/${a.id}`,
      lastModified: a.updated_at ? new Date(a.updated_at * 1000) : now,
      changeFrequency: "weekly" as const,
      priority: 0.7,
    })),
  ];
}
