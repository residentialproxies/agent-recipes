"""
Agent Navigator - Data Store
============================
Thin, Streamlit-free loader/cacher for `data/agents.json`.

Supports two search backends:
- BM25 (in-memory): Fast, works for <5k agents
- SQLite FTS5: Scalable, works for 100k+ agents

Set SEARCH_ENGINE=sqlite in environment to use SQLite backend.

Used by:
- FastAPI backend
- Streamlit UI (optionally, in future refactors)
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from pathlib import Path

from src.config import settings
from src.exceptions import DataStoreError, SnapshotNotFoundError
from src.search import AgentSearch

logger = logging.getLogger(__name__)

# Lazy import SQLite search (only if needed)
_SQLiteAgentSearch = None
_sqlite_import_lock = threading.Lock()


def _get_sqlite_search_class() -> type:
    """
    Lazy import SQLite search engine.

    Thread-safe: uses double-checked locking pattern.
    """
    global _SQLiteAgentSearch
    if _SQLiteAgentSearch is None:
        with _sqlite_import_lock:
            # Double-check after acquiring lock
            if _SQLiteAgentSearch is None:
                try:
                    from src.search_sqlite import SQLiteAgentSearch

                    _SQLiteAgentSearch = SQLiteAgentSearch
                except ImportError as e:
                    logger.error("Failed to import SQLiteAgentSearch: %s", e)
                    raise
    return _SQLiteAgentSearch


@dataclass
class AgentsSnapshot:
    mtime_ns: int
    agents: list[dict]


_lock = threading.Lock()
_snapshot: AgentsSnapshot | None = None
_search_engine: AgentSearch | any | None = None


def _read_agents_file(path: Path) -> list[dict]:
    """Read agents from JSON file with error handling."""
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise DataStoreError(
            message="Failed to read agents data file",
            operation="read",
            path=str(path),
        ) from e

    alt_path = Path("src/data/agents.json")
    try:
        if alt_path.exists():
            return json.loads(alt_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise DataStoreError(
            message="Failed to read fallback agents data file",
            operation="read",
            path=str(alt_path),
        ) from e

    return []


def load_agents(*, path: Path | None = None) -> AgentsSnapshot:
    """
    Load agents from disk and cache by mtime.

    Returns an AgentsSnapshot so callers can cheaply detect changes.
    """
    data_path = path or settings.data_path
    try:
        mtime_ns = data_path.stat().st_mtime_ns
    except OSError:
        mtime_ns = 0

    global _snapshot
    with _lock:
        if _snapshot is not None and _snapshot.mtime_ns == mtime_ns:
            return _snapshot
        try:
            agents = _read_agents_file(data_path)
            _snapshot = AgentsSnapshot(mtime_ns=mtime_ns, agents=agents)
        except DataStoreError:
            raise
        except Exception as e:
            logger.error("Unexpected error loading agents: %s", e, exc_info=True)
            raise DataStoreError(
                message="Unexpected error loading agents data",
                operation="load",
            ) from e
        return _snapshot


def get_search_engine(*, snapshot: AgentsSnapshot | None = None) -> AgentSearch | any:
    """
    Get a cached search engine instance for the current agents snapshot.

    Returns AgentSearch (BM25), SQLiteAgentSearch (FTS5), or HybridSearch
    depending on environment variables:
    - SEARCH_ENGINE=sqlite: Use SQLite FTS5
    - HYBRID_SEARCH=true: Wrap in HybridSearch for vector similarity
    - Default: BM25 in-memory

    Args:
        snapshot: Optional agents snapshot to use

    Returns:
        Search engine instance
    """
    snap = snapshot or load_agents()
    use_sqlite = os.environ.get("SEARCH_ENGINE", "").lower() == "sqlite"
    use_hybrid = os.environ.get("HYBRID_SEARCH", "").lower() in ("true", "1", "yes")

    global _search_engine, _snapshot
    with _lock:
        # If the snapshot changed or search backend changed, rebuild the search engine
        if _snapshot is None or _snapshot.mtime_ns != snap.mtime_ns:
            _snapshot = snap
            _search_engine = None

        if _search_engine is None:
            # Step 1: Create base search engine (BM25 or SQLite)
            if use_sqlite:
                logger.info("Using SQLite FTS5 search engine")
                SQLiteSearch = _get_sqlite_search_class()
                db_path = settings.data_path.parent / "agents.db"

                # Check if database needs reindexing
                needs_reindex = True
                if db_path.exists():
                    try:
                        db_mtime = db_path.stat().st_mtime_ns
                        json_mtime = snap.mtime_ns
                        needs_reindex = json_mtime > db_mtime
                    except OSError:
                        needs_reindex = True

                base_engine = SQLiteSearch(db_path=db_path)

                # Reindex if JSON is newer than DB
                if needs_reindex:
                    logger.info(f"Reindexing {len(snap.agents)} agents into SQLite")
                    base_engine.index_agents(snap.agents)
                else:
                    logger.info("Using existing SQLite index")
            else:
                logger.info("Using BM25 in-memory search engine")
                base_engine = AgentSearch(snap.agents)

            # Step 2: Wrap with HybridSearch if enabled
            if use_hybrid:
                logger.info("Enabling hybrid search (BM25 + embeddings)")
                try:
                    from src.search_hybrid import HybridSearch

                    openai_key = os.environ.get("OPENAI_API_KEY")
                    if not openai_key:
                        logger.warning("HYBRID_SEARCH=true but OPENAI_API_KEY not set, falling back to keyword search")
                        _search_engine = base_engine
                    else:
                        _search_engine = HybridSearch(
                            base_search_engine=base_engine,
                            api_key=openai_key,
                            enable_embeddings=True,
                        )
                except ImportError as e:
                    logger.error(f"Failed to import HybridSearch: {e}")
                    logger.warning("Falling back to keyword search only")
                    _search_engine = base_engine
            else:
                _search_engine = base_engine

        return _search_engine
