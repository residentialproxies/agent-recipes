"use client";

import { useMemo, useState } from "react";
import type { ConsultResponse } from "@/lib/api";
import { consult } from "@/lib/api";

export default function ConsultForm({
  capabilities,
}: {
  capabilities: string[];
}) {
  const [problem, setProblem] = useState("");
  const [capability, setCapability] = useState("");
  const [pricing, setPricing] = useState("");
  const [minScore, setMinScore] = useState("0");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ConsultResponse | null>(null);

  const canSubmit = useMemo(
    () => problem.trim().length > 0 && !loading,
    [problem, loading],
  );

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const out = await consult({
        problem,
        capability: capability || null,
        pricing: pricing || null,
        min_score: Number(minScore || 0),
        max_candidates: 50,
      });
      setResult(out);
    } catch (err: any) {
      setError(err?.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="section">
      <h2>Describe your task</h2>
      <p className="muted">
        WebManus will recommend 1–3 AI workers to automate it.
      </p>
      <form onSubmit={onSubmit} style={{ marginTop: 12 }}>
        <div style={{ marginBottom: 12 }}>
          <div className="label">Problem</div>
          <textarea
            className="input"
            rows={5}
            placeholder='e.g. "Every morning, summarize my emails and draft replies to the obvious ones."'
            value={problem}
            onChange={(e) => setProblem(e.target.value)}
          />
        </div>
        <div className="row" style={{ marginTop: 0 }}>
          <div>
            <div className="label">Capability</div>
            <select
              className="input"
              value={capability}
              onChange={(e) => setCapability(e.target.value)}
            >
              <option value="">Any</option>
              {capabilities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="label">Pricing</div>
            <select
              className="input"
              value={pricing}
              onChange={(e) => setPricing(e.target.value)}
            >
              <option value="">Any</option>
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
              value={minScore}
              onChange={(e) => setMinScore(e.target.value)}
            />
          </div>
          <div style={{ display: "flex", alignItems: "end" }}>
            <button className="cta" type="submit" disabled={!canSubmit}>
              {loading ? "Consulting…" : "Consult"}
            </button>
          </div>
        </div>
      </form>

      {error ? (
        <div className="error" style={{ marginTop: 14 }}>
          {error}
        </div>
      ) : null}

      {result ? (
        <div style={{ marginTop: 14 }}>
          <div className="label">Recommendations</div>
          {(result.recommendations || []).length ? (
            <div
              className="grid"
              style={{ gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}
            >
              {result.recommendations.map((r) => (
                <a
                  className="card"
                  key={r.slug}
                  href={`/workers/${encodeURIComponent(r.slug)}`}
                >
                  <h3>{r.name || r.slug}</h3>
                  <p>{r.tagline ? `${r.tagline} — ${r.reason}` : r.reason}</p>
                  <div className="meta">
                    <span className="pill">
                      match: {Math.round(r.match_score * 100)}%
                    </span>
                  </div>
                </a>
              ))}
            </div>
          ) : (
            <p className="muted">
              {result.no_match_suggestion || "No good match found."}
            </p>
          )}
        </div>
      ) : null}
    </div>
  );
}
