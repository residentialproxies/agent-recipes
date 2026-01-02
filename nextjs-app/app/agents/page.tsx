"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { getAgents, getFilters } from "@/lib/api";
import { AgentGrid } from "@/components/agent-grid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import type { Agent, FiltersResponse } from "@/types/agent";

export default function AgentsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();

  const [agents, setAgents] = useState<Agent[]>([]);
  const [filters, setFilters] = useState<FiltersResponse | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const q = searchParams.get("q") || "";
  const category = searchParams.get("category") || "";
  const framework = searchParams.get("framework") || "";
  const provider = searchParams.get("provider") || "";
  const complexity = searchParams.get("complexity") || "";
  const localOnly = searchParams.get("local_only") === "true";
  const page = Math.max(1, parseInt(searchParams.get("page") || "1", 10));
  const pageSize = Math.min(
    48,
    Math.max(6, parseInt(searchParams.get("page_size") || "24", 10)),
  );

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
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
          items: [],
          total: 0,
          page,
          page_size: pageSize,
          query: q,
        })),
      ]);
      setFilters(filtersData);
      setAgents(agentsData.items);
      setTotal(agentsData.total);
    } finally {
      setLoading(false);
    }
  }, [q, category, framework, provider, complexity, localOnly, page, pageSize]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const buildUrl = (params: Record<string, string | undefined>) => {
    const sp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v) sp.set(k, v);
    });
    const qs = sp.toString();
    return qs ? `/agents?${qs}` : "/agents";
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const params: Record<string, string | undefined> = {
      q: (formData.get("q") as string) || undefined,
      category: (formData.get("category") as string) || undefined,
      framework: (formData.get("framework") as string) || undefined,
      provider: (formData.get("provider") as string) || undefined,
      complexity: (formData.get("complexity") as string) || undefined,
      local_only: formData.get("local_only") ? "true" : undefined,
      page_size: String(pageSize),
    };
    router.push(buildUrl(params));
  };

  const baseParams = {
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
            <h1 className="text-4xl font-bold tracking-tight">
              Explore Agents
            </h1>
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
            <form
              onSubmit={handleSubmit}
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

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : (
          <AgentGrid agents={agents} />
        )}

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
