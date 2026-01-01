"""
FastAPI application factory.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from src.ai_selector import DailyBudget, FileTTLCache
from src.config import settings
from src.data_store import get_search_engine, load_agents
from src.repository import AgentRepo
from src.security.rate_limit import RateLimitConfig, get_rate_limiter
from src.security.validators import ValidationError

from src.api.middleware import setup_compression, setup_cors, setup_request_size_limit, setup_security_headers
from src.api.observability import ObservabilityMiddleware
from src.api.routes import agents as agents_routes
from src.api.routes import ai as ai_routes
from src.api.routes import webmanus as webmanus_routes
from src.api.state import AppState


def create_app(
    *,
    agents_path: Optional[Path] = None,
    webmanus_db_path: Optional[Path] = None,
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

    @app.exception_handler(ValidationError)
    def _validation_error(_: Request, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(exc)})

    @app.exception_handler(Exception)
    def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        _ = exc
        return JSONResponse(status_code=500, content={"error": "internal_error"})

    return app


app = create_app()
