"""
Dependency helpers for API routes.

These are kept as simple functions (not FastAPI Depends) because the app
already uses request.app.state for most stateful components.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request

from src.data_store import AgentsSnapshot, get_search_engine, load_agents
from src.repository import AgentRepo
from src.api.state import AppState


def get_state(request: Request) -> AppState:
    state = getattr(request.app.state, "state", None)
    if state is None:
        snap = load_agents()
        state = AppState(snapshot=snap, webmanus_repo=None)
        request.app.state.state = state
    return state


def get_snapshot(request: Request) -> AgentsSnapshot:
    return get_state(request).snapshot


def get_search_engine_for_request(request: Request):
    snap = get_snapshot(request)
    return get_search_engine(snapshot=snap)


def get_webmanus_repo(request: Request) -> AgentRepo:
    state = get_state(request)
    repo: Optional[AgentRepo] = state.webmanus_repo
    if repo is None:
        repo = AgentRepo(str(settings.webmanus_db_path))
        state.webmanus_repo = repo
    return repo


def get_ai_cache(request: Request):
    return request.app.state.ai_cache


def get_ai_budget(request: Request):
    return request.app.state.ai_budget


def get_rate_limiter(request: Request):
    return request.app.state.rate_limiter
