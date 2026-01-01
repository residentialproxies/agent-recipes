"""
Shared UI context (constants + lightweight helpers).

This module is intentionally small and dependency-light to avoid circular imports.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import streamlit as st

DATA_PATH = Path("data/agents.json")
SOURCE_REPO_URL = "https://github.com/Shubhamsaboo/awesome-llm-apps"
SOURCE_BRANCH = "main"


def track_event(event_name: str, properties: Optional[dict] = None) -> None:
    """
    Track analytics event (placeholder for future integration).

    Stored in session state for debugging purposes.
    """
    event_data = {
        "event": event_name,
        "properties": properties or {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    if "_analytics_events" not in st.session_state:
        st.session_state["_analytics_events"] = []
    st.session_state["_analytics_events"].append(event_data)

