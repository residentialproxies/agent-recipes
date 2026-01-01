"""
Agent Navigator UI Package.

Keeps Streamlit concerns in src/ui/* while preserving the legacy
entrypoint at src/app.py (streamlit run src/app.py).
"""

from __future__ import annotations

from src.ui.app import main

__all__ = ["main"]

