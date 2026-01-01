# Agent Navigator

Agent Navigator turns a large "awesome list" style repository of LLM apps into a searchable discovery UI. It ships with:

- A repository indexer (`src/indexer.py`) that builds `data/agents.json`
- A Next.js production frontend (`nextjs-app/`) with SSR/ISR support
- A FastAPI backend (`src/api/`) for the frontend and headless access
- A Streamlit admin UI (`tools/streamlit_app.py`) for internal use
- An optional static site exporter (`src/export_static.py`) for SEO / fallback hosting

## Quickstart

**Production Frontend (Next.js):**

```bash
cd nextjs-app
npm install
npm run dev  # Visit http://localhost:3000
```

**Admin UI (Streamlit - Internal Only):**

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run tools/streamlit_app.py
```

## API Server (for Next.js SSR frontend)

Run locally:

```bash
uvicorn src.api:app --reload --port 8000
```

Key endpoints:

- `GET /v1/agents` (search + filters + pagination)
- `GET /v1/agents/{id}` (detail)
- `POST /v1/search` (same as `/v1/agents`, but JSON body)
- `POST /v1/ai/select` (non-stream AI selector; cached)
- `POST /v1/ai/select/stream` (SSE streaming; cached)

WebManus (consumer-facing) endpoints:

- `GET /v1/workers` (SQLite-backed workers directory; supports `q`, `capability`, `pricing`, `min_score`, `limit`, `offset`)
- `GET /v1/workers/{slug}`
- `GET /v1/capabilities`
- `POST /v1/consult` (consumer-focused recommendations; JSON)
- `POST /v1/consult/stream` (SSE streaming; JSON in `done` event)

Environment variables (VPS):

- `ANTHROPIC_API_KEY` (required for AI endpoints)
- `CORS_ALLOW_ORIGINS` (default `*`, or comma-separated origins)
- `TRUST_PROXY_HEADERS` (set `true` if you run behind a reverse proxy and want to trust `X-Forwarded-For`)
- `TRUSTED_PROXY_IPS` (comma-separated proxy IPs to trust; set to `*` to trust all proxies — not recommended)
- `AI_DAILY_BUDGET_USD` (default `5.0`)
- `AI_CACHE_TTL_SECONDS` (default `21600`)
- `ANTHROPIC_INPUT_USD_PER_MILLION` / `ANTHROPIC_OUTPUT_USD_PER_MILLION` (required if you change to a non-“haiku” model)

## Build / Update the Index

1. Download/clone the source repo (default: `awesome-llm-apps`)
2. Run the indexer:

```bash
python3 src/indexer.py --repo /path/to/awesome-llm-apps --output data/agents.json
```

Notes:

- Add `--no-llm` to run fully offline (heuristics only).
- Add `--fetch-stars` to populate GitHub repo stars (best-effort; may be rate limited).

## AI Selector (Optional)

The “AI Selector” tab uses Anthropic Claude.

- Local run: export `ANTHROPIC_API_KEY` into Streamlit secrets (`.streamlit/secrets.toml`)
- CI: set `ANTHROPIC_API_KEY` as a GitHub Actions secret

## Static Export (SEO / Fallback)

```bash
python3 src/export_static.py --output site --base-url https://example.com
```

This writes `site/index.html`, per-agent pages under `site/agents/<id>/`, plus `site/404.html` and `site/_headers` for static hosting. If `--base-url` is set, it also writes `site/sitemap.xml` + `site/robots.txt`.

### Cloudflare Pages (recommended for static SEO site)

- Build command: `python3 src/export_static.py --output site --base-url https://your-domain.com`
- Output directory: `site`

Note: The Next.js frontend is configured for Node runtime (`output: "standalone"`). If you want to run it on Cloudflare Pages/Workers, you’ll need a Cloudflare adapter (e.g. `@cloudflare/next-on-pages`) and some config changes.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## WebManus: Migrate JSON → SQLite

Generate `data/webmanus.db` from the existing developer-facing `data/agents.json`:

```bash
python3 scripts/migrate_to_webmanus.py
```

## WebManus Frontend (Next.js)

```bash
cd nextjs-frontend
npm install
API_URL=http://localhost:8000 NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Docker (API + Web)

```bash
docker compose -f docker-compose.webmanus.yml up --build
```
