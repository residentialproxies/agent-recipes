"""
Agent Navigator - Data Store
============================
Thin, Streamlit-free loader/cacher for `data/agents.json`.

Used by:
- FastAPI backend
- Streamlit UI (optionally, in future refactors)
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from src.config import settings
from src.search import AgentSearch


@dataclass
class AgentsSnapshot:
    mtime_ns: int
    agents: list[dict]


_lock = threading.Lock()
_snapshot: Optional[AgentsSnapshot] = None
_search_engine: Optional[AgentSearch] = None


def _read_agents_file(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    alt_path = Path("src/data/agents.json")
    if alt_path.exists():
        return json.loads(alt_path.read_text(encoding="utf-8"))
    return []


def load_agents(*, path: Optional[Path] = None) -> AgentsSnapshot:
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
        agents = _read_agents_file(data_path)
        _snapshot = AgentsSnapshot(mtime_ns=mtime_ns, agents=agents)
        return _snapshot


def get_search_engine(*, snapshot: Optional[AgentsSnapshot] = None) -> AgentSearch:
    """
    Get a cached AgentSearch instance for the current agents snapshot.
    """
    snap = snapshot or load_agents()

    global _search_engine, _snapshot
    with _lock:
        # If the snapshot changed, rebuild the search engine.
        if _snapshot is None or _snapshot.mtime_ns != snap.mtime_ns:
            _snapshot = snap
            _search_engine = None

        if _search_engine is None:
            _search_engine = AgentSearch(snap.agents)

        return _search_engine

