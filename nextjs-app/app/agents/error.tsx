"use client";

export default function AgentsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-10 space-y-4">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="text-muted-foreground">{error.message}</p>
        <button
          onClick={() => reset()}
          className="rounded-md bg-black px-4 py-2 text-white"
        >
          Try again
        </button>
      </div>
    </main>
  );
}
