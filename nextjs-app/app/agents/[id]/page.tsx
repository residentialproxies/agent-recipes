import { notFound } from "next/navigation";
import Link from "next/link";
import { getAgent } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Metadata } from "next";
import {
  ArrowLeft,
  ExternalLink,
  Star,
  GitFork,
  Calendar,
  Code2,
  Cpu,
} from "lucide-react";
import { getCategoryColor, getComplexityBadge, formatDate } from "@/lib/utils";

export const revalidate = 3600;

interface PageProps {
  params: {
    id: string;
  };
}

export async function generateMetadata({
  params,
}: PageProps): Promise<Metadata> {
  try {
    const agent = await getAgent(params.id);
    const title = `${agent.name} | Agent Navigator`;
    const description =
      (agent.description || "").trim() ||
      `Explore ${agent.name}: an LLM agent example (${agent.category}).`;

    return {
      title,
      description,
      alternates: { canonical: `/agents/${agent.id}` },
      openGraph: {
        title,
        description,
        type: "article",
        url: `/agents/${agent.id}`,
      },
    };
  } catch {
    return {
      title: "Agent not found | Agent Navigator",
      description: "This agent could not be found.",
    };
  }
}

export default async function AgentDetailPage({ params }: PageProps) {
  let agent;

  try {
    agent = await getAgent(params.id);
  } catch (error) {
    notFound();
  }

  const complexityBadge = getComplexityBadge(agent.complexity);
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "SoftwareSourceCode",
    name: agent.name,
    description: agent.description,
    codeRepository: agent.github_url,
    programmingLanguage: (agent.languages || [])[0],
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <script
        type="application/ld+json"
        // eslint-disable-next-line react/no-danger
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div className="container mx-auto px-4 py-8">
        {/* Back button */}
        <Button asChild variant="ghost" className="mb-6">
          <Link href="/agents">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Agents
          </Link>
        </Button>

        {/* Header */}
        <div className="mb-8">
          <div
            className={`mb-4 h-1 w-20 ${getCategoryColor(agent.category)}`}
          />

          <div className="mb-4 flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="mb-2 text-4xl font-bold">{agent.name}</h1>
              {agent.tagline && (
                <p className="text-xl text-muted-foreground">{agent.tagline}</p>
              )}
            </div>

            <div className="flex gap-2">
              <Button asChild>
                <a
                  href={agent.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="mr-2 h-4 w-4" />
                  View on GitHub
                </a>
              </Button>
            </div>
          </div>

          {/* Badges */}
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className={complexityBadge.color}>
              {complexityBadge.label}
            </Badge>
            <Badge variant="outline">{agent.category}</Badge>
            {agent.supports_local_models && (
              <Badge variant="secondary">Local models</Badge>
            )}
            {agent.requires_gpu && <Badge variant="secondary">GPU</Badge>}
            {agent.stars !== undefined && agent.stars !== null && (
              <Badge variant="outline">
                <Star className="mr-1 h-3 w-3 fill-yellow-400 text-yellow-400" />
                {agent.stars} stars
              </Badge>
            )}
            <Badge variant="outline">
              <Calendar className="mr-1 h-3 w-3" />
              Updated{" "}
              {agent.updated_at ? formatDate(agent.updated_at) : "Unknown"}
            </Badge>
          </div>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Description */}
            <Card>
              <CardHeader>
                <CardTitle>About</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-lg leading-relaxed text-muted-foreground">
                  {agent.description || "No description available."}
                </p>
              </CardContent>
            </Card>

            {/* Quick Start */}
            {(agent.clone_command || agent.quick_start) && (
              <Card>
                <CardHeader>
                  <CardTitle>Quick Start</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {agent.clone_command && (
                    <div>
                      <p className="mb-2 text-sm font-medium">Clone</p>
                      <pre className="overflow-x-auto rounded-md bg-slate-950 p-4 text-sm text-slate-50">
                        <code>{agent.clone_command}</code>
                      </pre>
                    </div>
                  )}
                  {agent.quick_start && (
                    <div>
                      <p className="mb-2 text-sm font-medium">Run</p>
                      <pre className="overflow-x-auto rounded-md bg-slate-950 p-4 text-sm text-slate-50">
                        <code>{agent.quick_start}</code>
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Use Case */}
            {agent.use_case && (
              <Card>
                <CardHeader>
                  <CardTitle>Use Case</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-muted-foreground">{agent.use_case}</p>
                </CardContent>
              </Card>
            )}

            {/* Tags */}
            {agent.tags && agent.tags.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Tags</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {agent.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Frameworks */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Code2 className="h-5 w-5" />
                  Frameworks
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(agent.frameworks || []).length > 0 ? (
                  <div className="space-y-2">
                    {(agent.frameworks || []).map((framework) => (
                      <div
                        key={framework}
                        className="rounded-md bg-slate-100 px-3 py-2 text-sm font-medium"
                      >
                        {framework}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No frameworks specified
                  </p>
                )}
              </CardContent>
            </Card>

            {/* LLM Providers */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cpu className="h-5 w-5" />
                  LLM Providers
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(agent.llm_providers || []).length > 0 ? (
                  <div className="space-y-2">
                    {(agent.llm_providers || []).map((provider) => (
                      <div
                        key={provider}
                        className="rounded-md bg-slate-100 px-3 py-2 text-sm font-medium capitalize"
                      >
                        {provider}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">
                    No providers specified
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card>
              <CardHeader>
                <CardTitle>Quick Links</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <Button
                  asChild
                  variant="outline"
                  className="w-full justify-start"
                >
                  <a
                    href={agent.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <GitFork className="mr-2 h-4 w-4" />
                    View Source Code
                  </a>
                </Button>
                {agent.codespaces_url && (
                  <Button
                    asChild
                    variant="outline"
                    className="w-full justify-start"
                  >
                    <a
                      href={agent.codespaces_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open in Codespaces
                    </a>
                  </Button>
                )}
                {agent.colab_url && (
                  <Button
                    asChild
                    variant="outline"
                    className="w-full justify-start"
                  >
                    <a
                      href={agent.colab_url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      Open in Colab
                    </a>
                  </Button>
                )}
                {agent.readme_relpath && (
                  <Button
                    asChild
                    variant="outline"
                    className="w-full justify-start"
                  >
                    <a
                      href={`${agent.github_url}/blob/main/${agent.readme_relpath}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      <ExternalLink className="mr-2 h-4 w-4" />
                      View README
                    </a>
                  </Button>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
