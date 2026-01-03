import type { Metadata } from "next";
import Link from "next/link";
import { getAgents, getFilters } from "@/lib/api.server";
import { AgentGrid } from "@/components/agent-grid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Agent, AgentFiltersResponse } from "@/types/agent";
import AgentsClient from "./agents-client";
import { computeFiltersFromAgents, loadRepoAgents } from "@/lib/repo-agents";

type SearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string {
  if (!value) return "";
  return Array.isArray(value) ? value[0] || "" : value;
}

function toInt(value: string, fallback: number): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  return Math.floor(n);
}

function buildUrl(params: Record<string, string | undefined>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) sp.set(k, v);
  });
  const qs = sp.toString();
  return qs ? `/agents?${qs}` : "/agents";
}

// SSR/ISR: Revalidate agents listing every hour.
export const revalidate = 3600;

export function generateMetadata(): Metadata {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
  const canonical = siteUrl ? new URL("/agents/", siteUrl).toString() : undefined;
  return {
    alternates: canonical ? { canonical } : undefined,
    robots: { index: true, follow: true },
  };
}

export default async function AgentsPage({
  searchParams,
}: {
  searchParams?: SearchParams;
}) {
  const isStaticExport = (process.env.NEXT_OUTPUT || "").toLowerCase() === "export";
  if (isStaticExport) {
    const allAgents = await loadRepoAgents().catch(() => [] as Agent[]);
    const filters = computeFiltersFromAgents(allAgents);
    return <AgentsClient allAgents={allAgents} filters={filters} />;
  }

  const q = first(searchParams?.q);
  const category = first(searchParams?.category);
  const framework = first(searchParams?.framework);
  const provider = first(searchParams?.provider);
  const complexity = first(searchParams?.complexity);
  const localOnly = first(searchParams?.local_only) === "true";
  const page = Math.max(1, toInt(first(searchParams?.page) || "1", 1));
  const pageSize = Math.min(
    48,
    Math.max(6, toInt(first(searchParams?.page_size) || "24", 24)),
  );

  const [filtersData, agentsData] = await Promise.all([
    getFilters().catch(() => null),
    getAgents({
      q: q || undefined,
      category: category || undefined,
      framework: framework || undefined,
      provider: provider || undefined,
      complexity: complexity || undefined,
      local_only: localOnly,
      page,
      page_size: pageSize,
      sort: q ? undefined : "-stars",
    }).catch(() => ({
      items: [] as Agent[],
      total: 0,
      page,
      page_size: pageSize,
      query: q,
    })),
  ]);

  const filters: AgentFiltersResponse | null = filtersData;
  const agents = agentsData.items || [];
  const total = agentsData.total || 0;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const baseParams: Record<string, string | undefined> = {
    q: q || undefined,
    category: category || undefined,
    framework: framework || undefined,
    provider: provider || undefined,
    complexity: complexity || undefined,
    local_only: localOnly ? "true" : undefined,
    page_size: String(pageSize),
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10 space-y-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">Explore Agents</h1>
            <p className="text-muted-foreground">
              Search and filter across {total} agents
            </p>
          </div>
          <Button asChild variant="outline">
            <Link href="/">Back to Home</Link>
          </Button>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-lg">Search & Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <form action="/agents" method="get" className="grid gap-3 md:grid-cols-12">
              <input type="hidden" name="page" value="1" />
              <input type="hidden" name="page_size" value={String(pageSize)} />

              <div className="md:col-span-5">
                <Input
                  name="q"
                  defaultValue={q}
                  placeholder="Search agents… (e.g. pdf chatbot, rag, coding)"
                />
              </div>

              <div className="md:col-span-2">
                <select
                  name="category"
                  defaultValue={category}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">All categories</option>
                  {(filters?.categories || []).map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <select
                  name="framework"
                  defaultValue={framework}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">All frameworks</option>
                  {(filters?.frameworks || []).map((f) => (
                    <option key={f} value={f}>
                      {f}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-2">
                <select
                  name="provider"
                  defaultValue={provider}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">All providers</option>
                  {(filters?.providers || []).map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-1">
                <select
                  name="complexity"
                  defaultValue={complexity}
                  className="h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">Any</option>
                  {(filters?.complexities || ["beginner", "intermediate", "advanced"]).map((c) => (
                    <option key={c} value={String(c)}>
                      {String(c)}
                    </option>
                  ))}
                </select>
              </div>

              <div className="md:col-span-12 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    name="local_only"
                    value="true"
                    defaultChecked={localOnly}
                    className="h-4 w-4"
                  />
                  Local models only
                </label>
                <div className="flex gap-2">
                  <Button type="submit">Apply</Button>
                  <Button asChild type="button" variant="outline">
                    <Link href="/agents">Reset</Link>
                  </Button>
                </div>
              </div>
            </form>
          </CardContent>
        </Card>

        <AgentGrid agents={agents} />

        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button asChild variant="outline" disabled={page <= 1}>
              <Link
                href={
                  page > 1
                    ? buildUrl({ ...baseParams, page: String(page - 1) })
                    : "#"
                }
                aria-disabled={page <= 1}
              >
                ← Prev
              </Link>
            </Button>
            <Button asChild variant="outline" disabled={page >= totalPages}>
              <Link
                href={
                  page < totalPages
                    ? buildUrl({ ...baseParams, page: String(page + 1) })
                    : "#"
                }
                aria-disabled={page >= totalPages}
              >
                Next →
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </main>
  );
}
