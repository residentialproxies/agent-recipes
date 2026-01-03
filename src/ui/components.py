"""
Reusable UI components (cards, sidebar, onboarding, diagrams).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import streamlit as st
import streamlit.components.v1 as components

from src.config import CATEGORY_ICONS
from src.ui.context import SOURCE_REPO_URL, track_event
from src.ui.session import (
    get_favorites,
    get_recently_viewed,
    mark_onboarding_complete,
    toggle_favorite,
)

logger = logging.getLogger(__name__)


def _is_trending_agent(agent: dict) -> bool:
    updated_at = agent.get("updated_at")
    if not updated_at:
        return False
    cutoff = datetime.utcnow() - timedelta(days=30)
    try:
        updated_date = datetime.utcfromtimestamp(updated_at)
        if updated_date < cutoff:
            return False
    except (ValueError, TypeError):
        return False
    has_stars = isinstance(agent.get("stars"), int) and agent.get("stars", 0) > 100
    has_popular_frameworks = any(fw in agent.get("frameworks", []) for fw in ["langchain", "crewai", "autogen"])
    return has_stars or has_popular_frameworks


def _is_new_agent(agent: dict) -> bool:
    updated_at = agent.get("updated_at")
    if not updated_at:
        return False
    cutoff = datetime.utcnow() - timedelta(days=7)
    try:
        updated_date = datetime.utcfromtimestamp(updated_at)
        return updated_date >= cutoff
    except (ValueError, TypeError):
        return False


def render_mermaid(diagram: str, *, height: int = 260) -> None:
    components.html(
        f"""
        <div class="mermaid">{diagram}</div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>
          mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
        </script>
        """,
        height=height,
        scrolling=True,
    )


def render_onboarding_tour() -> bool:
    if st.session_state.get("_onboarding_complete", False):
        return False

    st.markdown(
        """
        <div class="onboarding-popup">
        <h2>Welcome to Agent Navigator! 🧭</h2>
        <p>Find the perfect agent example for your next project.</p>
        <hr>
        <p><strong>Quick Start:</strong></p>
        <ul>
        <li>🔍 Try searching for <code>"RAG chatbot"</code>, <code>"PDF bot"</code>, or <code>"multi-agent"</code></li>
        <li>🤖 Use <strong>AI Selector</strong> to describe what you want in natural language</li>
        <li>🏷️ Filter by category, framework, or complexity</li>
        <li>⭐ Save your favorites and track recently viewed agents</li>
        </ul>
        <p><strong>Keyboard Shortcuts:</strong></p>
        <p><span class="keyboard-shortcut">/</span> to focus search &nbsp;|&nbsp; <span class="keyboard-shortcut">Esc</span> to clear</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Get Started! →", type="primary", use_container_width=True):
            mark_onboarding_complete()
            track_event("onboarding_complete", {})
            st.rerun()
        if st.button("Skip", use_container_width=True):
            mark_onboarding_complete()
            st.rerun()
    return True


