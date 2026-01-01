# P2 Optimization Plan: Agent Navigator (Gemini)

This comprehensive plan targets performance, architecture, and scalability improvements for the Agent Navigator platform. The core strategy involves unifying the data architecture around SQLite to resolve memory bottlenecks and enable scalability beyond 10,000 agents, while modernizing the frontend stack.

## 1. Architecture: Unify Data Persistence

**Problem:** The system currently maintains two sources of truth: `agents.json` (loaded into memory for BM25 search) and `webmanus.db` (SQLite for WebManus features). This duplication increases memory usage, complicates data management, and slows down application startup (~500+ agents loaded/tokenized on boot).
**Impact:** High - Reduces memory footprint, speeds up startup, simplifies data logic.
**Implementation:**

- **Consolidate to SQLite:** Migrate all data from `agents.json` into `webmanus.db`.
- **Schema Update:** Enhance the `agents` table in `src/repository.py` to store all fields currently in `agents.json` (e.g., `frameworks`, `llm_providers` as JSON columns or related tables).
- **Single Source:** Update `src/indexer.py` to write directly to SQLite instead of JSON, or add a post-indexing step to sync JSON -> SQLite.

## 2. Scalability & Performance: SQLite FTS5 Search

**Problem:** The current in-memory BM25 search (`src/search.py`) is fast but memory-bound. As the dataset grows, startup time and memory consumption will degrade linearly.
**Impact:** High - Enables scaling to 100k+ agents with constant startup time.
**Implementation:**

- **Enable FTS5:** Use SQLite's Full-Text Search extension (FTS5).
- **Migration:** Replace the in-memory `AgentSearch` class with a SQL-based implementation using FTS5 virtual tables.
  ```sql
  CREATE VIRTUAL TABLE agents_fts USING fts5(name, description, tagline, content=agents, content_rowid=slug);
  ```
- **Relevance:** SQLite FTS5 supports BM25 ranking via the `bm25()` function (available in modern builds) or standard ranking, which is sufficient for this domain.

## 3. Frontend Performance: Next.js Optimization

**Problem:** The Next.js app (`nextjs-app`) is currently a basic build. Production performance can be significantly improved.
**Impact:** Medium - Better Core Web Vitals and user experience.
**Implementation:**

- **Image Optimization:** Enforce `next/image` usage with proper sizing policies to prevent layout shift (CLS).
- **Bundle Analysis:** Add `@next/bundle-analyzer` to identifying and trimming large dependencies.
- **React Server Components:** Ensure the main agent grid is a Server Component to reduce client-side JavaScript hydration cost.

## 4. Developer Experience: End-to-End Type Safety

**Problem:** Backend (Python) and Frontend (TypeScript) types are manually synced, leading to potential runtime errors if the API changes.
**Impact:** Medium - Prevents bugs, speeds up development.
**Implementation:**

- **OpenAPI to TypeScript:** Use `openapi-typescript-codegen` to automatically generate the frontend API client from FastAPI's `openapi.json`.
  ```bash
  # In CI/CD or pre-commit
  npx openapi-typescript-codegen --input ./openapi.json --output ./nextjs-app/lib/api-client
  ```
- **Strict Python Typing:** Configure `mypy` with `--strict` in `pyproject.toml` to catch type errors in the backend.

## 5. Deployment: Optimized Docker Build

**Problem:** The current `Dockerfile` (implied) likely copies the entire source. A unified repo often leads to large images.
**Impact:** Medium - Faster deployments, lower storage costs.
**Implementation:**

- **Multi-Stage Build:** Create a 2-stage Dockerfile.
  1.  **Builder:** Install build deps, build Next.js app (`npm run build`), export static files or standalone server.
  2.  **Runner:** Minimal Python slim image, copy only necessary artifacts (Python venv, Next.js standalone/static).
- **Layer Caching:** Order `requirements.txt` and `package.json` installs before source code copying.

## 6. SEO & Discovery: Dynamic Metadata & Sitemap

**Problem:** The Next.js app needs to be discoverable. Static export is good, but dynamic rendering offers better long-tail SEO for thousands of agent pages.
**Impact:** High - Increases organic traffic.
**Implementation:**

- **Dynamic Sitemap:** Implement `app/sitemap.ts` in Next.js to generate a sitemap of all indexed agents dynamically from the API.
- **Metadata API:** Use Next.js `generateMetadata` function in `app/agent/[slug]/page.tsx` to inject dynamic Title, Description, and Open Graph tags for every agent.

## 7. Cost Efficiency: CDN & Caching Strategy

**Problem:** Serving API requests for static data (agent details) consumes compute resources.
**Impact:** Medium - Reduces server load.
**Implementation:**

- **Cache-Control Headers:** Implement aggressive `Cache-Control` headers (e.g., `public, max-age=3600, stale-while-revalidate=86400`) in FastAPI for GET endpoints.
- **Stale-While-Revalidate:** Allow the CDN/browser to serve stale content while updating in the background.

## 8. Code Quality: Integration Testing

**Problem:** Current tests are likely unit-focused. The search logic (core value) needs end-to-end verification.
**Impact:** Medium - Ensures core feature stability during refactors.
**Implementation:**

- **API Tests:** Add `pytest` integration tests that spin up the `TestClient(app)`, insert sample data into SQLite, and verify search results match expectations via the API.
- **Verify FTS:** specifically test edge cases (typos, partial matches) in the new SQLite FTS implementation.

## 9. Security: Content Security Policy (CSP)

**Problem:** Web apps are vulnerable to XSS if not properly secured.
**Impact:** Low (Internal tool) / High (Public).
**Implementation:**

- **Strict CSP:** Configure `helmet` (or FastAPI middleware) to send strict `Content-Security-Policy` headers, allowing scripts only from self and trusted analytics domains.

## 10. User Experience: Search Autocomplete

**Problem:** Users have to type full terms and hit enter to see results.
**Impact:** Medium - "Delight" factor and usability.
**Implementation:**

- **Type-ahead API:** Create a lightweight `/v1/agents/suggest?q=...` endpoint optimized for speed (searching only names/categories).
- **Frontend Integration:** Use `cmdk` or a similar accessible combobox component in Next.js to show real-time suggestions as the user types.

---

### Recommended Execution Order

1.  **Architecture:** SQLite Migration (Unifies data, enables FTS).
2.  **Performance:** SQLite FTS5 Implementation (Solves scalability).
3.  **DX:** OpenAPI Client Generation (Safe frontend dev).
4.  **SEO:** Sitemap & Metadata (Visibility).
5.  **Deployment:** Docker Optimization (Efficiency).
