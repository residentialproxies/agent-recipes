import type { Metadata } from "next";
import { HeroSection } from "@/components/hero-section";
import { AIConciergeCTA } from "@/components/ai-concierge";
import { AgentGrid } from "@/components/agent-grid";
import { getAgents } from "@/lib/api";
import { Button } from "@/components/ui/button";
import Link from "next/link";

// ISR: Revalidate every hour (home page with trending content)
export const revalidate = 3600;

export function generateMetadata(): Metadata {
  const siteUrl = process.env.NEXT_PUBLIC_SITE_URL;
  const canonical = siteUrl ? new URL("/", siteUrl).toString() : undefined;
  return {
    alternates: canonical ? { canonical } : undefined,
  };
}

export default async function HomePage() {
  // Fetch trending agents (latest 12)
  const { items } = await getAgents({ page_size: 12, sort: "-stars" }).catch(
    () => ({
      query: "",
      total: 0,
      page: 1,
      page_size: 12,
      items: [],
    }),
  );

  return (
    <main className="min-h-screen">
      <HeroSection />

      <div className="container mx-auto px-4 py-12 space-y-12">
        {/* AI Concierge Section */}
        <section id="ai-concierge">
          <AIConciergeCTA />
        </section>

        {/* Trending Agents Section */}
        <section>
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold tracking-tight">
                Trending Agents
              </h2>
              <p className="text-muted-foreground">
                Recently added and popular agent examples
              </p>
            </div>
            <Button asChild variant="outline">
              <Link href="/agents">View All →</Link>
            </Button>
          </div>

          <AgentGrid agents={items} />
        </section>

        {/* Categories Section */}
        <section className="py-12">
          <h2 className="mb-8 text-center text-3xl font-bold tracking-tight">
            Browse by Category
          </h2>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              {
                name: "RAG",
                value: "rag",
                emoji: "📚",
                description: "Retrieval Augmented Generation",
                color: "from-blue-500 to-cyan-500",
              },
              {
                name: "Chatbots",
                value: "chatbot",
                emoji: "💬",
                description: "Conversational AI agents",
                color: "from-green-500 to-emerald-500",
              },
              {
                name: "Coding",
                value: "coding",
                emoji: "💻",
                description: "Code generation & analysis",
                color: "from-amber-500 to-orange-500",
              },
              {
                name: "Research",
                value: "research",
                emoji: "🔬",
                description: "Research & analysis agents",
                color: "from-violet-500 to-purple-500",
              },
            ].map((category) => (
              <Link
                key={category.name}
                href={`/agents?category=${category.value}`}
                className="group relative overflow-hidden rounded-lg border p-6 transition-all hover:shadow-lg"
              >
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${category.color} opacity-0 transition-opacity group-hover:opacity-10`}
                />
                <div className="relative">
                  <div className="mb-3 text-4xl">{category.emoji}</div>
                  <h3 className="mb-1 font-semibold">{category.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    {category.description}
                  </p>
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Footer CTA */}
        <section className="rounded-2xl bg-gradient-to-br from-purple-600 to-pink-600 p-12 text-center text-white">
          <h2 className="mb-4 text-3xl font-bold">
            Ready to Build Your Agent?
          </h2>
          <p className="mb-6 text-lg text-purple-100">
            Explore our full catalog of 100+ agent examples and start building
            today
          </p>
          <Button
            asChild
            size="lg"
            className="bg-white text-purple-600 hover:bg-purple-50"
          >
            <Link href="/agents">Explore All Agents</Link>
          </Button>
        </section>
      </div>
    </main>
  );
}
