"""
Page renderers for Streamlit UI.
"""

from __future__ import annotations

import logging
import urllib.request
from datetime import datetime

import streamlit as st

from src import domain
from src.ai_selector import handle_anthropic_error
from src.search import AgentSearch
from src.security import (
    ValidationError,
    get_rate_limiter,
    get_secrets_manager,
    sanitize_llm_output,
    sanitize_markdown,
)
from src.ui.components import render_agent_card, render_mermaid
from src.ui.context import SOURCE_BRANCH, SOURCE_REPO_URL, track_event
from src.ui.session import add_to_recently_viewed, get_favorites, get_session_id, toggle_favorite

logger = logging.getLogger(__name__)

try:
    import anthropic  # type: ignore

    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


@st.cache_data(show_spinner=False)
def fetch_readme_markdown(readme_url: str) -> str:
    from src.security.validators import validate_github_url
    try:
        validated_url = validate_github_url(readme_url)
    except ValidationError as exc:
        raise ValueError(f"Invalid URL: {exc}") from exc
    with urllib.request.urlopen(validated_url, timeout=10) as resp:
        return resp.read().decode("utf-8", errors="replace")


def ai_select_agents(query: str, agents: list[dict]) -> str:
    query = (query or "").strip()
    if not query:
        return "Please describe what you want to build."

    secrets_mgr = get_secrets_manager()
    api_key = secrets_mgr.get_secret("ANTHROPIC_API_KEY")
    if not api_key:
        return "AI selector disabled: missing ANTHROPIC_API_KEY."

    if not HAS_ANTHROPIC:
        return "AI selector disabled: missing `anthropic` dependency."

    rate_limiter = get_rate_limiter()
    session_id = get_session_id()
    allowed, retry_after = rate_limiter.check_rate_limit(session_id)
    if not allowed:
        logger.info("Rate limit exceeded for session %s", session_id)
        return f"Rate limited: try again in {retry_after}s."

    agent_list = "\n".join(
        f"- {a['id']}: {a.get('name','')} — {a.get('description','')} [{a.get('category','other')}; {', '.join(a.get('frameworks', [])[:3])}]"
        for a in agents[:80]
    )

    prompt = f"""You recommend the best matching agent examples.

Available Agents:
{agent_list}

User Request: "{query}"

Return the top 5 agent IDs with 1-2 sentences each:
1. **agent_id**: reason
...
If nothing fits, say what tags/frameworks the user should search for.
"""

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_output = response.content[0].text

        try:
            safe_output = sanitize_llm_output(raw_output, allow_markdown=True)
        except ValidationError as exc:
            logger.warning("LLM output sanitization failed: %s", exc)
            safe_output = "AI response could not be safely displayed."

        track_event("ai_selector", {"query_length": len(query), "result_length": len(safe_output)})
        return safe_output

    except (OSError, TimeoutError) as exc:
        logger.error("Network error calling AI API: %s", exc)
        return "AI error: Network error. Please try again."
    except Exception as exc:
        error_msg = handle_anthropic_error(exc, detail_prefix="AI error")
        logger.error("AI selector error: %s", exc)
        track_event("ai_selector_error", {"error": str(exc)})
        return error_msg


