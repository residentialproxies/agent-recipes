export default function Loading() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-24">
        <div className="h-10 w-80 animate-pulse rounded-md bg-slate-200" />
        <div className="mt-6 h-6 w-64 animate-pulse rounded-md bg-slate-200" />
      </div>
    </main>
  );
}
