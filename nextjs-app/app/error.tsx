"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-24 text-center space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">
          Something went wrong
        </h1>
        <p className="text-muted-foreground">{error.message}</p>
        <div className="flex justify-center gap-2">
          <Button onClick={() => reset()}>Retry</Button>
          <Button asChild variant="outline">
            <Link href="/">Home</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
