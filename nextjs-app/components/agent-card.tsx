import Link from "next/link";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Star, Code2 } from "lucide-react";
import type { Agent } from "@/types/agent";
import { getCategoryColor, getComplexityBadge } from "@/lib/utils";

interface AgentCardProps {
  agent: Agent;
}

export function AgentCard({ agent }: AgentCardProps) {
  const complexityBadge = getComplexityBadge(agent.complexity);

  return (
    <Card className="group flex h-full flex-col transition-all hover:shadow-lg">
      {/* Header with category indicator */}
      <div className={`h-2 ${getCategoryColor(agent.category)}`} />

      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="truncate text-xl font-bold group-hover:text-purple-600">
              {agent.name}
            </h3>
            {agent.tagline && (
              <p className="mt-1 text-sm text-muted-foreground line-clamp-1">
                {agent.tagline}
              </p>
            )}
          </div>
          {agent.stars !== undefined && agent.stars !== null && (
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
              <span>{agent.stars}</span>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent className="flex-1 pb-3">
        <p className="mb-4 text-sm text-muted-foreground line-clamp-3">
          {agent.description || "No description available."}
        </p>

        {/* Tags */}
        <div className="mb-3 flex flex-wrap gap-1.5">
          <Badge variant="outline" className={complexityBadge.color}>
            {complexityBadge.label}
          </Badge>
          <Badge variant="outline">{agent.category}</Badge>
        </div>

        {/* Frameworks */}
        {agent.frameworks.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {agent.frameworks.slice(0, 3).map((framework) => (
              <Badge key={framework} variant="secondary" className="text-xs">
                <Code2 className="mr-1 h-3 w-3" />
                {framework}
              </Badge>
            ))}
            {agent.frameworks.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{agent.frameworks.length - 3}
              </Badge>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="gap-2 pt-0">
        <Button asChild className="flex-1" variant="outline">
          <Link href={`/agents/${agent.id}`}>View Details</Link>
        </Button>
        <Button asChild size="icon" variant="ghost">
          <a
            href={agent.github_url}
            target="_blank"
            rel="noopener noreferrer"
            title="View on GitHub"
          >
            <ExternalLink className="h-4 w-4" />
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}
