# Repository Guidelines

## Project Structure & Module Organization

- `src/`: Python sources
  - `src/app.py`: Streamlit UI (“Agent Navigator”)
  - `src/search.py`: BM25 search + filtering
  - `src/indexer.py`: Claude-powered indexer that generates agent metadata
- `data/`: generated artifacts
  - `data/agents.json`: searchable agent index consumed by the app
  - `data/.indexer_cache.json`: incremental cache for the indexer
- `docs/genesis/`: architecture notes and design rationale
- `.github/workflows/update-index.yml`: scheduled workflow to refresh `data/agents.json`

## Build, Test, and Development Commands

- Create an environment + install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run the UI locally: `streamlit run src/app.py`
- Regenerate the agent index (requires a local clone of the source repo):
  - `python src/indexer.py --repo /path/to/awesome-llm-apps --output data/agents.json`
  - Use `--dry-run` to preview what would be indexed without LLM calls.
- Quick search smoke test: `python src/search.py`
- Export SEO/static fallback site: `python3 src/export_static.py --output site --base-url https://example.com`

## Coding Style & Naming Conventions

- Python (targeting 3.11+), 4-space indentation.
- Keep UI concerns in `src/app.py`, retrieval logic in `src/search.py`, and indexing/LLM logic in `src/indexer.py`.
- Naming: modules `snake_case.py`, classes `PascalCase`, constants `UPPER_SNAKE_CASE`.
- No formatter/linter is enforced in-repo; match existing style and keep diffs small.

## Testing Guidelines

- No test suite is committed yet.
- If adding tests, prefer `pytest` under `tests/` (e.g., `tests/test_search.py`) and keep defaults offline (no LLM/network calls).

## Commit & Pull Request Guidelines

- This checkout doesn’t include Git history; use small, focused commits with imperative subjects (e.g., “Fix filter logic”).
- PRs should include: what changed, how to run/verify, and screenshots for Streamlit UI changes.
- If `data/agents.json` changes, regenerate it via `src/indexer.py` (and include cache updates) rather than hand-editing.

## Security & Configuration Tips

- LLM features require `ANTHROPIC_API_KEY` (env var for `src/indexer.py`; Streamlit secrets for the “AI Selector”).
- Do not commit API keys or `.streamlit/secrets.toml`.
