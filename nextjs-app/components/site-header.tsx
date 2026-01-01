import Link from "next/link";
import { Button } from "@/components/ui/button";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur">
      <div className="container mx-auto flex h-16 items-center justify-between px-4">
        <Link href="/" className="font-bold tracking-tight">
          Agent Navigator
        </Link>
        <nav className="flex items-center gap-2">
          <Button asChild variant="ghost">
            <Link href="/agents">Explore</Link>
          </Button>
          <Button asChild>
            <Link href="/agents?q=pdf">Find an Agent</Link>
          </Button>
        </nav>
      </div>
    </header>
  );
}