def render_sidebar(search_engine, _agents: list[dict], agent_by_id: dict[str, dict]) -> dict:
    st.sidebar.title("Filters")

    favorites = get_favorites()
    if favorites:
        st.sidebar.markdown("### ⭐ Favorites")
        for agent_id in list(favorites)[:5]:
            agent = agent_by_id.get(agent_id)
            if agent and st.sidebar.button(
                f"★ {agent.get('name', agent_id)}",
                key=f"fav_sidebar_{agent_id}",
                use_container_width=True,
            ):
                st.query_params["agent"] = agent_id
                st.rerun()
        if len(favorites) > 5:
            st.sidebar.caption(f"+{len(favorites) - 5} more saved")
        st.sidebar.divider()

    recent = get_recently_viewed()
    if recent:
        st.sidebar.markdown("### 🕐 Recently Viewed")
        for agent_id in recent[:5]:
            agent = agent_by_id.get(agent_id)
            if agent and st.sidebar.button(
                agent.get("name", agent_id),
                key=f"recent_sidebar_{agent_id}",
                use_container_width=True,
            ):
                st.query_params["agent"] = agent_id
                st.rerun()
        st.sidebar.divider()

    options = search_engine.get_filter_options()
    filters: dict = {}

    filters["category"] = st.sidebar.multiselect(
        "Category",
        options["categories"],
        default=[],
        format_func=lambda x: x.replace("_", " ").title(),
    )
    if filters["category"]:
        track_event("filter_click", {"filter_type": "category", "values": filters["category"]})

    filters["framework"] = st.sidebar.multiselect("Framework", options["frameworks"], default=[])
    filters["provider"] = st.sidebar.multiselect("LLM Provider", options["providers"], default=[])
    filters["complexity"] = st.sidebar.multiselect("Complexity", options["complexities"], default=[])
    filters["local_only"] = st.sidebar.checkbox("Local Models Only", value=False)

    st.sidebar.divider()
    st.sidebar.caption(f"Data source: {SOURCE_REPO_URL}")

    with st.sidebar.expander("About", expanded=False):
        st.write("Agent Navigator indexes a source repo and helps you find runnable examples fast.")
        st.markdown("- Generate data: `python3 src/indexer.py --repo /path/to/awesome-llm-apps`")
        st.markdown("- Run UI: `streamlit run src/app.py`")
        st.markdown("- AI Selector: set `ANTHROPIC_API_KEY` in Streamlit secrets.")

    with st.sidebar.expander("Keyboard Shortcuts", expanded=False):
        st.markdown("**Search**")
        st.code("/ : Focus search\nEsc : Clear search", language="text")
        st.markdown("**Navigation**")
        st.code("← : Back to search\n→ : Open agent details", language="text")

    return filters


def render_agent_card(agent: dict) -> None:
    agent_id = agent.get("id", "")
    favorites = get_favorites()
    is_favorite = agent_id in favorites

    with st.container(border=True):
        col1, col2 = st.columns([3, 1])
        with col1:
            icon = CATEGORY_ICONS.get(agent.get("category", "other"), "✨")
            badges = []
            if _is_trending_agent(agent):
                badges.append('<span class="trending-badge">🔥 Trending</span>')
            if _is_new_agent(agent):
                badges.append('<span class="new-badge">✨ New</span>')
            badge_html = " ".join(badges)
            st.markdown(f"### {icon} {agent.get('name','(unnamed)')} {badge_html}", unsafe_allow_html=True)

        with col2:
            fav_label = "★" if is_favorite else "☆"
            if st.button(fav_label, key=f"fav_card_{agent_id}", help="Save to favorites"):
                toggle_favorite(agent_id)
                st.rerun()

            complexity = agent.get("complexity", "unknown")
            colors = {"beginner": "green", "intermediate": "orange", "advanced": "red"}
            st.markdown(f":{colors.get(complexity,'gray')}[{complexity}]")

        st.write(agent.get("description") or "")

        badges = [f"`{fw}`" for fw in (agent.get("frameworks") or [])[:4]]
        badges += [f"`{prov}`" for prov in (agent.get("llm_providers") or [])[:3]]
        if isinstance(agent.get("stars"), int):
            badges.append(f"⭐ {agent['stars']:,}")
        if agent.get("supports_local_models"):
            badges.append(":green[local]")
        if agent.get("requires_gpu"):
            badges.append(":orange[GPU]")
        if badges:
            st.markdown(" ".join(badges))

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("Details", use_container_width=True, key=f"details_{agent_id}"):
                track_event("detail_view", {"agent_id": agent_id, "source": "card"})
                st.query_params["agent"] = agent_id
                st.rerun()
        with col2:
            st.link_button("GitHub", agent.get("github_url", SOURCE_REPO_URL), use_container_width=True)
        with col3:
            if agent.get("codespaces_url"):
                st.link_button("Codespaces", agent["codespaces_url"], use_container_width=True)
        with col4:
            if agent.get("colab_url"):
                st.link_button("Colab", agent["colab_url"], use_container_width=True)

        with st.expander("Quick Start"):
            st.code(agent.get("clone_command", ""), language="bash")
            st.code(agent.get("quick_start", "See README for instructions"), language="bash")
