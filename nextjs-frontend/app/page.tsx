import { fetchCapabilities, fetchWorkers } from "@/lib/api";

type SearchParams = {
  q?: string;
  capability?: string;
  pricing?: string;
  min_score?: string;
  page?: string;
};

export default async function Home({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const sp = (await searchParams) || {};
  const q = sp.q || "";
  const capability = sp.capability || "";
  const pricing = sp.pricing || "";
  const min_score = sp.min_score || "0";
  const pageSize = 30;
  const requestedPageRaw = Number(sp.page || "1");
  const requestedPage =
    Number.isFinite(requestedPageRaw) && requestedPageRaw > 0
      ? Math.floor(requestedPageRaw)
      : 1;

  const [caps, workers0] = await Promise.all([
    fetchCapabilities().catch(() => [] as string[]),
    fetchWorkers({
      q,
      capability,
      pricing,
      min_score,
      limit: String(pageSize),
      offset: String((requestedPage - 1) * pageSize),
    }).catch(() => ({ total: 0, items: [] })),
  ]);

  const totalPages0 = Math.max(1, Math.ceil((workers0.total || 0) / pageSize));
  const page = Math.min(requestedPage, totalPages0);
  const workers =
    page === requestedPage
      ? workers0
      : await fetchWorkers({
          q,
          capability,
          pricing,
          min_score,
          limit: String(pageSize),
          offset: String((page - 1) * pageSize),
        }).catch(() => ({ total: 0, items: [] }));

  const totalPages = Math.max(1, Math.ceil((workers.total || 0) / pageSize));

  function pageHref(p: number): string {
    const usp = new URLSearchParams();
    if (q) usp.set("q", q);
    if (capability) usp.set("capability", capability);
    if (pricing) usp.set("pricing", pricing);
    if (min_score && min_score !== "0") usp.set("min_score", min_score);
    if (p > 1) usp.set("page", String(p));
    const qs = usp.toString();
    return qs ? `/?${qs}` : "/";
  }

  return (
    <>
      <div className="hero">
        <h1>AI Workers for Real Work</h1>
        <p>
          Search and filter WebManus “workers” by capability, pricing, and
          automation score. Use <a href="/consult">Consult</a> to get 1–3
          recommendations for your task.
        </p>

        <form className="row" action="/" method="get">
          <input type="hidden" name="page" value="1" />
          <div>
            <div className="label">Search</div>
            <input
              className="input"
              name="q"
              placeholder="e.g. email triage, customer support, research..."
              defaultValue={q}
            />
          </div>
          <div>
            <div className="label">Capability</div>
            <select
              className="input"
              name="capability"
              defaultValue={capability}
            >
              <option value="">All</option>
              {caps.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="label">Pricing</div>
            <select className="input" name="pricing" defaultValue={pricing}>
              <option value="">All</option>
              <option value="free">free</option>
              <option value="freemium">freemium</option>
              <option value="paid">paid</option>
              <option value="enterprise">enterprise</option>
            </select>
          </div>
          <div>
            <div className="label">Min score</div>
            <input
              className="input"
              name="min_score"
              defaultValue={min_score}
            />
          </div>
        </form>
      </div>

      <div className="section">
        <h2>
          Workers <span className="muted">({workers.total})</span>
        </h2>
        {workers.items.length ? (
          <div className="grid">
            {workers.items.map((w) => (
              <a
                className="card"
                key={w.slug}
                href={`/workers/${encodeURIComponent(w.slug)}`}
              >
                <h3>{w.name}</h3>
                <p>{w.tagline || "—"}</p>
                <div className="meta">
                  <span className="pill">
                    pricing: {w.pricing || "freemium"}
                  </span>
                  <span className="pill">
                    score:{" "}
                    {typeof w.labor_score === "number"
                      ? w.labor_score.toFixed(1)
                      : "—"}
                  </span>
                  {(w.capabilities || []).slice(0, 2).map((c) => (
                    <span key={c} className="pill">
                      {c}
                    </span>
                  ))}
                </div>
              </a>
            ))}
          </div>
        ) : (
          <p className="muted" style={{ marginTop: 12 }}>
            No workers found. Try broadening your search.
          </p>
        )}

        <div
          style={{
            marginTop: 16,
            display: "flex",
            gap: 10,
            alignItems: "center",
            flexWrap: "wrap",
          }}
        >
          {page > 1 ? (
            <a className="cta" href={pageHref(page - 1)}>
              ← Prev
            </a>
          ) : (
            <span className="cta disabled" aria-disabled="true">
              ← Prev
            </span>
          )}
          <span className="muted">
            Page {page} / {totalPages}
          </span>
          {page < totalPages ? (
            <a className="cta" href={pageHref(page + 1)}>
              Next →
            </a>
          ) : (
            <span className="cta disabled" aria-disabled="true">
              Next →
            </span>
          )}
        </div>
      </div>
    </>
  );
}
