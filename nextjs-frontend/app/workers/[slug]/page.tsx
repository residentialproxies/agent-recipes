import { fetchWorker } from "@/lib/api";
import type { Metadata } from "next";
import { notFound } from "next/navigation";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const worker = await fetchWorker(slug).catch(() => null);

  const siteUrl =
    process.env.SITE_URL ||
    process.env.NEXT_PUBLIC_SITE_URL ||
    "http://localhost:3000";
  const canonicalUrl = `${siteUrl}/workers/${encodeURIComponent(slug)}`;
  const workerName = worker?.name || slug;
  const workerDesc =
    worker?.tagline || `WebManus worker profile for ${workerName}.`;

  return {
    title: `${workerName} — WebManus Worker`,
    description: workerDesc,
    keywords: [
      workerName,
      "AI worker",
      "AI agent",
      "automation",
      ...(worker?.capabilities || []).slice(0, 5),
    ].filter(Boolean),
    authors: [{ name: "WebManus" }],
    alternates: {
      canonical: canonicalUrl,
    },
    openGraph: {
      type: "website",
      siteName: "WebManus",
      title: `${workerName} — AI Worker`,
      description: workerDesc,
      url: canonicalUrl,
      images: worker?.logo_url
        ? [
            {
              url: worker.logo_url,
              width: 1200,
              height: 630,
              alt: `${workerName} logo`,
            },
          ]
        : [
            {
              url: `${siteUrl}/og-image.png`,
              width: 1200,
              height: 630,
              alt: "WebManus - AI Workers Directory",
            },
          ],
    },
    twitter: {
      card: "summary_large_image",
      site: "@webmanus",
      title: `${workerName} — AI Worker`,
      description: workerDesc,
      images: worker?.logo_url
        ? [worker.logo_url]
        : [`${siteUrl}/og-image.png`],
    },
    robots: {
      index: true,
      follow: true,
    },
  };
}

export default async function WorkerPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const worker = await fetchWorker(slug);
  if (!worker) notFound();

  return (
    <>
      <div className="hero">
        <h1>{worker.name}</h1>
        <p>{worker.tagline || "—"}</p>
        <div
          style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}
        >
          {worker.affiliate_url ? (
            <a
              className="cta"
              href={worker.affiliate_url}
              target="_blank"
              rel="noreferrer"
            >
              Visit (affiliate)
            </a>
          ) : null}
          {worker.website ? (
            <a
              className="cta"
              href={worker.website}
              target="_blank"
              rel="noreferrer"
            >
              Official site
            </a>
          ) : null}
          {worker.source_url ? (
            <a
              className="cta"
              href={worker.source_url}
              target="_blank"
              rel="noreferrer"
            >
              Source
            </a>
          ) : null}
        </div>
      </div>

      <div className="section">
        <h2>Overview</h2>
        <div className="meta">
          <span className="pill">pricing: {worker.pricing || "freemium"}</span>
          <span className="pill">
            score:{" "}
            {typeof worker.labor_score === "number"
              ? worker.labor_score.toFixed(1)
              : "—"}
          </span>
          <span className="pill">
            browser: {worker.browser_native ? "native" : "unknown"}
          </span>
        </div>
        <div style={{ marginTop: 12 }} className="meta">
          {(worker.capabilities || []).map((c) => (
            <span key={c} className="pill">
              {c}
            </span>
          ))}
        </div>
      </div>
    </>
  );
}
