"""
Agent search + detail routes.
"""

from __future__ import annotations

from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Request, Response

from src.api.dependencies import get_search_engine_for_request, get_snapshot
from src.api.models import SearchRequest
from src.config import settings
from src.data_store import AgentsSnapshot, get_search_engine
from src.security.validators import ValidationError, validate_agent_id
from src.validation import generate_seo_description

router = APIRouter(prefix="/v1", tags=["agents"])


@router.get("/filters")
def filters(request: Request, response: Response) -> dict:
    engine = get_search_engine_for_request(request)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return engine.get_filter_options()


def _normalize_agent_for_api(agent: dict) -> dict:
    out = dict(agent)

    description = str(out.get("description") or "").strip()
    if not description:
        out["description"] = generate_seo_description(out)[:180]

    # Back-compat alias (some clients might still send/expect github_stars)
    if out.get("stars") is None and out.get("github_stars") is not None:
        out["stars"] = out.get("github_stars")

    out.setdefault("frameworks", [])
    out.setdefault("llm_providers", [])
    out.setdefault("tags", [])
    out.setdefault("languages", [])

    return out


def _sort_agents(items: list[dict], *, query: str, sort: Optional[str]) -> list[dict]:
    if not sort:
        return items if query else sorted(items, key=lambda a: (a.get("name") or "").lower())

    sort_key = sort.strip()
    if sort_key in ("relevance", "+relevance", "-relevance"):
        return items if query else sorted(items, key=lambda a: (a.get("name") or "").lower())

    descending = sort_key.startswith("-")
    if descending:
        sort_key = sort_key[1:]

    def name_key(a: dict) -> str:
        return (a.get("name") or "").lower()

    if sort_key == "name":
        return sorted(items, key=name_key, reverse=descending)

    if sort_key in ("stars", "updated_at"):
        def numeric(a: dict) -> int:
            value = a.get(sort_key)
            if value is None:
                return -1
            try:
                return int(value)
            except Exception:
                return -1

        # Default to descending for stars/updated_at unless user explicitly uses "+key"
        descending_final = not sort.strip().startswith("+")
        if descending:
            descending_final = True
        if sort.strip().startswith("+"):
            descending_final = False

        if descending_final:
            return sorted(items, key=lambda a: (-numeric(a), name_key(a)))
        return sorted(items, key=lambda a: (numeric(a), name_key(a)))

    if sort_key == "category":
        return sorted(items, key=lambda a: (str(a.get("category") or ""), name_key(a)), reverse=descending)

    # Unknown sort => no-op
    return items


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

    filtered = _sort_agents(filtered, query=query, sort=payload.sort)

    total = len(filtered)
    start = (payload.page - 1) * payload.page_size
    end = start + payload.page_size
    items = [_normalize_agent_for_api(a) for a in filtered[start:end]]
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
    category: Optional[List[str]] = Query(default=None),
    framework: Optional[List[str]] = Query(default=None),
    provider: Optional[List[str]] = Query(default=None),
    complexity: Optional[List[str]] = Query(default=None),
    local_only: bool = False,
    sort: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
) -> dict:
    snapshot = get_snapshot(request)
    # Cache for 1 hour with stale-while-revalidate for 24 hours
    # This improves performance while keeping data relatively fresh
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"

    # Clamp to keep responses bounded without rejecting large client values.
    page_size = min(int(page_size), 100)

    return _search_with_filters(
        SearchRequest(
            q=q,
            category=category,
            framework=framework,
            provider=provider,
            complexity=complexity,
            local_only=local_only,
            sort=sort,
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
    # Cache agent details for 1 hour with stale-while-revalidate for 24 hours
    # Agent details are relatively static, so aggressive caching is safe
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    return _normalize_agent_for_api(agent)
