# P2 Production Upgrade Plan (PM + Architecture + pSEO)

**Date:** 2026-01-03  
**Target:** “P2 production-grade” quality without changing the product direction (FastAPI backend + Next.js frontend + static export + Streamlit admin).

---

## Goals (What “production-grade” means here)

1. **Reliability:** predictable behavior under concurrency (thread-safety, consistent error envelopes, request correlation).
2. **Performance:** cache correctness + bounded responses; avoid accidental O(n) hot paths and large in-memory keys.
3. **Maintainability:** reduce confusing duplication; align docs/config with actual runtime behavior.
4. **SEO + Content:** correct metadata/canonicals/sitemaps; meaningful landing content; no “placeholder-only” SEO.
5. **Verification:** unit tests + minimal end-to-end validation for API + exporter + Next.js builds.

Non-goals:

- Full product pivot (no redesign into a different stack).
- Introducing new paid infrastructure (Redis, external observability vendors) unless strictly necessary.

---

## Workstreams (parallelizable)

### A) Backend (FastAPI) — “Architect”

- **Request correlation**: ensure `X-Request-ID` is present on _all_ responses, including error paths.
- **Proxy-aware client IP**: use the _same_ trusted-proxy logic everywhere (rate limiting + observability logs).
- **Consistent errors**: keep a small, stable error shape (`{"error": ...}` or FastAPI `detail`) and include request ID.
- **Safety**: keep request size limits, SSRF guards, and rate limiting behavior deterministic.

**Acceptance criteria**

- `X-Request-ID` always returned (200/4xx/5xx).
- Observability logs never trust spoofed `X-Forwarded-For` unless explicitly configured.

### B) Search / Data — “Architect”

- **Thread-safe in-memory cache**: avoid concurrent mutation bugs in BM25 result cache.
- **Cache key hygiene**: avoid huge salts based on full agent ID lists; use stable short hashes.
- **Correctness**: cached results must not be accidentally mutated across requests.

**Acceptance criteria**

- Search cache is safe under concurrent access and returns immutable/copy-safe payloads.

### C) Frontend (Next.js) — “PM + Architect”

- **Deployment alignment**: make config match docs (“standalone/SSR” vs “static export”).
- **API access**: if client code uses `/api/*`, provide rewrites/proxy behavior by default.
- **SEO basics**: sitemap and robots include at least the core entry points; agent pages should be indexable in SSR mode.

**Acceptance criteria**

- `nextjs-app` builds in SSR mode by default (with optional static-export switch).
- Client requests resolve without relying on an external reverse proxy.

### D) Static SEO Export — “pSEO”

- Keep the exporter “production safe”: canonical URLs + sitemap + robots always correct when `--base-url` is provided.
- Continue generating pSEO pages (categories/frameworks/providers/comparisons/tutorials/patterns).

**Acceptance criteria**

- Static export generates a complete sitemap and robots.txt referencing it (when base URL is set).

### E) Verification & QA — “PM”

- **Unit tests**: keep `pytest` green.
- **Build checks**: validate Next.js builds (at least compile/build) for the updated configs.
- **Smoke checks**: basic `uvicorn` startup + one or two endpoint hits (local).

---

## Release Checklist (Definition of Done)

- [ ] `pytest -q` passes
- [ ] FastAPI: `X-Request-ID` returned on error responses
- [ ] Search cache thread-safe + correct
- [ ] `nextjs-app` can build in default (SSR) mode
- [ ] Exporter still produces site + sitemap/robots with `--base-url`
- [ ] Docs updated where behavior changed (deployment knobs)
