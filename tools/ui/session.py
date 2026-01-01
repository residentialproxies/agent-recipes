"""
Session state helpers for the Streamlit UI.
"""

from __future__ import annotations

import uuid
from typing import List, Set

import streamlit as st

from src.ui.context import track_event


def init_session_state() -> None:
    if "_recently_viewed" not in st.session_state:
        st.session_state["_recently_viewed"] = []
    if "_favorites" not in st.session_state:
        st.session_state["_favorites"] = set()
    if "_onboarding_complete" not in st.session_state:
        st.session_state["_onboarding_complete"] = False
    if "_analytics_events" not in st.session_state:
        st.session_state["_analytics_events"] = []
    if "_session_id" not in st.session_state:
        st.session_state["_session_id"] = str(uuid.uuid4())


def get_session_id() -> str:
    return st.session_state.get("_session_id", "default")


def get_recently_viewed() -> List[str]:
    return st.session_state.get("_recently_viewed", [])


def add_to_recently_viewed(agent_id: str) -> None:
    if "_recently_viewed" not in st.session_state:
        st.session_state["_recently_viewed"] = []
    recent = st.session_state["_recently_viewed"]
    if agent_id in recent:
        recent.remove(agent_id)
    recent.insert(0, agent_id)
    st.session_state["_recently_viewed"] = recent[:10]


def get_favorites() -> Set[str]:
    return st.session_state.get("_favorites", set())


def toggle_favorite(agent_id: str) -> None:
    if "_favorites" not in st.session_state:
        st.session_state["_favorites"] = set()
    favorites = st.session_state["_favorites"]
    if agent_id in favorites:
        favorites.remove(agent_id)
        track_event("unfavorite", {"agent_id": agent_id})
    else:
        favorites.add(agent_id)
        track_event("favorite", {"agent_id": agent_id})
    st.session_state["_favorites"] = favorites


def is_onboarding_complete() -> bool:
    return bool(st.session_state.get("_onboarding_complete", False))


def mark_onboarding_complete() -> None:
    st.session_state["_onboarding_complete"] = True

