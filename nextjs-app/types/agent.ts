export interface Agent {
  id: string;
  name: string;
  description: string;
  category: string;
  frameworks: string[];
  llm_providers: string[];
  complexity: string;
  design_pattern?: string;
  github_url: string;
  codespaces_url?: string;
  colab_url?: string | null;
  folder_path?: string;
  readme_relpath?: string;
  clone_command?: string;
  quick_start?: string;
  stars?: number | null;
  updated_at?: number | null;
  supports_local_models?: boolean;
  requires_gpu?: boolean;
  api_keys?: string[];
  languages?: string[];
  tagline?: string;
  use_case?: string;
  tags?: string[];
}

export type Complexity = "beginner" | "intermediate" | "advanced" | string;

export interface AgentFiltersResponse {
  categories: string[];
  capabilities: string[];
  frameworks: string[];
  providers: string[];
  pricings: string[];
  complexities: Complexity[];
}

export interface AgentSearchParams {
  q?: string;
  category?: string | string[];
  framework?: string | string[];
  provider?: string | string[];
  complexity?: Complexity | Complexity[];
  local_only?: boolean;
  page?: number;
  page_size?: number;
  sort?: string;
}

export interface AgentSearchResponse {
  query: string;
  total: number;
  page: number;
  page_size: number;
  items: Agent[];
}
