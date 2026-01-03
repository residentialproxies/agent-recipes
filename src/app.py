"""
Legacy Streamlit entrypoint.

This project’s primary production frontend is Next.js (see `nextjs-app/`).
The Streamlit UI is kept for internal/admin use and local debugging.

Backward compatible with:
  streamlit run src/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> None:
    # `streamlit run src/app.py` sets sys.path[0] == "src", which breaks `import src.*`.
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_s = str(repo_root)
    if repo_root_s not in sys.path:
        sys.path.insert(0, repo_root_s)


_ensure_repo_root_on_path()

from src.ui.app import main  # noqa: E402

if __name__ == "__main__":
    main()
