import "server-only";

import type {
  Agent,
  AgentFiltersResponse,
  AgentSearchParams,
  AgentSearchResponse,
} from "@/types/agent";
import {
  computeFiltersFromAgents,
  loadRepoAgentById,
  loadRepoAgents,
} from "@/lib/repo-agents";

const SERVER_API_BASE_URL =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

function shouldUseRepoDataFallback(): boolean {
  if ((process.env.NEXT_OUTPUT || "").toLowerCase() === "export") return true;
  if (process.env.NEXTJS_REPO_DATA === "1") return true;

  // Local builds often don't have the API running; prefer repo data when present.
  return /^https?:\/\/(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?$/i.test(
    (SERVER_API_BASE_URL || "").trim().replace(/\/$/, ""),
  );
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

async function errorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    const detail =
      (typeof data?.detail === "string" && data.detail) ||
      (typeof data?.error === "string" && data.error);
    if (detail) return detail;
  } catch {
    // ignore
  }
  return `${response.status} ${response.statusText}`.trim();
}

export async function getAgents(
  params: AgentSearchParams = {},
): Promise<AgentSearchResponse> {
  if (shouldUseRepoDataFallback()) {
    const allAgents = await loadRepoAgents().catch(() => [] as Agent[]);
    const q = (params.q || "").trim().toLowerCase();
    const category = Array.isArray(params.category)
      ? params.category[0]
      : params.category;
    const framework = Array.isArray(params.framework)
      ? params.framework[0]
      : params.framework;
    const provider = Array.isArray(params.provider)
      ? params.provider[0]
      : params.provider;
    const complexity = Array.isArray(params.complexity)
      ? params.complexity[0]
      : params.complexity;
    const localOnly = Boolean(params.local_only);

    let items = allAgents.filter((a) => {
      if (category && a.category !== category) return false;
      if (framework && !(a.frameworks || []).includes(framework)) return false;
      if (provider && !(a.llm_providers || []).includes(provider)) return false;
      if (complexity && a.complexity !== complexity) return false;
      if (localOnly && !a.supports_local_models) return false;
      if (q && !haystack(a).includes(q)) return false;
      return true;
    });

    if (params.sort === "-stars") {
      items = items.sort((a, b) => Number(b.stars || 0) - Number(a.stars || 0));
    } else {
      items = items.sort((a, b) => a.name.localeCompare(b.name));
    }

    const pageSize = params.page_size || 20;
    const page = params.page || 1;
    const start = (page - 1) * pageSize;
    const pageItems = items.slice(start, start + pageSize);

    return {
      query: params.q || "",
      total: items.length,
      page,
      page_size: pageSize,
      items: pageItems,
    };
  }

  const searchParams = new URLSearchParams();

  if (params.q) searchParams.set("q", params.q);

  if (params.category) {
    const categories = Array.isArray(params.category)
      ? params.category
      : [params.category];
    categories.forEach((c) => searchParams.append("category", c));
  }

  if (params.framework) {
    const frameworks = Array.isArray(params.framework)
      ? params.framework
      : [params.framework];
    frameworks.forEach((f) => searchParams.append("framework", f));
  }

  if (params.provider) {
    const providers = Array.isArray(params.provider)
      ? params.provider
      : [params.provider];
    providers.forEach((p) => searchParams.append("provider", p));
  }

  if (params.complexity) {
    const complexities = Array.isArray(params.complexity)
      ? params.complexity
      : [params.complexity];
    complexities.forEach((c) => searchParams.append("complexity", c));
  }

  if (params.local_only) searchParams.set("local_only", "true");
  if (params.page) searchParams.set("page", params.page.toString());
  if (params.page_size)
    searchParams.set("page_size", params.page_size.toString());
  if (params.sort) searchParams.set("sort", params.sort);

  const url = `${SERVER_API_BASE_URL}/v1/agents?${searchParams.toString()}`;

  const response = await fetch(url, {
    next: { revalidate: 3600 }, // Cache for 1 hour
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${await errorMessage(response)}`);
  }

  return response.json();
}

export async function getAgent(id: string): Promise<Agent> {
  if (shouldUseRepoDataFallback()) {
    const agent = await loadRepoAgentById(id).catch(() => null);
    if (!agent) throw new Error("Agent not found");
    return agent;
  }

  const url = `${SERVER_API_BASE_URL}/v1/agents/${id}`;

  const response = await fetch(url, {
    next: { revalidate: 3600 },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agent: ${await errorMessage(response)}`);
  }

  return response.json();
}

export async function getFilters(): Promise<AgentFiltersResponse> {
  if (shouldUseRepoDataFallback()) {
    const allAgents = await loadRepoAgents().catch(() => [] as Agent[]);
    return computeFiltersFromAgents(allAgents);
  }

  const url = `${SERVER_API_BASE_URL}/v1/filters`;
  const response = await fetch(url, { next: { revalidate: 3600 } });
  if (!response.ok) {
    throw new Error(`Failed to fetch filters: ${await errorMessage(response)}`);
  }
  return response.json();
}

