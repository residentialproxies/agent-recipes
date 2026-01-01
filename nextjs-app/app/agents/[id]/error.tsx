"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function AgentError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10 space-y-4">
        <h1 className="text-2xl font-bold">Couldn’t load this agent</h1>
        <p className="text-muted-foreground">{error.message}</p>
        <div className="flex gap-2">
          <Button onClick={() => reset()}>Retry</Button>
          <Button asChild variant="outline">
            <Link href="/agents">Back to agents</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
