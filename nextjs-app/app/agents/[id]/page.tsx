import type { Metadata } from "next";
import { notFound } from "next/navigation";

import AgentDetail from "./agent-detail";
import { getAgent } from "@/lib/api.server";
import { loadRepoAgentById, loadRepoAgentIds } from "@/lib/repo-agents";
import type { Agent } from "@/types/agent";

export const revalidate = 3600;

export async function generateStaticParams(): Promise<{ id: string }[]> {
  const isStaticExport =
    (process.env.NEXT_OUTPUT || "").toLowerCase() === "export";
  if (!isStaticExport) return [];

  const ids = await loadRepoAgentIds().catch(() => [] as string[]);
  return ids.map((id) => ({ id }));
}

async function loadAgent(id: string): Promise<Agent | null> {
  const isStaticExport =
    (process.env.NEXT_OUTPUT || "").toLowerCase() === "export";
  if (isStaticExport) return loadRepoAgentById(id).catch(() => null);
  return getAgent(id).catch(() => null);
}

export async function generateMetadata({
  params,
}: {
  params: { id: string };
}): Promise<Metadata> {
  const id = params.id;
  const agent = await loadAgent(id);

  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
  const canonical = siteUrl
    ? new URL(`/agents/${encodeURIComponent(id)}`, siteUrl).toString()
    : undefined;

  if (!agent) {
    return {
      title: "Agent Not Found | Agent Navigator",
      robots: { index: false, follow: false },
      alternates: canonical ? { canonical } : undefined,
    };
  }

  const title = `${agent.name} | Agent Navigator`;
  const description =
    agent.description || "Discover production-ready LLM agent examples.";

  return {
    title,
    description,
    alternates: canonical ? { canonical } : undefined,
    openGraph: {
      title,
      description,
      type: "article",
      url: canonical,
    },
    twitter: {
      card: "summary",
      title,
      description,
    },
  };
}

export default async function AgentDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const agent = await loadAgent(params.id);
  if (!agent) notFound();
  return <AgentDetail agent={agent} />;
}