def render_detail_page(agent: dict, agents: list[dict]) -> None:
    agent_id = agent.get("id", "")
    add_to_recently_viewed(agent_id)
    track_event("detail_view", {"agent_id": agent_id, "source": "direct_link"})

    favorites = get_favorites()
    is_favorite = agent_id in favorites

    st.title(agent.get("name", "Agent"))
    st.caption(agent.get("description", ""))

    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("← Back to Search", use_container_width=True):
            st.query_params.clear()
            st.rerun()
    with col2:
        fav_label = "★ Unfavorite" if is_favorite else "☆ Favorite"
        if st.button(fav_label, key=f"fav_detail_{agent_id}", use_container_width=True):
            toggle_favorite(agent_id)
            st.rerun()
    with col3:
        st.link_button("Open on GitHub", agent.get("github_url", SOURCE_REPO_URL), use_container_width=True)
    with col4:
        updated_at = agent.get("updated_at")
        if isinstance(updated_at, int):
            st.caption(f"Last updated: {datetime.utcfromtimestamp(updated_at).strftime('%Y-%m-%d')} (UTC)")

    meta1, meta2 = st.columns(2)
    with meta1:
        st.markdown("#### Quick Start")
        if agent.get("api_keys"):
            st.write("Required API keys:", ", ".join(agent["api_keys"]))
        st.write("Estimated setup time:", domain.estimate_setup_time(agent.get("complexity") or ""))
        st.code(agent.get("clone_command", ""), language="bash")
        st.code(agent.get("quick_start", ""), language="bash")
        if st.button("📋 Copy Clone Command", key=f"copy_clone_{agent_id}"):
            st.code(agent.get("clone_command", ""), language="bash")
            st.success("Command copied to clipboard!")
            track_event("clone_click", {"agent_id": agent_id})

    with meta2:
        st.markdown("#### Tech Stack")
        st.write("Category:", (agent.get("category") or "other").replace("_", " "))
        st.write("Complexity:", agent.get("complexity", "intermediate"))
        st.write("Frameworks:", ", ".join(agent.get("frameworks") or []) or "—")
        st.write("Providers:", ", ".join(agent.get("llm_providers") or []) or "—")
        if isinstance(agent.get("stars"), int):
            st.write("Repo stars:", f"{agent['stars']:,}")
        if agent.get("languages"):
            st.write("Languages:", ", ".join(agent["languages"]))
        st.markdown("#### Architecture Preview")
        try:
            render_mermaid(domain.build_agent_diagram(agent))
        except (ValueError, KeyError, AttributeError) as exc:
            logger.warning("Could not render mermaid diagram: %s", exc)
            st.code(domain.build_agent_diagram(agent), language="text")

    st.divider()

    similar = domain.recommend_similar(agent, agents, limit=6)
    if similar:
        st.markdown("#### Similar Agents")
        cols = st.columns(3)
        for i, a in enumerate(similar):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{a.get('name','')}**")
                    st.caption(a.get("category", "other").replace("_", " "))
                    if st.button("Open", key=f"open_sim_{a.get('id')}", use_container_width=True):
                        st.query_params["agent"] = a.get("id", "")
                        st.rerun()

    st.divider()

    st.markdown("## README")
    url = domain.raw_readme_url(agent, default_branch=SOURCE_BRANCH)
    if not url:
        st.warning("README unavailable for this entry.")
        return

    try:
        md = fetch_readme_markdown(url)
        md = domain.rewrite_relative_links(md, agent, default_branch=SOURCE_BRANCH)
        try:
            safe_md = sanitize_markdown(md, max_length=500_000)
            st.markdown(safe_md)
        except (TypeError, ValueError) as exc:
            logger.warning("Markdown sanitization failed for %s: %s", agent.get("id"), exc)
            st.warning("README content could not be safely displayed.")
            st.link_button("View on GitHub", agent.get("github_url", SOURCE_REPO_URL))
    except (ValueError, urllib.error.HTTPError, urllib.error.URLError) as exc:
        st.warning(f"Could not fetch README ({exc}).")
        st.link_button("View on GitHub", agent.get("github_url", SOURCE_REPO_URL))
    except (OSError, TimeoutError) as exc:
        st.warning(f"Network error fetching README: {exc}")
        st.link_button("View on GitHub", agent.get("github_url", SOURCE_REPO_URL))


def render_ai_selector_hero(agents: list[dict]) -> tuple[bool, str]:
    st.markdown("## 🤖 AI Selector")
    st.caption("Describe what you want to build, and get recommended agent examples.")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("What do you want to build?", key="ai_query", placeholder="e.g. RAG chatbot for PDFs")
    with col2:
        run = st.button("Recommend", type="primary", use_container_width=True)

    if run:
        with st.spinner("Thinking..."):
            result = ai_select_agents(query, agents)
        return True, result

    return False, ""


def render_search_page(search_engine: AgentSearch, agents: list[dict], agent_by_id: dict[str, dict]) -> None:
    from src.ui.components import render_onboarding_tour, render_sidebar

    shown = render_onboarding_tour()
    if shown:
        st.stop()

    st.title("Agent Navigator")
    st.caption("Search, filter, and inspect agent examples indexed from awesome-llm-apps.")

    filters = render_sidebar(search_engine, agents, agent_by_id)

    st.markdown("## Search")

    q_default = st.query_params.get("q", "")
    q = st.text_input("Search agents...", value=q_default, key="search_input", help="Type keywords and press Enter")

    query_params = st.query_params
    query_params["q"] = q
    st.caption("Tip: Press `/` to focus search, `Esc` to clear.")

    ai_ran, ai_text = render_ai_selector_hero(agents)
    if ai_ran and ai_text:
        st.markdown(ai_text)
        st.divider()

    results = search_engine.search(q, limit=500) if q.strip() else list(search_engine.agents.values())
    results = search_engine.filter_agents(
        results,
        category=filters.get("category") or None,
        framework=filters.get("framework") or None,
        provider=filters.get("provider") or None,
        complexity=filters.get("complexity") or None,
        local_only=bool(filters.get("local_only")),
    )
    results.sort(key=lambda a: (a.get("name", "") or "").lower())

    st.markdown(f"### Results ({len(results)})")

    if "_page" not in st.session_state:
        st.session_state["_page"] = 1

    page_size = 20
    page = int(query_params.get("page", st.session_state["_page"]) or 1)
    total_pages = max(1, (len(results) + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    st.session_state["_page"] = page
    query_params["page"] = str(page)

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    with nav1:
        if st.button("← Prev", disabled=(page <= 1), use_container_width=True):
            st.session_state["_page"] = max(1, page - 1)
            st.rerun()
    with nav2:
        st.caption(f"Page {page} / {total_pages}")
    with nav3:
        if st.button("Next →", disabled=(page >= total_pages), use_container_width=True):
            st.session_state["_page"] = min(total_pages, page + 1)
            st.rerun()

    start = (page - 1) * page_size
    end = start + page_size
    view = results[start:end]

    cols = st.columns(2)
    for i, agent in enumerate(view):
        with cols[i % 2]:
            render_agent_card(agent)

