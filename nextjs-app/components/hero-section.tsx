import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";
import { getAgents, getFilters } from "@/lib/api";

export async function HeroSection() {
  const [agentsRes, filters] = await Promise.all([
    getAgents({ page: 1, page_size: 1 }).catch(() => ({
      query: "",
      total: 0,
      page: 1,
      page_size: 1,
      items: [],
    })),
    getFilters().catch(() => null),
  ]);

  const total = agentsRes.total ?? 0;
  const frameworksCount = filters?.frameworks?.length ?? 0;
  const categoriesCount = filters?.categories?.length ?? 0;

  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-grid-white/[0.05] bg-[size:20px_20px]" />

      <div className="container relative mx-auto px-4 py-20 sm:py-28">
        <div className="mx-auto max-w-4xl text-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-sm backdrop-blur-sm">
            <Sparkles className="h-4 w-4 text-purple-400" />
            <span>100+ Production-Ready Agent Examples</span>
          </div>

          {/* Main heading */}
          <h1 className="mb-6 text-5xl font-extrabold tracking-tight sm:text-6xl lg:text-7xl">
            Navigate the World of{" "}
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Agents
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mb-10 text-xl text-slate-300 sm:text-2xl">
            Don&apos;t know which AI tool to use? Browse our curated index or
            let our AI Concierge pick the perfect one for you.
          </p>

          {/* CTA buttons */}
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              asChild
              size="lg"
              className="group min-w-[200px] bg-purple-600 text-white hover:bg-purple-700"
            >
              <Link href="/agents">
                Explore Agents
                <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button
              asChild
              size="lg"
              variant="outline"
              className="min-w-[200px] border-white/20 bg-white/5 text-white hover:bg-white/10"
            >
              <Link href="/#ai-concierge">Ask AI Assistant</Link>
            </Button>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-2 gap-8 sm:grid-cols-4">
            {[
              { label: "Agents", value: `${total}` },
              { label: "Frameworks", value: `${frameworksCount}` },
              { label: "Categories", value: `${categoriesCount}` },
              { label: "Updated", value: "Hourly" },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold text-purple-400">
                  {stat.value}
                </div>
                <div className="text-sm text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom gradient fade */}
      <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-background to-transparent" />
    </section>
  );
}
