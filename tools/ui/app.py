"""
Streamlit UI entrypoint (new home for the old src/app.py).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import streamlit as st


def _ensure_repo_root_on_path() -> None:
    # streamlit run src/app.py sets sys.path[0] == "src", which breaks `import src.*`.
    repo_root = Path(__file__).resolve().parents[2]
    repo_root_s = str(repo_root)
    if repo_root_s not in sys.path:
        sys.path.insert(0, repo_root_s)


_ensure_repo_root_on_path()

from src import domain  # noqa: E402
from src.search import AgentSearch  # noqa: E402
from src.ui.context import DATA_PATH, SOURCE_REPO_URL  # noqa: E402
from src.ui.data import build_search_engine, data_version, load_agents  # noqa: E402
from src.ui.pages import render_detail_page, render_search_page  # noqa: E402
from src.ui.session import init_session_state  # noqa: E402
from src.ui.styles import apply_styles  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    st.set_page_config(
        page_title="Agent Navigator",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    apply_styles()
    init_session_state()

    agents_raw = load_agents(data_version(DATA_PATH))
    agents = [domain.normalize_agent_record(a, source_repo_url=SOURCE_REPO_URL) for a in agents_raw]

    if not agents:
        st.error("No agents found. Generate `data/agents.json` via `python3 src/indexer.py ...`.")
        return

    agent_by_id: dict[str, dict] = {a["id"]: a for a in agents if a.get("id")}
    search_engine: AgentSearch = build_search_engine(agents)

    agent_id = st.query_params.get("agent")
    if agent_id:
        selected = agent_by_id.get(agent_id)
        if not selected:
            st.error(f"Unknown agent id: {agent_id}")
            if st.button("Back to Search"):
                st.query_params.clear()
                st.rerun()
            return
        render_detail_page(selected, agents)
        return

    render_search_page(search_engine, agents, agent_by_id)


if __name__ == "__main__":
    main()
