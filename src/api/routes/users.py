"""
User routes for favorites and view history.
"""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Request, Response

from src.api.models import (
    FavoriteAddRequest,
    FavoriteListResponse,
    FavoriteResponse,
    HistoryListResponse,
    HistoryRecordResponse,
    UserInfoResponse,
)
from src.repository.users import get_user_repo

router = APIRouter(prefix="/v1/users", tags=["users"])


def _extract_user_id(request: Request) -> str:
    """
    Extract user_id from request.
    Looks in order: X-User-ID header, Authorization header (for auth integration).
    Falls back to anonymous user ID from session.
    """
    # Try custom header first
    user_id = request.headers.get("x-user-id") or request.headers.get("X-User-ID")
    if user_id:
        return str(user_id).strip()[:255]

    # Try session-based fallback
    user_id = request.headers.get("x-session-id") or request.headers.get("X-Session-ID")
    if user_id:
        return f"session:{user_id}"[:255]

    # Last resort: generate a temporary ID (not ideal for persistence)
    return f"anonymous:{request.client.host if request.client else 'unknown'}"


@router.post(
    "/favorites",
    response_model=FavoriteResponse,
    responses={
        200: {"description": "Favorite added"},
        400: {"description": "X-User-ID header required"},
    },
)
def add_favorite(payload: FavoriteAddRequest, request: Request, response: Response) -> dict:
    """
    Add an agent to user's favorites.

    X-User-ID header should contain a unique user identifier.
    For anonymous users, use a persistent UUID stored in localStorage.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        # For truly anonymous users, we'd need a client-generated ID
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header required. Use a persistent UUID from localStorage.",
        )

    repo = get_user_repo()
    agent_id = str(payload.agent_id).strip()[:100]

    is_favorite = repo.add_favorite(user_id, agent_id)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "agent_id": agent_id, "is_favorite": is_favorite}


@router.delete(
    "/favorites/{agent_id}",
    response_model=FavoriteResponse,
    responses={
        200: {"description": "Favorite removed"},
        400: {"description": "X-User-ID header required"},
    },
)
def remove_favorite(agent_id: str, request: Request, response: Response) -> dict:
    """
    Remove an agent from user's favorites.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header required.",
        )

    repo = get_user_repo()
    agent_id_clean = str(agent_id).strip()[:100]

    repo.remove_favorite(user_id, agent_id_clean)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "agent_id": agent_id_clean, "is_favorite": False}


@router.post(
    "/favorites/{agent_id}/toggle",
    response_model=FavoriteResponse,
    responses={
        200: {"description": "Favorite toggled"},
        400: {"description": "X-User-ID header required"},
    },
)
def toggle_favorite(agent_id: str, request: Request, response: Response) -> dict:
    """
    Toggle an agent's favorite status.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        raise HTTPException(
            status_code=400,
            detail="X-User-ID header required.",
        )

    repo = get_user_repo()
    agent_id_clean = str(agent_id).strip()[:100]

    is_favorite, _ = repo.toggle_favorite(user_id, agent_id_clean)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "agent_id": agent_id_clean, "is_favorite": is_favorite}


@router.get(
    "/favorites",
    response_model=FavoriteListResponse,
    responses={200: {"description": "List of favorite agent IDs"}},
)
def list_favorites(request: Request, response: Response) -> dict:
    """
    Get user's favorite agents list.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        # Return empty for anonymous instead of error
        response.headers["Cache-Control"] = "no-store"
        return {"user_id": "", "agent_ids": []}

    repo = get_user_repo()
    favorites = repo.get_favorites(user_id)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "agent_ids": list(favorites)}


@router.post(
    "/history/{agent_id}",
    response_model=HistoryRecordResponse,
    responses={200: {"description": "View recorded"}},
)
def record_view(agent_id: str, request: Request, response: Response) -> dict:
    """
    Record an agent view for history.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        response.headers["Cache-Control"] = "no-store"
        return {"user_id": "", "agent_id": agent_id, "recorded": False}

    repo = get_user_repo()
    agent_id_clean = str(agent_id).strip()[:100]

    recorded = repo.record_view(user_id, agent_id_clean)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "agent_id": agent_id_clean, "recorded": recorded}


@router.get(
    "/history",
    response_model=HistoryListResponse,
    responses={200: {"description": "List of viewed agent IDs"}},
)
def list_history(
    request: Request,
    response: Response,
    limit: int = 20,
) -> dict:
    """
    Get user's view history.
    """
    user_id = _extract_user_id(request)
    if not user_id or user_id.startswith("anonymous:"):
        response.headers["Cache-Control"] = "no-store"
        return {"user_id": "", "items": []}

    limit = max(1, min(int(limit), 100))
    repo = get_user_repo()
    history = repo.get_view_history(user_id, limit=limit)

    response.headers["Cache-Control"] = "no-store"
    return {"user_id": user_id, "items": [{"agent_id": aid} for aid in history]}


@router.get(
    "/me",
    response_model=UserInfoResponse,
    responses={200: {"description": "User information"}},
)
def get_user_info(request: Request, response: Response) -> dict:
    """
    Get current user info (derived from headers).
    """
    user_id = _extract_user_id(request)

    response.headers["Cache-Control"] = "no-store"
    return {
        "user_id": user_id,
        "is_anonymous": user_id.startswith("anonymous:") or user_id.startswith("session:"),
    }
