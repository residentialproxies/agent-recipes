"""
Data loading + search engine construction for the Streamlit UI.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import streamlit as st

from src.search import AgentSearch
from src.ui.context import DATA_PATH

logger = logging.getLogger(__name__)


def data_version(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except (OSError, AttributeError) as exc:
        logger.warning("Could not get data version: %s", exc)
        return 0


@st.cache_data(show_spinner=False)
def load_agents(data_version: int) -> list[dict]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    alt_path = Path("src/data/agents.json")
    if alt_path.exists():
        return json.loads(alt_path.read_text(encoding="utf-8"))
    return []


@st.cache_resource(show_spinner=False)
def build_search_engine(agents: list[dict]) -> AgentSearch:
    return AgentSearch(agents)

