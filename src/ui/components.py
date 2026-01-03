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
    add_to_comparison,
    get_comparison_list,
    get_favorites,
    get_recently_viewed,
    mark_onboarding_complete,
    remove_from_comparison,
    toggle_favorite,
)

logger = logging.getLogger(__name__)


def render_agent_card_skeleton(count: int = 1) -> None:
    """Display skeleton placeholder for agent cards during loading."""
    skeleton_html = """
    <div class="skeleton-card">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
            <div class="skeleton skeleton-title" style="width: 50%;"></div>
            <div class="skeleton" style="width: 40px; height: 40px; border-radius: 50%;"></div>
        </div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text-short"></div>
        <div style="margin-top: 12px;">
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton skeleton-badge"></div>
        </div>
        <div style="margin-top: 16px; display: flex; gap: 8px;">
            <div class="skeleton skeleton-button" style="width: 80px;"></div>
            <div class="skeleton skeleton-button" style="width: 80px;"></div>
            <div class="skeleton skeleton-button" style="width: 80px;"></div>
        </div>
    </div>
    """
    for _ in range(count):
        st.markdown(skeleton_html, unsafe_allow_html=True)


def render_ai_selector_skeleton() -> None:
    """Display skeleton placeholder for AI selector during processing."""
    st.markdown("""
    <div style="padding: 1.5rem; border: 1px solid #e0e0e0; border-radius: 8px; background: #fafafa;">
        <div class="skeleton skeleton-title" style="width: 40%; margin-bottom: 16px;"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text-short"></div>
        <div style="margin-top: 16px;">
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton skeleton-badge"></div>
        </div>
        <div style="margin-top: 12px; padding: 12px; background: #f0f0f0; border-radius: 6px;">
            <small style="color: #666;">Analyzing your request with AI...</small>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_readme_skeleton() -> None:
    """Display skeleton placeholder for README content during loading."""
    st.markdown("""
    <div style="padding: 1rem;">
        <div class="skeleton skeleton-title" style="width: 30%; margin-bottom: 16px;"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text-short" style="margin-bottom: 16px;"></div>
        <div class="skeleton skeleton-title" style="width: 25%; margin-bottom: 12px;"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text"></div>
        <div class="skeleton skeleton-text-short"></div>
    </div>
    """, unsafe_allow_html=True)


def render_loading_indicator(message: str = "Loading...", size: str = "default") -> None:
    """Display a loading spinner with custom message."""
    sizes = {"small": "0.8rem", "default": "1rem", "large": "1.2rem"}
    font_size = sizes.get(size, "1rem")
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0;">
        <svg style="animation: spin 1s linear infinite; width: 20px; height: 20px;" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" fill="none" stroke-dasharray="32" stroke-dashoffset="32"></circle>
        </svg>
        <span style="font-size: {font_size}; color: #666;">{message}</span>
    </div>
    <style>
        @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}
    </style>
    """, unsafe_allow_html=True)


def render_error_with_retry(error_message: str, retry_key: str) -> bool:
    """Display error message with retry button. Returns True if retry clicked."""
    st.error(error_message)
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Retry", key=f"retry_{retry_key}", type="secondary"):
            return True
    return False


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
    st.sidebar.title("Agent Navigator")

    # Navigation links
    if st.sidebar.button("🔍 Search", use_container_width=True):
        st.query_params.clear()
        st.rerun()
    if st.sidebar.button("⭐ Favorites", use_container_width=True):
        st.query_params["view"] = "favorites"
        st.rerun()
    if st.sidebar.button("🕐 History", use_container_width=True):
        st.query_params["view"] = "history"
        st.rerun()

    st.sidebar.divider()
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
            st.sidebar.caption(f"[View all ({len(favorites)})]", help="Go to favorites page")
            if st.sidebar.button("View All Favorites", key="view_all_fav", use_container_width=True):
                st.query_params["view"] = "favorites"
                st.rerun()
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
        if len(recent) > 5:
            st.sidebar.caption(f"[View all ({len(recent)})]", help="Go to history page")
            if st.sidebar.button("View All History", key="view_all_hist", use_container_width=True):
                st.query_params["view"] = "history"
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


