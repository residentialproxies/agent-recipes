"""
Agent search + detail routes.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response

from src.api.dependencies import get_search_engine_for_request, get_snapshot
from src.api.models import SearchRequest
from src.config import settings
from src.data_store import AgentsSnapshot, get_search_engine
from src.security.validators import ValidationError, validate_agent_id

router = APIRouter(prefix="/v1", tags=["agents"])


@router.get("/filters")
def filters(request: Request, response: Response) -> dict:
    engine = get_search_engine_for_request(request)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return engine.get_filter_options()


def _search_with_filters(payload: SearchRequest, snapshot: AgentsSnapshot) -> dict:
    engine = get_search_engine(snapshot=snapshot)

    query = (payload.q or "").strip()
    if not query:
        base = list(engine.agents.values())
        filtered = engine.filter_agents(
            base,
            category=payload.category,
            framework=payload.framework,
            provider=payload.provider,
            complexity=payload.complexity,
            local_only=payload.local_only,
        )
        filtered.sort(key=lambda a: (a.get("name", "") or "").lower())
    else:
        results = engine.search(query, limit=settings.max_search_results)
        filtered = engine.filter_agents(
            results,
            category=payload.category,
            framework=payload.framework,
            provider=payload.provider,
            complexity=payload.complexity,
            local_only=payload.local_only,
        )

    total = len(filtered)
    start = (payload.page - 1) * payload.page_size
    end = start + payload.page_size
    items = filtered[start:end]
    return {
        "query": query,
        "total": total,
        "page": payload.page,
        "page_size": payload.page_size,
        "items": items,
    }


@router.get("/agents")
def agents(
    request: Request,
    response: Response,
    q: str = "",
    category: Optional[str] = None,
    framework: Optional[str] = None,
    provider: Optional[str] = None,
    complexity: Optional[str] = None,
    local_only: bool = False,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    snapshot = get_snapshot(request)
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return _search_with_filters(
        SearchRequest(
            q=q,
            category=category,
            framework=framework,
            provider=provider,
            complexity=complexity,
            local_only=local_only,
            page=page,
            page_size=page_size,
        ),
        snapshot=snapshot,
    )


@router.post("/search")
def search(payload: SearchRequest, request: Request) -> dict:
    snapshot = get_snapshot(request)
    return _search_with_filters(payload, snapshot=snapshot)


@router.get("/agents/{agent_id}")
def agent_detail(agent_id: str, request: Request, response: Response) -> dict:
    try:
        agent_id = validate_agent_id(agent_id)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    engine = get_search_engine_for_request(request)
    agent = engine.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    response.headers["Cache-Control"] = "public, max-age=300"
    return agent

