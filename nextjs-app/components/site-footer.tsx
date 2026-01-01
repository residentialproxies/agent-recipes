import Link from "next/link";

export function SiteFooter() {
  return (
    <footer className="border-t">
      <div className="container mx-auto flex flex-col gap-2 px-4 py-8 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
        <p>© {new Date().getFullYear()} Agent Navigator</p>
        <div className="flex gap-4">
          <Link href="/agents" className="hover:text-foreground">
            Browse
          </Link>
          <a href="/api/docs" className="hover:text-foreground">
            API Docs
          </a>
        </div>
      </div>
    </footer>
  );
}
