import fs from "node:fs/promises";
import path from "node:path";

import type { Agent, AgentFiltersResponse } from "@/types/agent";

let agentsPromise: Promise<Agent[]> | null = null;

function repoAgentsPath(): string {
  // `process.cwd()` is `nextjs-app/` during Next builds.
  return path.join(process.cwd(), "..", "data", "agents.json");
}

function normalizeAgent(raw: Partial<Agent>): Agent {
  return {
    id: raw.id || "",
    name: raw.name || "Untitled",
    description: raw.description || "",
    category: raw.category || "other",
    frameworks: Array.isArray(raw.frameworks) ? raw.frameworks : [],
    llm_providers: Array.isArray(raw.llm_providers) ? raw.llm_providers : [],
    complexity: raw.complexity || "intermediate",
    github_url: raw.github_url || "",
    design_pattern: raw.design_pattern,
    codespaces_url: raw.codespaces_url,
    colab_url: raw.colab_url,
    folder_path: raw.folder_path,
    readme_relpath: raw.readme_relpath,
    clone_command: raw.clone_command,
    quick_start: raw.quick_start,
    stars: raw.stars ?? null,
    updated_at: raw.updated_at ?? null,
    supports_local_models: raw.supports_local_models,
    requires_gpu: raw.requires_gpu,
    api_keys: raw.api_keys,
    languages: raw.languages,
    tagline: raw.tagline,
    use_case: raw.use_case,
    tags: raw.tags,
  };
}

export async function loadRepoAgents(): Promise<Agent[]> {
  if (!agentsPromise) {
    agentsPromise = (async () => {
      const filePath = repoAgentsPath();
      const content = await fs.readFile(filePath, "utf8");
      const parsed = JSON.parse(content);
      const items: unknown[] = Array.isArray(parsed) ? parsed : [];
      return items
        .map((a) => normalizeAgent(a as Partial<Agent>))
        .filter((a) => Boolean(a.id));
    })();
  }
  return agentsPromise;
}

export async function loadRepoAgentIds(): Promise<string[]> {
  const agents = await loadRepoAgents();
  return agents.map((a) => a.id).filter(Boolean);
}

export async function loadRepoAgentById(id: string): Promise<Agent | null> {
  const agents = await loadRepoAgents();
  return agents.find((a) => a.id === id) || null;
}

export function computeFiltersFromAgents(
  agents: Agent[],
): AgentFiltersResponse {
  const categories = new Set<string>();
  const frameworks = new Set<string>();
  const providers = new Set<string>();
  const complexities = new Set<string>();

  for (const a of agents) {
    if (a.category) categories.add(a.category);
    for (const f of a.frameworks || []) frameworks.add(f);
    for (const p of a.llm_providers || []) providers.add(p);
    if (a.complexity) complexities.add(a.complexity);
  }

  return {
    categories: Array.from(categories).sort(),
    capabilities: [],
    frameworks: Array.from(frameworks).sort(),
    providers: Array.from(providers).sort(),
    pricings: [],
    complexities: Array.from(complexities).sort(),
  };
}
