# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Navigator is a discovery platform that indexes LLM agent examples from [awesome-llm-apps](https://github.com/Shubhamsaboo/awesome-llm-apps) into a searchable UI. It provides:

- A Streamlit app for browsing/searching agents
- A FastAPI backend for headless/SSR frontends
- A static site exporter for SEO
- An AI-powered agent selector using Claude

## Development Commands

```bash
# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # production deps
pip install -r requirements-dev.txt      # includes test/lint tools

# Run Streamlit UI
streamlit run src/app.py

# Run API server (for Next.js frontend)
uvicorn src.api:app --reload --port 8000

# Regenerate agent index (requires source repo clone)
python3 src/indexer.py --repo /path/to/awesome-llm-apps --output data/agents.json
python3 src/indexer.py --repo /path/to/awesome-llm-apps --dry-run  # preview only
python3 src/indexer.py --repo /path/to/awesome-llm-apps --no-llm   # heuristics only
python3 src/indexer.py --repo /path/to/awesome-llm-apps --workers 20  # parallel LLM

# Export static SEO site
python3 src/export_static.py --output site --base-url https://example.com

# Tests
pytest -q                    # all tests
pytest tests/test_search.py  # single file
pytest -k "test_bm25"        # by pattern

# Code quality
black src/ tests/
ruff check src/ tests/
mypy src/
bandit -r src/
```

## Architecture

```
src/
├── app.py          # Streamlit UI - search page, agent detail, AI selector tab
├── api.py          # FastAPI backend - /v1/agents, /v1/ai/select endpoints
├── search.py       # BM25 search engine with LRU caching (AgentSearch class)
├── indexer.py      # Builds agents.json from source repo using LLM+heuristics
├── ai_selector.py  # AI-powered agent recommendation logic
├── domain.py       # Pure business logic - URL parsing, complexity ranking
├── export_static.py# Generates static HTML site with sitemap for SEO
├── config.py       # Settings dataclass with env var overrides
├── data_store.py   # Data loading and snapshot management
├── cache.py        # Caching utilities
└── security/       # Rate limiting, input validation, secrets management

data/
├── agents.json         # The searchable agent index (generated)
└── .indexer_cache.json # Incremental update cache (content hash based)
```

## Key Patterns

- **Dual import paths**: Modules support both `from src.X` and direct `from X` for flexibility
- **BM25 over embeddings**: Cost-effective search that still handles semantic matches ("PDF bot" finds "Document Assistant")
- **LLM+heuristic hybrid**: Indexer works without API key (heuristics) but enriches with Claude when available
- **Parallel LLM processing**: Indexer uses ThreadPoolExecutor with rate limiting (10 req/s default)

## Environment Variables

Required for LLM features:

- `ANTHROPIC_API_KEY` - Claude API key

Optional:

- `GITHUB_TOKEN` - For fetching stars (avoids rate limits)
- `AI_DAILY_BUDGET_USD` - API cost limit (default: 5.0)
- `INDEXER_WORKERS` - Parallel workers (default: 20)
- `CORS_ALLOW_ORIGINS` - API CORS origins (default: \*)

## API Endpoints

- `GET /v1/agents` - Search with filters and pagination
- `GET /v1/agents/{id}` - Agent detail
- `POST /v1/search` - Same as GET but JSON body
- `POST /v1/ai/select` - AI selector (non-streaming, cached)
- `POST /v1/ai/select/stream` - AI selector with SSE streaming

## Data Model

Each agent in `agents.json` has:

- `id`, `name`, `description` - Identity
- `category` - One of: rag, chatbot, agent, multi_agent, automation, search, vision, voice, coding, finance, research, other
- `frameworks` - List: langchain, llamaindex, crewai, autogen, phidata, dspy, etc.
- `llm_providers` - List: openai, anthropic, google, ollama, local, etc.
- `complexity` - beginner, intermediate, advanced
- `github_url`, `folder_path`, `readme_relpath` - Source location
- `github_stars`, `added_at` - Metadata
