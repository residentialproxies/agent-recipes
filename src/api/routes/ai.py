"""
AI selector routes.
"""

from __future__ import annotations

import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

import src.api as api_mod
from src.ai_selector import (
    AISelectorError,
    AnthropicService,
    CacheEntry,
    build_ai_selector_prompt,
    estimate_cost_usd,
    make_cache_key,
    require_budget,
    sanitize_final_text,
)
from src.api.dependencies import get_ai_budget, get_ai_cache, get_rate_limiter, get_snapshot
from src.api.middleware import get_client_ip
from src.api.observability import get_request_id
from src.api.models import AISelectRequest, AISelectResponse
from src.config import settings
from src.circuit_breaker import CircuitBreakerOpenError
from src.data_store import get_search_engine
from src.exceptions import (
    AgentNavigatorError,
    APIConnectionError,
    APITimeoutError,
    BudgetExceededError,
    CircuitBreakerOpenError as CircuitBreakerOpenErrorExt,
    MissingAPIKeyError,
    RateLimitError,
    exception_to_http_status,
    handle_exception,
)

from src.logging_config import get_logger, LogLevel

logger = get_logger(__name__)

router = APIRouter(prefix="/v1/ai", tags=["ai"])


def _ai_candidates(payload: AISelectRequest, snapshot) -> tuple[list[dict], list[str]]:
    engine = get_search_engine(snapshot=snapshot)
    candidates = engine.search(payload.query, limit=payload.max_candidates)
    candidates = engine.filter_agents(
        candidates,
        category=payload.category,
        framework=payload.framework,
        provider=payload.provider,
        complexity=payload.complexity,
        local_only=payload.local_only,
    )
    candidate_ids = [(a.get("id") or "") for a in candidates][: payload.max_candidates]
    return candidates, candidate_ids