def render_agent_card(agent: dict, search_query: str = "") -> None:
    agent_id = agent.get("id", "")
    favorites = get_favorites()
    is_favorite = agent_id in favorites

    # Escape for HTML attributes
    def esc(s: str) -> str:
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    agent_name = esc(agent.get("name", "(unnamed)"))
    agent_desc = esc(agent.get("description") or "")

    # Add highlight class for JS targeting
    highlight_class = ' search-highlight-target' if search_query else ''

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
            st.markdown(
                f'### {icon} <span class="search-name{highlight_class}" data-original-text="{agent_name}">{agent_name}</span> {badge_html}',
                unsafe_allow_html=True
            )

        with col2:
            fav_label = "★" if is_favorite else "☆"
            if st.button(fav_label, key=f"fav_card_{agent_id}", help="Save to favorites"):
                toggle_favorite(agent_id)
                st.rerun()

            complexity = agent.get("complexity", "unknown")
            colors = {"beginner": "green", "intermediate": "orange", "advanced": "red"}
            st.markdown(f":{colors.get(complexity,'gray')}[{complexity}]")

        st.markdown(f'<div class="search-desc{highlight_class}" data-original-text="{agent_desc}">{agent_desc}</div>', unsafe_allow_html=True)

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

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            if st.button("Details", use_container_width=True, key=f"details_{agent_id}"):
                track_event("detail_view", {"agent_id": agent_id, "source": "card"})
                st.query_params["agent"] = agent_id
                st.rerun()
        with col2:
            render_comparison_actions(agent_id)
        with col3:
            st.link_button("GitHub", agent.get("github_url", SOURCE_REPO_URL), use_container_width=True)
        with col4:
            if agent.get("codespaces_url"):
                st.link_button("Codespaces", agent["codespaces_url"], use_container_width=True)
        with col5:
            if agent.get("colab_url"):
                st.link_button("Colab", agent["colab_url"], use_container_width=True)

        with st.expander("Quick Start"):
            st.code(agent.get("clone_command", ""), language="bash")
            st.code(agent.get("quick_start", "See README for instructions"), language="bash")

    # Trigger client-side highlighting if there's a search query
    if search_query:
        import json
        escaped_query = json.dumps(search_query)
        st.markdown(f"""
        <script>
        (function() {{
            const query = {escaped_query};
            if (window.AgentSearchEnhancements) {{
                setTimeout(() => {{
                    document.querySelectorAll('.search-highlight-target').forEach(el => {{
                        const keywords = query.toLowerCase().split(/\\s+/).filter(k => k.length > 2);
                        if (keywords.length === 0) return;
                        const regex = new RegExp('(' + keywords.map(k => k.replace(/[.*+?^{{}}()|[\\]\\\\]/g, '\\\\$&')).join('|') + ')', 'gi');
                        const original = el.dataset.originalText || el.textContent;
                        if (!el.dataset.originalText) el.dataset.originalText = original;
                        el.innerHTML = original.replace(regex, '<mark class="search-highlight">$1</mark>');
                    }});
                }}, 100);
            }}
        }})();
        </script>
        """, unsafe_allow_html=True)


def render_comparison_bar() -> bool:
    """Show comparison bar when agents are added to comparison. Returns True if should show."""
    comparison = get_comparison_list()
    if not comparison:
        return False

    st.markdown(
        f"""
        <div class="comparison-bar">
            <span style="font-weight: 600;">{len(comparison)} agent(s) selected for comparison</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption("IDs: " + ", ".join(comparison))
    with col2:
        if st.button("Compare Now", key="compare_now_btn", type="primary", use_container_width=True):
            st.query_params["view"] = "compare"
            st.rerun()
    with col3:
        if st.button("Clear", key="clear_compare_btn", use_container_width=True):
            from src.ui.session import clear_comparison
            clear_comparison()
            st.rerun()

    return True


def render_comparison_table(agents: list[dict]) -> None:
    """Render comparison table with agents as columns and attributes as rows."""
    if not agents:
        st.info("No agents to compare. Add agents from the search results.")
        return

    if len(agents) < 2:
        st.warning("Select at least 2 agents to compare.")
        return

    n_cols = len(agents)
    col_width = f"{100 // n_cols}%"

    st.markdown(f"### Comparing {len(agents)} Agent(s)")

    for attr_data in _get_comparison_attributes():
        label = attr_data["label"]
        key = attr_data["key"]
        formatter = attr_data.get("formatter", _default_formatter)
        highlight = attr_data.get("highlight", False)

        values = [formatter(agent.get(key)) for agent in agents]

        if highlight and len(set(values)) > 1:
            st.markdown(f"**{label}** :orange[_differences detected_]")
        else:
            st.markdown(f"**{label}**")

        cols = st.columns(n_cols)
        for i, (col, value) in enumerate(zip(cols, values)):
            with col:
                if highlight and len(set(values)) > 1:
                    st.markdown(f"<div class='comparison-cell comparison-cell-diff'>{value}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='comparison-cell'>{value}</div>", unsafe_allow_html=True)

        st.markdown("---")


def _get_comparison_attributes() -> list[dict]:
    """Return ordered list of attributes to compare."""
    return [
        {"label": "Name", "key": "name", "formatter": lambda x: f"**{x or '(unnamed)'}**"},
        {"label": "Description", "key": "description", "formatter": lambda x: x or "—", "highlight": False},
        {"label": "Category", "key": "category", "formatter": lambda x: (x or "other").replace("_", " ").title(), "highlight": True},
        {"label": "Frameworks", "key": "frameworks", "formatter": _format_list, "highlight": True},
        {"label": "LLM Providers", "key": "llm_providers", "formatter": _format_list, "highlight": True},
        {"label": "Complexity", "key": "complexity", "formatter": lambda x: (x or "unknown").title(), "highlight": True},
        {"label": "GitHub Stars", "key": "stars", "formatter": _format_stars, "highlight": True},
        {"label": "Languages", "key": "languages", "formatter": _format_list},
        {"label": "Local Models", "key": "supports_local_models", "formatter": _format_bool},
        {"label": "Requires GPU", "key": "requires_gpu", "formatter": _format_bool},
    ]


def _default_formatter(value) -> str:
    return str(value) if value is not None else "—"


def _format_list(value) -> str:
    if not value:
        return "—"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value[:5])
    return str(value)


def _format_stars(value) -> str:
    if isinstance(value, int):
        return f"⭐ {value:,}"
    return "—"


def _format_bool(value) -> str:
    if value is True:
        return ":green[Yes]"
    if value is False:
        return "—"
    return "Unknown"


def render_comparison_actions(agent_id: str) -> None:
    """Render add/remove from comparison button."""
    comparison = get_comparison_list()
    is_added = agent_id in comparison

    label = "− Compare" if is_added else "+ Compare"
    help_text = "Remove from comparison" if is_added else "Add to comparison (max 4)"

    if st.button(label, key=f"compare_{agent_id}", help=help_text, use_container_width=True):
        if is_added:
            remove_from_comparison(agent_id)
        else:
            success = add_to_comparison(agent_id)
            if not success:
                st.error("Maximum 4 agents can be compared. Remove an agent first.")
        st.rerun()
