"""
Agent search + detail routes.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Query, Request, Response

from src.api.dependencies import get_search_engine_for_request, get_snapshot
from src.api.models import (
    AgentListResponse,
    AgentResponse,
    FilterOptionsResponse,
    SearchRequest,
)
from src.api.observability import get_request_id
from src.config import settings
from src.data_store import AgentsSnapshot, get_search_engine
from src.exceptions import AgentNotFoundError, InvalidAgentIDError, exception_to_http_status
from src.logging_config import get_logger, log_performance
from src.security.validators import ValidationError, validate_agent_id
from src.validation import generate_seo_description

logger = get_logger(__name__)

router = APIRouter(prefix="/v1", tags=["agents"])


@router.get(
    "/filters",
    response_model=FilterOptionsResponse,
    responses={200: {"description": "Available filter options"}},
)
def filters(request: Request, response: Response) -> dict:
    start_time = time.perf_counter()
    engine = get_search_engine_for_request(request)
    response.headers["Cache-Control"] = "public, max-age=3600"
    result = engine.get_filter_options()
    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info("filters_requested", extra={"endpoint": "/v1/filters", "duration_ms": round(duration_ms, 2)})
    return result


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


def _sort_agents(items: list[dict], *, query: str, sort: str | None) -> list[dict]:
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
            except (ValueError, TypeError):
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
    start_time = time.perf_counter()
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

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "search_completed",
        extra={
            "query": query or "(empty)",
            "result_count": total,
            "page": payload.page,
            "page_size": payload.page_size,
            "duration_ms": round(duration_ms, 2),
            "category": payload.category,
            "framework": payload.framework,
            "provider": payload.provider,
        },
    )

    return {
        "query": query,
        "total": total,
        "page": payload.page,
        "page_size": payload.page_size,
        "items": items,
    }


@router.get(
    "/agents",
    response_model=AgentListResponse,
    responses={200: {"description": "List of agents matching search criteria"}},
)
def agents(
    request: Request,
    response: Response,
    q: str = Query(default="", description="Search query", examples=["rag", "chatbot", "pdf"]),
    category: list[str] | None = Query(default=None, description="Filter by category", examples=[["rag", "chatbot"]]),
    framework: list[str] | None = Query(default=None, description="Filter by framework", examples=[["langchain"]]),
    provider: list[str] | None = Query(default=None, description="Filter by LLM provider", examples=[["openai", "anthropic"]]),
    complexity: list[str] | None = Query(default=None, description="Filter by complexity", examples=[["beginner"]]),
    local_only: bool = Query(default=False, description="Only agents with local model support"),
    sort: str | None = Query(default=None, description="Sort order (e.g., '-stars', 'name')", examples=["-stars", "name"]),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, description="Results per page"),
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


@router.post(
    "/search",
    response_model=AgentListResponse,
    responses={200: {"description": "List of agents matching search criteria"}},
)
def search(payload: SearchRequest, request: Request) -> dict:
    snapshot = get_snapshot(request)
    return _search_with_filters(payload, snapshot=snapshot)


@router.get(
    "/agents/{agent_id}",
    response_model=AgentResponse,
    responses={
        200: {"description": "Agent details"},
        404: {"description": "Agent not found"},
        400: {"description": "Invalid agent ID"},
    },
)
def agent_detail(
    agent_id: str,
    request: Request,
    response: Response,
) -> dict:
    request_id = get_request_id() or "unknown"
    start_time = time.perf_counter()

    try:
        agent_id = validate_agent_id(agent_id)
    except ValidationError as exc:
        error = InvalidAgentIDError(agent_id, request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from exc

    try:
        engine = get_search_engine_for_request(request)
    except Exception as exc:
        logger.error("search_engine_init_failed", extra={"request_id": request_id, "error": str(exc)}, exc_info=True)
        raise HTTPException(status_code=500, detail="Search engine initialization failed") from exc

    agent = engine.agents.get(agent_id)
    if not agent:
        error = AgentNotFoundError(agent_id, request_id=request_id)
        logger.warning("agent_not_found", extra={"agent_id": agent_id, "request_id": request_id})
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from None

    duration_ms = (time.perf_counter() - start_time) * 1000
    logger.info(
        "agent_detail_retrieved",
        extra={
            "agent_id": agent_id,
            "request_id": request_id,
            "duration_ms": round(duration_ms, 2),
        },
    )

    # Cache agent details for 1 hour with stale-while-revalidate for 24 hours
    # Agent details are relatively static, so aggressive caching is safe
    response.headers["Cache-Control"] = "public, max-age=3600, stale-while-revalidate=86400"
    response.headers["X-Request-ID"] = request_id
    return _normalize_agent_for_api(agent)
