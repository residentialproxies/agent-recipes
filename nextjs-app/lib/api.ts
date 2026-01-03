import type {
  Agent,
  AgentFiltersResponse,
  AgentSearchParams,
  AgentSearchResponse,
} from "@/types/agent";

const SERVER_API_BASE_URL =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";
const CLIENT_API_BASE_PATH = "/api";

function apiBaseUrl(): string {
  // Browser calls same-origin and relies on Next.js rewrites (`/api/* -> backend/*`).
  if (typeof window !== "undefined") return CLIENT_API_BASE_PATH;
  // Server Components call the backend directly (Node fetch needs absolute URLs).
  return SERVER_API_BASE_URL;
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

  const url = `${apiBaseUrl()}/v1/agents?${searchParams.toString()}`;

  const response = await fetch(url, {
    next: { revalidate: 3600 }, // Cache for 1 hour
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agents: ${await errorMessage(response)}`);
  }

  return response.json();
}

export async function getAgent(id: string): Promise<Agent> {
  const url = `${apiBaseUrl()}/v1/agents/${id}`;

  const response = await fetch(url, {
    next: { revalidate: 3600 },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch agent: ${await errorMessage(response)}`);
  }

  return response.json();
}

export async function getFilters(): Promise<AgentFiltersResponse> {
  const url = `${apiBaseUrl()}/v1/filters`;
  const response = await fetch(url, { next: { revalidate: 3600 } });
  if (!response.ok) {
    throw new Error(`Failed to fetch filters: ${await errorMessage(response)}`);
  }
  return response.json();
}

export async function getAIRecommendations(query: string): Promise<string> {
  const url = `${apiBaseUrl()}/v1/ai/select`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query }),
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(
      `Failed to get AI recommendations: ${await errorMessage(response)}`,
    );
  }

  const data = await response.json();
  return (
    data.text ||
    data.recommendation ||
    data.response ||
    "No recommendations available."
  );
}
