"use client";

import { useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";

import { AgentGrid } from "@/components/agent-grid";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Agent, AgentFiltersResponse } from "@/types/agent";

function clampInt(value: string, fallback: number, min: number, max: number): number {
  const n = Number(value);
  if (!Number.isFinite(n)) return fallback;
  const i = Math.floor(n);
  return Math.min(max, Math.max(min, i));
}

function haystack(a: Agent): string {
  return [
    a.name,
    a.description,
    a.tagline,
    a.category,
    ...(a.frameworks || []),
    ...(a.llm_providers || []),
    ...(a.tags || []),
    ...(a.languages || []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function buildUrl(params: Record<string, string | undefined>) {
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v) sp.set(k, v);
  });
  const qs = sp.toString();
  return qs ? `/agents?${qs}` : "/agents";
}

export default function AgentsClient({
  allAgents,
  filters,
}: {
  allAgents: Agent[];
  filters: AgentFiltersResponse;
}) {
  const searchParams = useSearchParams();
  const router = useRouter();

  const q = searchParams.get("q") || "";
  const category = searchParams.get("category") || "";
  const framework = searchParams.get("framework") || "";
  const provider = searchParams.get("provider") || "";
  const complexity = searchParams.get("complexity") || "";
  const localOnly = searchParams.get("local_only") === "true";
  const page = clampInt(searchParams.get("page") || "1", 1, 1, 10000);
  const pageSize = clampInt(searchParams.get("page_size") || "24", 24, 6, 48);

  const { items, total } = useMemo(() => {
    const qNorm = q.trim().toLowerCase();
    const out: Agent[] = [];

    for (const a of allAgents) {
      if (category && a.category !== category) continue;
      if (framework && !(a.frameworks || []).includes(framework)) continue;
      if (provider && !(a.llm_providers || []).includes(provider)) continue;
      if (complexity && a.complexity !== complexity) continue;
      if (localOnly && !a.supports_local_models) continue;

      if (qNorm) {
        if (!haystack(a).includes(qNorm)) continue;
      }

      out.push(a);
    }

    if (!qNorm) {
      out.sort((a, b) => (Number(b.stars || 0) - Number(a.stars || 0)));
    } else {
      out.sort((a, b) => a.name.localeCompare(b.name));
    }

    return { items: out, total: out.length };
  }, [allAgents, q, category, framework, provider, complexity, localOnly]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  const pageItems = items.slice(start, start + pageSize);

  const baseParams: Record<string, string | undefined> = {
    q: q || undefined,
    category: category || undefined,
    framework: framework || undefined,
    provider: provider || undefined,
    complexity: complexity || undefined,
    local_only: localOnly ? "true" : undefined,
    page_size: String(pageSize),
  };

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
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
      page: "1",
    };
    router.push(buildUrl(params));
  }

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
            <form onSubmit={onSubmit} className="grid gap-3 md:grid-cols-12">
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
                  {(filters.categories || []).map((c) => (
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
                  {(filters.frameworks || []).map((f) => (
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
                  {(filters.providers || []).map((p) => (
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
                  {(filters.complexities || ["beginner", "intermediate", "advanced"]).map((c) => (
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

        <AgentGrid agents={pageItems} />

        <div className="flex items-center justify-between">
          <div className="text-sm text-muted-foreground">
            Page {safePage} of {totalPages}
          </div>
          <div className="flex gap-2">
            <Button asChild variant="outline" disabled={safePage <= 1}>
              <Link
                href={
                  safePage > 1
                    ? buildUrl({ ...baseParams, page: String(safePage - 1) })
                    : "#"
                }
                aria-disabled={safePage <= 1}
              >
                ← Prev
              </Link>
            </Button>
            <Button asChild variant="outline" disabled={safePage >= totalPages}>
              <Link
                href={
                  safePage < totalPages
                    ? buildUrl({ ...baseParams, page: String(safePage + 1) })
                    : "#"
                }
                aria-disabled={safePage >= totalPages}
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

