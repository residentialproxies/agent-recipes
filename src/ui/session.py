"""
Session state helpers for the Streamlit UI.
"""

from __future__ import annotations

import uuid

import streamlit as st

from src.ui.context import SOURCE_REPO_URL, track_event
from src.ui.user_service import get_view_history_api, record_view_api, sync_favorites_from_api, toggle_favorite_api


def init_session_state() -> None:
    if "_recently_viewed" not in st.session_state:
        st.session_state["_recently_viewed"] = []
    if "_favorites" not in st.session_state:
        st.session_state["_favorites"] = set()
    if "_comparison_list" not in st.session_state:
        st.session_state["_comparison_list"] = []
    if "_onboarding_complete" not in st.session_state:
        st.session_state["_onboarding_complete"] = False
    if "_analytics_events" not in st.session_state:
        st.session_state["_analytics_events"] = []
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())

    # Sync favorites from API on session init
    favorites = sync_favorites_from_api()
    st.session_state["_favorites"] = favorites

    # Sync history from API
    history = get_view_history_api(limit=20)
    if history:
        st.session_state["_recently_viewed"] = history[:10]


def get_session_id() -> str:
    return st.session_state.get("_session_id", "default")


def get_recently_viewed() -> list[str]:
    return st.session_state.get("_recently_viewed", [])


def add_to_recently_viewed(agent_id: str) -> None:
    if "_recently_viewed" not in st.session_state:
        st.session_state["_recently_viewed"] = []
    recent = st.session_state["_recently_viewed"]
    if agent_id in recent:
        recent.remove(agent_id)
    recent.insert(0, agent_id)
    st.session_state["_recently_viewed"] = recent[:10]

    # Record to API for persistence
    record_view_api(agent_id)


def get_favorites() -> set[str]:
    return st.session_state.get("_favorites", set())


def toggle_favorite(agent_id: str) -> None:
    """Toggle favorite using API for persistence."""
    is_favorite = toggle_favorite_api(agent_id)

    if "_favorites" not in st.session_state:
        st.session_state["_favorites"] = set()
    favorites = st.session_state["_favorites"]

    if is_favorite:
        favorites.add(agent_id)
        track_event("favorite", {"agent_id": agent_id})
    else:
        favorites.discard(agent_id)
        track_event("unfavorite", {"agent_id": agent_id})

    st.session_state["_favorites"] = favorites


def is_onboarding_complete() -> bool:
    return bool(st.session_state.get("_onboarding_complete", False))


def mark_onboarding_complete() -> None:
    st.session_state["_onboarding_complete"] = True


def get_comparison_list() -> list[str]:
    return st.session_state.get("_comparison_list", [])


def add_to_comparison(agent_id: str) -> None:
    if "_comparison_list" not in st.session_state:
        st.session_state["_comparison_list"] = []
    comparison = st.session_state["_comparison_list"]
    if agent_id not in comparison:
        if len(comparison) >= 4:
            return False
        comparison.append(agent_id)
        track_event("add_to_comparison", {"agent_id": agent_id, "list_size": len(comparison)})
        st.session_state["_comparison_list"] = comparison
    return True


def remove_from_comparison(agent_id: str) -> None:
    if "_comparison_list" not in st.session_state:
        st.session_state["_comparison_list"] = []
    comparison = st.session_state["_comparison_list"]
    if agent_id in comparison:
        comparison.remove(agent_id)
        track_event("remove_from_comparison", {"agent_id": agent_id, "list_size": len(comparison)})
        st.session_state["_comparison_list"] = comparison


def clear_comparison() -> None:
    st.session_state["_comparison_list"] = []
    track_event("clear_comparison", {})
