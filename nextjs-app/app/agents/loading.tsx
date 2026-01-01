export default function LoadingAgents() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10">
        <div className="h-10 w-64 animate-pulse rounded-md bg-slate-200" />
        <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {Array.from({ length: 12 }).map((_, i) => (
            <div
              key={i}
              className="h-64 animate-pulse rounded-lg border bg-white"
            />
          ))}
        </div>
      </div>
    </main>
  );
}
