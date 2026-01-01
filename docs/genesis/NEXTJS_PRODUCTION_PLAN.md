# Next.js App Production Plan (Agent Navigator)

## Goal

Ship a production-ready “Agent Navigator” Next.js 14 (App Router) frontend (`nextjs-app/`) backed by the existing FastAPI API (`src/api/`), with working search/browse/detail flows, resilient UX, and baseline technical SEO.

## Scope (M0: Production MVP)

- **Frontend**
  - `/` landing loads without errors and shows “Trending” agents.
  - `/agents` works: search, filters, pagination, empty-state, loading/error states.
  - `/agents/[id]` works: server-rendered detail, links, robust missing-field fallbacks.
  - AI Concierge works against `/v1/ai/select` (and optionally streaming).
- **Backend / API**
  - API contract is stable for the Next.js app (query params, response shape).
  - Missing/empty descriptions are auto-filled server-side (no blank cards).
  - Sorting supported (e.g. trending by stars/updated time).
- **SEO**
  - Correct metadata (title/description/canonical) for landing, listing, and detail pages.
  - `robots.txt` + `sitemap.xml` generated from agent index.
  - Structured data (JSON-LD) for agent detail pages.
- **Ops**
  - `.env` templates for local + production.
  - Build passes: `npm run build` in `nextjs-app/` and `pytest -q` for backend.

## Parallel Workstreams (Execution Order)

1. **API Contract Alignment**
   - Fix `nextjs-app/lib/api.ts` + `nextjs-app/types/agent.ts` to match FastAPI.
   - Prefer same-origin proxying via Next.js rewrites (`/api/...`).
2. **Browse/Search UX**
   - Build `/agents` page + filter options powered by `GET /v1/filters`.
   - Add pagination controls and shareable URL query params.
3. **Detail Page Polish**
   - Add `generateMetadata` + JSON-LD.
   - Add loading/error/not-found UX.
4. **Content Baseline**
   - Ensure API returns a non-empty description (template fallback).
5. **SEO + Crawlability**
   - Add `app/sitemap.ts` and `app/robots.ts` in `nextjs-app/`.
6. **Verification**
   - Local run checklist:
     - `uvicorn src.api:app --reload --port 8000`
     - `cd nextjs-app && npm install && npm run dev`
     - Visit `/`, `/agents`, `/agents/<id>`, exercise AI Concierge.

## Acceptance Criteria

- No broken routes (home “View All” works).
- `/agents` supports deep links via querystring (shareable URLs).
- AI Concierge shows clear error on disabled AI selector / missing API key.
- Sitemap includes landing + agent pages.
- All pages render when agent fields are missing/empty (no crashes).
