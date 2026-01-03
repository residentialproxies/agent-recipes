"""
User service for Streamlit UI - handles persistent favorites and history.

Integrates with the API for backend storage, with localStorage fallback.
"""

from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import requests

logger = logging.getLogger(__name__)


# Default API URL (override via env)
DEFAULT_API_URL = "http://localhost:8000"


def _get_api_url() -> str:
    import os

    return os.environ.get("AGENT_NAV_API_URL", DEFAULT_API_URL)


def _get_user_id() -> str:
    """
    Get or generate a persistent user ID.

    Uses localStorage pattern with Streamlit session state.
    For real persistence across sessions, frontend must store in browser localStorage.
    """
    import streamlit as st

    # Try to get from session state
    if "_persistent_user_id" not in st.session_state:
        # Generate a new persistent ID
        st.session_state["_persistent_user_id"] = f"user_{uuid.uuid4().hex[:24]}"
    return st.session_state["_persistent_user_id"]


def get_user_id_for_client() -> str:
    """Get user ID and return it for client-side storage."""
    return _get_user_id()


def set_user_id(user_id: str) -> None:
    """Set user ID from client-side storage."""
    import streamlit as st

    if user_id:
        st.session_state["_persistent_user_id"] = str(user_id)[:255]


def sync_favorites_from_api(agent_ids: set[str] | None = None) -> set[str]:
    """
    Sync favorites from API, or provide local set to sync to API.

    Returns the current set of favorite agent IDs.
    """
    import streamlit as st

    user_id = _get_user_id()

    # Initialize in-memory cache
    if "_favorites_cache" not in st.session_state:
        st.session_state["_favorites_cache"] = set()

    try:
        api_url = _get_api_url()
        response = requests.get(
            f"{api_url}/v1/users/favorites",
            headers={"X-User-ID": user_id},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            favorites = set(data.get("agent_ids", []))
            st.session_state["_favorites_cache"] = favorites
            return favorites
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to fetch favorites from API: {e}")

    # Fall back to cached values
    return st.session_state["_favorites_cache"].copy()


def toggle_favorite_api(agent_id: str) -> bool:
    """
    Toggle favorite status via API.

    Returns True if agent is now favorited, False otherwise.
    """
    import streamlit as st

    user_id = _get_user_id()
    is_favorite = False

    try:
        api_url = _get_api_url()
        response = requests.post(
            f"{api_url}/v1/users/favorites/{agent_id}/toggle",
            headers={"X-User-ID": user_id},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            is_favorite = data.get("is_favorite", False)
        else:
            # Local fallback
            favorites = st.session_state.get("_favorites_cache", set())
            is_favorite = agent_id not in favorites
            if is_favorite:
                favorites.add(agent_id)
            else:
                favorites.discard(agent_id)
            st.session_state["_favorites_cache"] = favorites
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to toggle favorite via API: {e}")
        # Local fallback
        favorites = st.session_state.get("_favorites_cache", set())
        is_favorite = agent_id not in favorites
        if is_favorite:
            favorites.add(agent_id)
        else:
            favorites.discard(agent_id)
        st.session_state["_favorites_cache"] = favorites

    return is_favorite


def record_view_api(agent_id: str) -> bool:
    """Record an agent view via API."""
    user_id = _get_user_id()

    try:
        api_url = _get_api_url()
        requests.post(
            f"{api_url}/v1/users/history/{agent_id}",
            headers={"X-User-ID": user_id},
            timeout=5,
        )
        return True
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to record view via API: {e}")
        return False


def get_view_history_api(limit: int = 20) -> list[str]:
    """Get view history from API."""
    user_id = _get_user_id()

    try:
        api_url = _get_api_url()
        response = requests.get(
            f"{api_url}/v1/users/history",
            headers={"X-User-ID": user_id},
            params={"limit": limit},
            timeout=5,
        )
        if response.status_code == 200:
            data = response.json()
            return [item.get("agent_id", "") for item in data.get("items", [])]
    except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to fetch history from API: {e}")

    return []


# JavaScript snippet for client-side user ID management
USER_ID_JS = """
<script>
(function() {
    const STORAGE_KEY = 'agent_nav_user_id';
    const hiddenInput = document.getElementById('user-id-input');

    // Get existing or generate new user ID
    let userId = localStorage.getItem(STORAGE_KEY);
    if (!userId || userId.length < 10) {
        userId = 'user_' + crypto.randomUUID().slice(0, 24);
        localStorage.setItem(STORAGE_KEY, userId);
    }

    // Store in hidden input or data attribute
    if (hiddenInput) {
        hiddenInput.value = userId;
    }

    // Make available globally
    window.agentNavUserId = userId;
})();
</script>
"""


def render_user_id_sync() -> None:
    """
    Render JavaScript to sync user ID between server and client.

    This should be called once per session to establish persistent identity.
    """
    import streamlit as st

    st.markdown(USER_ID_JS, unsafe_allow_html=True)

    # Hidden input to receive user ID from client
    st.markdown(
        '<input type="hidden" id="user-id-input" data-user-id="">',
        unsafe_allow_html=True,
    )
