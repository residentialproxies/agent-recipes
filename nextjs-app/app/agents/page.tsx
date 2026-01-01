import type { Metadata } from "next";
import Link from "next/link";
import { getAgents, getFilters } from "@/lib/api";
import { AgentGrid } from "@/components/agent-grid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// ISR: Revalidate every hour (frequently updated content)
export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Explore Agents | Agent Navigator",
  description:
    "Browse and search 100+ LLM agent examples. Filter by category, framework, provider, and complexity.",
  alternates: { canonical: "/agents" },
  openGraph: {
    title: "Explore Agents | Agent Navigator",
    description:
      "Browse and search LLM agent examples. Filter by category, framework, provider, and complexity.",
    type: "website",
    url: "/agents",
  },
};

type SearchParams = Record<string, string | string[] | undefined>;

function first(value: string | string[] | undefined): string | undefined {
  if (Array.isArray(value)) return value[0];
  return value;
}

function buildQuery(params: Record<string, string | undefined>): string {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (!v) return;
    sp.set(k, v);
  });
  const qs = sp.toString();
  return qs ? `?${qs}` : "";
}

export default async function AgentsPage({
  searchParams,
}: {
  searchParams?: SearchParams;
}) {
  const sp = searchParams || {};
  const q = first(sp.q) || "";
  const category = first(sp.category) || "";
  const framework = first(sp.framework) || "";
  const provider = first(sp.provider) || "";
  const complexity = first(sp.complexity) || "";
  const localOnly = first(sp.local_only) === "true";

  const page = Math.max(1, Number.parseInt(first(sp.page) || "1", 10));
  const pageSize = Math.min(
    48,
    Math.max(6, Number.parseInt(first(sp.page_size) || "24", 10)),
  );

  const [filters, results] = await Promise.all([
    getFilters().catch(() => null),
    getAgents({
      q,
      category: category || undefined,
      framework: framework || undefined,
      provider: provider || undefined,
      complexity: complexity || undefined,
      local_only: localOnly,
      page,
      page_size: pageSize,
      sort: q ? undefined : "-stars",
    }).catch(() => ({
      query: q,
      total: 0,
      page,
      page_size: pageSize,
      items: [],
    })),
  ]);

  const totalPages = Math.max(1, Math.ceil(results.total / results.page_size));
  const prevPage = page > 1 ? page - 1 : null;
  const nextPage = page < totalPages ? page + 1 : null;

  const baseParams = {
    q: q || undefined,
    category: category || undefined,
    framework: framework || undefined,
    provider: provider || undefined,
    complexity: complexity || undefined,
    local_only: localOnly ? "true" : undefined,
    page_size: String(results.page_size),
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10 space-y-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-4xl font-bold tracking-tight">
              Explore Agents
            </h1>
            <p className="text-muted-foreground">
              Search and filter across {results.total} agents
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
            <form
              action="/agents"
              method="get"
              className="grid gap-3 md:grid-cols-12"
            >
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
                  {(
                    filters?.complexities || [
                      "beginner",
                      "intermediate",
                      "advanced",
                    ]
                  ).map((c) => (
                    <option key={c} value={c}>
                      {c}
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

        <AgentGrid agents={results.items} />

        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {results.page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button asChild variant="outline" disabled={!prevPage}>
              <Link
                aria-disabled={!prevPage}
                tabIndex={!prevPage ? -1 : 0}
                href={
                  prevPage
                    ? `/agents${buildQuery({ ...baseParams, page: String(prevPage) })}`
                    : "#"
                }
              >
                ← Prev
              </Link>
            </Button>
            <Button asChild variant="outline" disabled={!nextPage}>
              <Link
                aria-disabled={!nextPage}
                tabIndex={!nextPage ? -1 : 0}
                href={
                  nextPage
                    ? `/agents${buildQuery({ ...baseParams, page: String(nextPage) })}`
                    : "#"
                }
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
