"""
WebManus (workers + consult) routes.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

import src.api as api_mod
from src.affiliate_manager import batch_inject
from src.ai_selector import (
    AISelectorError,
    AnthropicService,
    CacheEntry,
    build_webmanus_prompt,
    estimate_cost_usd,
    extract_json_object,
    extract_usage,
    make_cache_key,
    require_budget,
)
from src.api.dependencies import get_ai_budget, get_ai_cache, get_rate_limiter, get_webmanus_repo
from src.api.middleware import get_client_ip
from src.api.models import WebManusConsultRequest, WebManusConsultResponse, WebManusRecommendation
from src.config import settings

router = APIRouter(prefix="/v1", tags=["webmanus"])
logger = logging.getLogger(__name__)


def _normalize_webmanus_consult_result(
    raw: dict,
    *,
    candidate_slugs: list[str],
    candidate_meta_by_slug: dict[str, dict] | None = None,
) -> dict:
    parsed = WebManusConsultResponse.model_validate(raw)
    allowed = {s for s in candidate_slugs if s}
    meta = candidate_meta_by_slug or {}

    cleaned: list[WebManusRecommendation] = []
    seen = set()
    for rec in parsed.recommendations or []:
        if rec.slug not in allowed:
            continue
        if rec.slug in seen:
            continue
        if rec.match_score <= 0.7:
            continue
        seen.add(rec.slug)
        cleaned.append(rec)

    cleaned.sort(key=lambda r: r.match_score, reverse=True)
    cleaned = cleaned[:3]

    for rec in cleaned:
        m = meta.get(rec.slug) or {}
        rec.name = m.get("name") or rec.name
        rec.tagline = m.get("tagline") or rec.tagline

    return {
        "recommendations": [r.model_dump() for r in cleaned],
        "no_match_suggestion": parsed.no_match_suggestion or "",
    }


@router.get("/workers")
def list_workers(
    request: Request,
    response: Response,
    q: str = Query(default="", max_length=200),
    capability: str | None = Query(default=None, max_length=80),
    pricing: str | None = Query(default=None, max_length=40),
    min_score: float = Query(default=0.0, ge=0.0, le=10.0),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    repo = get_webmanus_repo(request)
    total, items = repo.search_page(
        q=q,
        capability=capability,
        pricing=pricing,
        min_score=min_score,
        limit=limit,
        offset=offset,
    )
    items = batch_inject(items)
    response.headers["Cache-Control"] = "public, max-age=300"
    return {"total": total, "items": items}


@router.get("/workers/{slug}")
def get_worker(slug: str, request: Request, response: Response) -> dict:
    repo = get_webmanus_repo(request)
    agent = repo.get_by_slug(slug)
    if not agent:
        raise HTTPException(status_code=404, detail="Worker not found")
    response.headers["Cache-Control"] = "public, max-age=300"
    return batch_inject([agent])[0]


@router.get("/capabilities")
def list_capabilities(request: Request, response: Response) -> list[str]:
    repo = get_webmanus_repo(request)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return repo.get_all_capabilities()


@router.post("/consult")
def consult(payload: WebManusConsultRequest, request: Request) -> JSONResponse:
    if not settings.enable_ai_selector:
        raise HTTPException(status_code=404, detail="AI selector disabled")
    if not api_mod.HAS_ANTHROPIC:
        raise HTTPException(status_code=503, detail="Missing anthropic dependency")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Missing ANTHROPIC_API_KEY")

    repo = get_webmanus_repo(request)
    candidates = repo.search(
        capability=payload.capability,
        pricing=payload.pricing,
        min_score=payload.min_score,
        limit=payload.max_candidates,
    )
    candidate_slugs = [(c.get("slug") or "") for c in candidates]
    candidate_meta_by_slug = {str(c.get("slug")): c for c in candidates if c.get("slug")}

    prompt = build_webmanus_prompt(payload.problem, candidates, max_agents=min(30, len(candidates)))
    cache_key = make_cache_key(
        model=settings.anthropic_model,
        query=f"webmanus_consult:{payload.problem}",
        candidate_ids=candidate_slugs,
    )
    ai_cache = get_ai_cache(request)
    ai_budget = get_ai_budget(request)

    cached = ai_cache.get(cache_key)
    if cached:
        try:
            cached_obj = json.loads(cached.text)
            if isinstance(cached_obj, dict):
                cached_obj = _normalize_webmanus_consult_result(
                    cached_obj,
                    candidate_slugs=candidate_slugs,
                    candidate_meta_by_slug=candidate_meta_by_slug,
                )
            return JSONResponse(
                content=cached_obj,
                headers={"X-Cache": "HIT", "X-Model": cached.model, "Cache-Control": "no-store"},
            )
        except Exception as exc:
            logger.warning("Ignoring invalid cached consult payload: %s", exc)

    rate_limiter = get_rate_limiter(request)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_rate_limit(client_ip, cost=3)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"error": "rate_limited", "retry_after": retry_after},
            headers={"Retry-After": str(retry_after)},
        )

    try:
        require_budget(
            budget=ai_budget,
            model=settings.anthropic_model,
            prompt=prompt,
            max_output_tokens=settings.max_llm_tokens,
        )
    except AISelectorError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    anthropic_service = AnthropicService(api_key=settings.anthropic_api_key)
    response_obj = anthropic_service.create_non_streaming(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=settings.max_llm_tokens,
        model=settings.anthropic_model,
    )
    raw_text = anthropic_service.extract_text(response_obj)
    try:
        obj = extract_json_object(raw_text)
        result = _normalize_webmanus_consult_result(
            obj,
            candidate_slugs=candidate_slugs,
            candidate_meta_by_slug=candidate_meta_by_slug,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Invalid model JSON: {exc}") from exc

    usage = extract_usage(response_obj)
    cost_usd = (
        estimate_cost_usd(
            model=settings.anthropic_model,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
        )
        if usage
        else 0.0
    )

    ai_budget.add_spend(cost_usd)
    ai_cache.set(
        cache_key,
        CacheEntry(
            created_at=time.time(),
            model=settings.anthropic_model,
            text=json.dumps(result, ensure_ascii=False),
            usage=usage,
            cost_usd=cost_usd,
        ),
    )

    return JSONResponse(
        content=result,
        headers={"X-Cache": "MISS", "X-Model": settings.anthropic_model, "Cache-Control": "no-store"},
    )


@router.post("/consult/stream")
def consult_stream(payload: WebManusConsultRequest, request: Request) -> StreamingResponse:
    if not settings.enable_ai_selector:
        raise HTTPException(status_code=404, detail="AI selector disabled")
    if not api_mod.HAS_ANTHROPIC:
        raise HTTPException(status_code=503, detail="Missing anthropic dependency")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Missing ANTHROPIC_API_KEY")

    repo = get_webmanus_repo(request)
    candidates = repo.search(
        capability=payload.capability,
        pricing=payload.pricing,
        min_score=payload.min_score,
        limit=payload.max_candidates,
    )
    candidate_slugs = [(c.get("slug") or "") for c in candidates]
    candidate_meta_by_slug = {str(c.get("slug")): c for c in candidates if c.get("slug")}
    prompt = build_webmanus_prompt(payload.problem, candidates, max_agents=min(30, len(candidates)))
    cache_key = make_cache_key(
        model=settings.anthropic_model,
        query=f"webmanus_consult:{payload.problem}",
        candidate_ids=candidate_slugs,
    )
    ai_cache = get_ai_cache(request)
    ai_budget = get_ai_budget(request)
    cached = ai_cache.get(cache_key)

    def _sse(data: Any, *, event: str = "message") -> bytes:
        line = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {line}\n\n".encode()

    def generator():
        if cached:
            try:
                cached_obj = json.loads(cached.text)
                if isinstance(cached_obj, dict):
                    cached_obj = _normalize_webmanus_consult_result(
                        cached_obj,
                        candidate_slugs=candidate_slugs,
                        candidate_meta_by_slug=candidate_meta_by_slug,
                    )
                yield _sse({"cached": True, "result": cached_obj, "model": cached.model}, event="done")
            except Exception:
                yield _sse({"cached": True, "error": "cache_decode_failed"}, event="error")
            return

        rate_limiter = get_rate_limiter(request)
        client_ip = get_client_ip(request)
        allowed, retry_after = rate_limiter.check_rate_limit(client_ip, cost=3)
        if not allowed:
            yield _sse({"error": "rate_limited", "retry_after": retry_after}, event="error")
            return

        try:
            require_budget(
                budget=ai_budget,
                model=settings.anthropic_model,
                prompt=prompt,
                max_output_tokens=settings.max_llm_tokens,
            )
        except AISelectorError as exc:
            yield _sse({"error": str(exc)}, event="error")
            return

        anthropic_service = AnthropicService(api_key=settings.anthropic_api_key)
        chunks: list[str] = []
        response_obj = None
        try:
            with anthropic_service.create_streaming(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.max_llm_tokens,
                model=settings.anthropic_model,
            ) as stream:
                for text in stream.text_stream:
                    if not text:
                        continue
                    chunks.append(text)
                    yield _sse({"cached": False, "delta": text, "model": settings.anthropic_model}, event="delta")
                response_obj = stream.get_final_message()
        except Exception as exc:
            yield _sse({"error": "Upstream error", "detail": str(exc)}, event="error")
            return

        raw_text = "".join(chunks)
        try:
            obj = extract_json_object(raw_text)
            result = _normalize_webmanus_consult_result(
                obj,
                candidate_slugs=candidate_slugs,
                candidate_meta_by_slug=candidate_meta_by_slug,
            )
        except Exception as exc:
            yield _sse({"error": "Invalid model JSON", "detail": str(exc)}, event="error")
            return

        usage = anthropic_service.extract_usage(response_obj) if response_obj is not None else {}
        cost_usd = (
            estimate_cost_usd(
                model=settings.anthropic_model,
                input_tokens=int(usage.get("input_tokens") or 0),
                output_tokens=int(usage.get("output_tokens") or 0),
            )
            if usage
            else 0.0
        )

        ai_budget.add_spend(cost_usd)
        ai_cache.set(
            cache_key,
            CacheEntry(
                created_at=time.time(),
                model=settings.anthropic_model,
                text=json.dumps(result, ensure_ascii=False),
                usage=usage,
                cost_usd=cost_usd,
            ),
        )

        yield _sse(
            {"cached": False, "done": True, "result": result, "usage": usage, "cost_usd": cost_usd}, event="done"
        )

    return StreamingResponse(generator(), media_type="text/event-stream")
