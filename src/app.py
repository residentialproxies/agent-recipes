"""
Legacy Streamlit entrypoint.

Keep `streamlit run src/app.py` working while the UI code lives in `src/ui/`.
"""

from __future__ import annotations

try:
    # When `sys.path[0] == "src"` (streamlit run src/app.py), `ui` is importable.
    from ui.app import main
except Exception:  # pragma: no cover
    # Fallback for contexts where the repo root is on sys.path.
    from src.ui.app import main  # type: ignore


if __name__ == "__main__":
    main()

