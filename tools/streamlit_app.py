"""
Streamlit Admin UI - Internal Tool Only

This is the legacy Streamlit interface moved to tools/ for internal admin use.
The production frontend is Next.js (nextjs-app/).

Usage:
    streamlit run tools/streamlit_app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from tools.ui.app import main
except ImportError:
    from src.ui.app import main  # type: ignore


if __name__ == "__main__":
    main()

