import type { MetadataRoute } from "next";
import { getAgents } from "@/lib/api";
import { loadRepoAgents } from "@/lib/repo-agents";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000";
  const now = new Date();

  const entries: MetadataRoute.Sitemap = [
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
  ];

  const isStaticExport = (process.env.NEXT_OUTPUT || "").toLowerCase() === "export";

  // Best-effort: include agent detail pages for crawlability.
  try {
    const agents = isStaticExport
      ? await loadRepoAgents()
      : await (async () => {
          const pageSize = 100;
          const first = await getAgents({ page: 1, page_size: pageSize });
          const totalPages = Math.max(1, Math.ceil((first.total || 0) / pageSize));

          const pages = [first];
          for (let p = 2; p <= totalPages; p += 1) {
            pages.push(await getAgents({ page: p, page_size: pageSize }));
          }
          return pages.flatMap((r) => r.items || []);
        })();

    for (const a of agents) {
      const id = a.id;
      if (!id) continue;
      entries.push({
        url: `${baseUrl}/agents/${encodeURIComponent(id)}`,
        lastModified: a.updated_at ? new Date(a.updated_at * 1000) : now,
        changeFrequency: "weekly",
        priority: 0.7,
      });
    }
  } catch {
    // ignore
  }

  return entries;
}
