export type Worker = {
  slug: string;
  name: string;
  tagline?: string | null;
  pricing?: string | null;
  labor_score?: number | null;
  browser_native?: boolean | null;
  website?: string | null;
  affiliate_url?: string | null;
  logo_url?: string | null;
  source_url?: string | null;
  capabilities?: string[];
};

export type WorkersResponse = {
  total: number;
  items: Worker[];
};

export type ConsultRequest = {
  problem: string;
  max_candidates?: number;
  capability?: string | null;
  pricing?: string | null;
  min_score?: number;
};

export type ConsultResponse = {
  recommendations: {
    slug: string;
    match_score: number;
    reason: string;
    name?: string | null;
    tagline?: string | null;
  }[];
  no_match_suggestion: string;
};

function apiBaseUrl(): string {
  return (
    process.env.API_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    "http://localhost:8000"
  );
}

export async function fetchWorkers(params: {
  q?: string;
  capability?: string;
  pricing?: string;
  min_score?: string;
  limit?: string;
  offset?: string;
}): Promise<WorkersResponse> {
  const usp = new URLSearchParams();
  if (params.q) usp.set("q", params.q);
  if (params.capability) usp.set("capability", params.capability);
  if (params.pricing) usp.set("pricing", params.pricing);
  if (params.min_score) usp.set("min_score", params.min_score);
  if (params.limit) usp.set("limit", params.limit);
  if (params.offset) usp.set("offset", params.offset);
  const url = `${apiBaseUrl()}/v1/workers?${usp.toString()}`;

  const res = await fetch(url, { next: { revalidate: 300 } });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchWorker(slug: string): Promise<Worker | null> {
  const res = await fetch(
    `${apiBaseUrl()}/v1/workers/${encodeURIComponent(slug)}`,
    {
      next: { revalidate: 300 },
    },
  );
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Not found (${res.status})`);
  return res.json();
}

export async function fetchCapabilities(): Promise<string[]> {
  const res = await fetch(`${apiBaseUrl()}/v1/capabilities`, {
    next: { revalidate: 3600 },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function consult(body: ConsultRequest): Promise<ConsultResponse> {
  const res = await fetch(`${apiBaseUrl()}/v1/consult`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = "";
    try {
      detail = JSON.stringify(await res.json());
    } catch {}
    throw new Error(`Consult failed (${res.status}) ${detail}`);
  }
  return res.json();
}
