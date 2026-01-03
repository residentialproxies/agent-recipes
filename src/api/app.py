"""
FastAPI application factory.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.ai_selector import DailyBudget, FileTTLCache
from src.api.middleware import setup_compression, setup_cors, setup_request_size_limit, setup_security_headers
from src.api.observability import ObservabilityMiddleware, generate_request_id, get_request_id
from src.api.routes import agents as agents_routes
from src.api.routes import ai as ai_routes
from src.api.routes import webmanus as webmanus_routes
from src.api.state import AppState
from src.config import settings
from src.data_store import get_search_engine, load_agents
from src.repository import AgentRepo
from src.security.rate_limit import RateLimitConfig, get_rate_limiter
from src.security.validators import ValidationError


def create_app(
    *,
    agents_path: Path | None = None,
    webmanus_db_path: Path | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        snap = load_agents(path=agents_path)
        repo = AgentRepo(str(webmanus_db_path or settings.webmanus_db_path))
        app.state.state = AppState(snapshot=snap, webmanus_repo=repo)
        get_search_engine(snapshot=snap)
        yield

    app = FastAPI(
        title="Agent Navigator API",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    setup_compression(app)
    setup_cors(app)
    setup_security_headers(app)
    setup_request_size_limit(app)

    # Observability middleware (must be added last to wrap all others)
    app.add_middleware(ObservabilityMiddleware)

    # Runtime caches for AI selector
    app.state.ai_cache = FileTTLCache(settings.ai_cache_path, ttl_seconds=settings.ai_cache_ttl_seconds)
    app.state.ai_budget = DailyBudget(settings.ai_budget_path, daily_budget_usd=settings.ai_daily_budget_usd)
    app.state.rate_limiter = get_rate_limiter(
        config=RateLimitConfig(
            requests_per_window=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
    )

    @app.get("/v1/health")
    def health(response: Response) -> dict:
        response.headers["Cache-Control"] = "no-store"
        return {"ok": True}

    app.include_router(agents_routes.router)
    app.include_router(ai_routes.router)
    app.include_router(webmanus_routes.router)

    def _error_headers(request: Request) -> dict[str, str]:
        # Ensure clients always get a request id for correlation, even on errors.
        rid = request.headers.get("x-request-id") or get_request_id() or generate_request_id()
        return {"X-Request-ID": rid, "Cache-Control": "no-store"}

    @app.exception_handler(ValidationError)
    def _validation_error(request: Request, exc: ValidationError) -> JSONResponse:
        # Keep a stable envelope and add request correlation headers.
        return JSONResponse(status_code=400, content={"error": str(exc)}, headers=_error_headers(request))

    @app.exception_handler(Exception)
    def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # ObservabilityMiddleware logs the exception; we still return a safe, stable envelope.
        _ = exc
        return JSONResponse(status_code=500, content={"error": "internal_error"}, headers=_error_headers(request))

    return app


app = create_app()
