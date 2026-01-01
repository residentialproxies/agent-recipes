# Next.js Architecture Notes (Agent Navigator)

## High-Level Topology

- **FastAPI** (`src/api/`) serves the data plane:
  - `GET /v1/agents` search + filters + pagination.
  - `GET /v1/agents/{id}` detail.
  - `GET /v1/filters` filter values.
  - `POST /v1/ai/select` optional AI recommendation.
- **Next.js** (`nextjs-app/`) is the presentation plane:
  - Server Components for pages by default (SSR + caching).
  - Client Components only for interactive pieces (AI Concierge, filter UI).

## API Access Strategy

Prefer **same-origin** requests from the browser by using a Next.js rewrite:

- Browser calls `GET /api/v1/...`
- Next.js proxies to `${NEXT_PUBLIC_API_URL}/v1/...` via `next.config.js`

This avoids CORS complexity and keeps a single place to configure the backend URL.

## Data Contracts

FastAPI returns:

- `GET /v1/agents` → `{ query, total, page, page_size, items }`
- `POST /v1/ai/select` → `{ text, cached, model, usage, cost_usd }`
- Agent objects are dicts sourced from `data/agents.json` (fields like `stars`, `updated_at`, `quick_start`, etc.)

The Next.js app should align its types to these shapes and avoid assuming legacy fields like `added_at`/`github_stars`.

## Caching

- Next.js uses `fetch(..., { next: { revalidate: 3600 } })` for list/detail pages.
- FastAPI sets `Cache-Control` per route (short for list, longer for filters).
- AI endpoints are `no-store` in Next.js; FastAPI maintains its own TTL cache + daily budget guardrails.

## SEO

- Use `generateMetadata()` for `/agents/[id]` to generate unique titles/descriptions.
- Provide `app/sitemap.ts` and `app/robots.ts` to make the SSR frontend crawlable.
- Add JSON-LD on agent detail pages to increase rich-result eligibility.
