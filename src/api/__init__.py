"""
Agent Navigator API package.

Public exports:
- create_app: FastAPI factory
- app: default global FastAPI instance (for `uvicorn src.api:app`)
- AppState: app.state container used by tests
"""

from __future__ import annotations

from types import SimpleNamespace

try:
    import anthropic as anthropic  # type: ignore

    HAS_ANTHROPIC = True
except ImportError:  # pragma: no cover
    anthropic = SimpleNamespace(Anthropic=None)  # type: ignore
    HAS_ANTHROPIC = False

from fastapi import HTTPException as HTTPException

from src.api.app import app, create_app
from src.api.state import AppState

__all__ = ["AppState", "HAS_ANTHROPIC", "HTTPException", "anthropic", "app", "create_app"]