@router.post(
    "/select",
    response_model=AISelectResponse,
    responses={
        200: {"description": "AI selection result"},
        402: {"description": "Budget exceeded"},
        404: {"description": "AI selector disabled"},
        429: {"description": "Rate limited"},
        503: {"description": "Service unavailable"},
    },
)
def ai_select(payload: AISelectRequest, request: Request) -> JSONResponse:
    request_id = get_request_id() or "unknown"

    if not settings.enable_ai_selector:
        error = AgentNavigatorError("AI selector disabled", request_id=request_id)
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from None

    if not api_mod.HAS_ANTHROPIC:
        error = AgentNavigatorError("Missing anthropic dependency", request_id=request_id)
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from None

    if not settings.anthropic_api_key:
        error = MissingAPIKeyError("anthropic", env_var="ANTHROPIC_API_KEY", request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from None

    rate_limiter = get_rate_limiter(request)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_rate_limit(client_ip, cost=3)
    if not allowed:
        error = RateLimitError(retry_after=retry_after, request_id=request_id)
        error.log()
        return JSONResponse(
            status_code=exception_to_http_status(error),
            content=error.to_dict(),
            headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
        )

    snapshot = get_snapshot(request)
    candidates, candidate_ids = _ai_candidates(payload, snapshot=snapshot)
    prompt = build_ai_selector_prompt(payload.query, candidates, max_agents=payload.max_candidates)
    cache_key = make_cache_key(model=settings.anthropic_model, query=payload.query, candidate_ids=candidate_ids)
    ai_cache = get_ai_cache(request)
    ai_budget = get_ai_budget(request)

    cached = ai_cache.get(cache_key)
    if cached:
        return JSONResponse(
            content={
                "cached": True,
                "model": cached.model,
                "text": cached.text,
                "usage": cached.usage,
                "cost_usd": cached.cost_usd,
            },
            headers={"X-Request-ID": request_id},
        )

    try:
        require_budget(
            budget=ai_budget,
            model=settings.anthropic_model,
            prompt=prompt,
            max_output_tokens=settings.max_llm_tokens,
        )
    except AISelectorError as exc:
        error = BudgetExceededError(request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from exc

    try:
        anthropic_service = AnthropicService(api_key=settings.anthropic_api_key)
        response = anthropic_service.create_non_streaming(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=settings.max_llm_tokens,
            model=settings.anthropic_model,
        )
        raw_text = anthropic_service.extract_text(response)
        safe_text = sanitize_final_text(raw_text)
        usage = anthropic_service.extract_usage(response)
    except (CircuitBreakerOpenError, CircuitBreakerOpenErrorExt) as exc:
        error = CircuitBreakerOpenErrorExt("anthropic", retry_after_seconds=60, request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from exc
    except (TimeoutError, APITimeoutError) as exc:
        error = APITimeoutError("anthropic", timeout_seconds=settings.llm_timeout_seconds, request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from exc
    except (ConnectionError, APIConnectionError) as exc:
        error = APIConnectionError("anthropic", reason=str(exc), request_id=request_id)
        error.log()
        raise HTTPException(
            status_code=exception_to_http_status(error),
            detail=error.to_dict(),
        ) from exc
    except Exception as exc:
        error = handle_exception(exc, request_id=request_id)
        logger.error("AI select error", extra={"request_id": request_id, "error_type": type(exc).__name__}, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=error,
        ) from exc

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
            text=safe_text,
            usage=usage,
            cost_usd=cost_usd,
        ),
    )

    return JSONResponse(
        content={
            "cached": False,
            "model": settings.anthropic_model,
            "text": safe_text,
            "usage": usage,
            "cost_usd": cost_usd,
        },
        headers={"X-Request-ID": request_id},
    )


@router.post(
    "/select/stream",
    responses={
        200: {"description": "Server-Sent Events stream", "content": {"text/event-stream": {}}},
        402: {"description": "Budget exceeded"},
        404: {"description": "AI selector disabled"},
        429: {"description": "Rate limited"},
        503: {"description": "Service unavailable"},
    },
)
def ai_select_stream(payload: AISelectRequest, request: Request) -> StreamingResponse:
    if not settings.enable_ai_selector:
        raise HTTPException(status_code=404, detail="AI selector disabled")
    if not api_mod.HAS_ANTHROPIC:
        raise HTTPException(status_code=503, detail="Missing anthropic dependency")
    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Missing ANTHROPIC_API_KEY")

    rate_limiter = get_rate_limiter(request)
    client_ip = get_client_ip(request)
    allowed, retry_after = rate_limiter.check_rate_limit(client_ip, cost=3)
    if not allowed:
        raise HTTPException(status_code=429, detail=f"Rate limited. Retry after {retry_after}s.")

    snapshot = get_snapshot(request)
    candidates, candidate_ids = _ai_candidates(payload, snapshot=snapshot)
    prompt = build_ai_selector_prompt(payload.query, candidates, max_agents=payload.max_candidates)
    cache_key = make_cache_key(model=settings.anthropic_model, query=payload.query, candidate_ids=candidate_ids)
    ai_cache = get_ai_cache(request)
    ai_budget = get_ai_budget(request)
    cached = ai_cache.get(cache_key)

    def _sse(data: Any, *, event: str = "message") -> bytes:
        line = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {line}\n\n".encode()

    def generator():
        if cached:
            yield _sse({"cached": True, "delta": cached.text, "model": cached.model}, event="delta")
            yield _sse({"cached": True, "done": True}, event="done")
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
        except (CircuitBreakerOpenError, CircuitBreakerOpenErrorExt) as exc:
            error = CircuitBreakerOpenErrorExt("anthropic", retry_after_seconds=60, request_id=request_id)
            error.log()
            yield _sse(error.to_dict(), event="error")
            return
        except (TimeoutError, APITimeoutError) as exc:
            error = APITimeoutError("anthropic", timeout_seconds=settings.llm_timeout_seconds, request_id=request_id)
            error.log()
            yield _sse(error.to_dict(), event="error")
            return
        except (ConnectionError, APIConnectionError) as exc:
            error = APIConnectionError("anthropic", reason=str(exc), request_id=request_id)
            error.log()
            yield _sse(error.to_dict(), event="error")
            return
        except Exception as exc:
            error = handle_exception(exc, request_id=request_id)
            logger.error("AI stream error", extra={"request_id": request_id, "error_type": type(exc).__name__}, exc_info=True)
            yield _sse(error, event="error")
            return

        raw_text = "".join(chunks)
        safe_text = sanitize_final_text(raw_text)
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
                text=safe_text,
                usage=usage,
                cost_usd=cost_usd,
            ),
        )

        yield _sse(
            {"cached": False, "done": True, "text": safe_text, "usage": usage, "cost_usd": cost_usd}, event="done"
        )

    return StreamingResponse(generator(), media_type="text/event-stream")
