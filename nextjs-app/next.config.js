/** @type {import('next').NextConfig} */
const backend =
  process.env.API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || "";
const outputMode = process.env.NEXT_OUTPUT || "";
const isStaticExport = outputMode.toLowerCase() === "export";
const backendClean = backend.endsWith("/") ? backend.slice(0, -1) : backend;

if (process.env.NODE_ENV === "production" && !siteUrl) {
  throw new Error(
    "NEXT_PUBLIC_SITE_URL is required for production builds (sitemap/canonical).",
  );
}

const nextConfig = {
  trailingSlash: true,
  // Default to production SSR/ISR (standalone). Allow static export explicitly via NEXT_OUTPUT=export.
  output: isStaticExport ? "export" : "standalone",
  images: isStaticExport ? { unoptimized: true } : undefined,
  env: {
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL || "https://api.agentrecipes.com",
  },
  async rewrites() {
    // Browser requests use same-origin `/api/*` and are proxied to the backend.
    // For static export, rewrites are not applied; the app should be deployed behind a proxy/CDN if needed.
    if (isStaticExport) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${backendClean}/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
