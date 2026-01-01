import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-24 text-center space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">Page not found</h1>
        <p className="text-muted-foreground">
          The page you’re looking for doesn’t exist.
        </p>
        <div className="flex justify-center gap-2">
          <Button asChild>
            <Link href="/">Home</Link>
          </Button>
          <Button asChild variant="outline">
            <Link href="/agents">Explore agents</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}
