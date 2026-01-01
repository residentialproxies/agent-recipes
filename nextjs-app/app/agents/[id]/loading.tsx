export default function LoadingAgent() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10 space-y-6">
        <div className="h-10 w-96 animate-pulse rounded-md bg-slate-200" />
        <div className="grid gap-8 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-6">
            <div className="h-40 animate-pulse rounded-lg border bg-white" />
            <div className="h-40 animate-pulse rounded-lg border bg-white" />
          </div>
          <div className="space-y-6">
            <div className="h-40 animate-pulse rounded-lg border bg-white" />
            <div className="h-40 animate-pulse rounded-lg border bg-white" />
          </div>
        </div>
      </div>
    </main>
  );
}
