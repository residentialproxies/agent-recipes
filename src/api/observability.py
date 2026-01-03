"""
Observability utilities for API request tracking.

Provides request ID generation and middleware for distributed tracing,
logging correlation, and security monitoring.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.api.middleware import get_client_ip as get_client_ip_safe

# Context variables for request-scoped data
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_client_ip_ctx: ContextVar[str | None] = ContextVar("client_ip", default=None)
_request_start_ctx: ContextVar[float | None] = ContextVar("request_start", default=None)

logger = logging.getLogger(__name__)


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.

    Uses UUID4 for uniqueness. Format: 8-4-4-4-12 hexadecimal characters.
    """
    return str(uuid.uuid4())


def get_request_id() -> str | None:
    """Get the current request ID from context."""
    return _request_id_ctx.get()


def get_client_ip() -> str | None:
    """Get the current client IP from context."""
    return _client_ip_ctx.get()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request observability and tracing.

    Adds request ID tracking, timing metrics, and structured logging
    to all API requests. Enables distributed tracing correlation.

    Features:
    - Generates unique request ID (or uses X-Request-ID header)
    - Tracks request duration
    - Logs request/response metadata
    - Adds request ID to response headers
    - Captures client IP for security monitoring
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        self._logger = logging.getLogger(__name__)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or retrieve request ID
        request_id = request.headers.get("x-request-id") or generate_request_id()

        # Extract client IP (proxy-safe, honors TRUST_PROXY_HEADERS/TRUSTED_PROXY_IPS)
        client_ip = get_client_ip_safe(request)

        # Set context variables
        _request_id_ctx.set(request_id)
        _client_ip_ctx.set(client_ip)
        _request_start_ctx.set(time.perf_counter())

        # Log request start
        self._logger.info(
            "request_started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            start_time = _request_start_ctx.get()
            duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            # Log completion
            self._logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url.path),
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            return response

        except Exception as exc:
            # Calculate duration even for errors
            start_time = _request_start_ctx.get()
            duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0

            # Log error with context
            self._logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url.path),
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "duration_ms": round(duration_ms, 2),
                },
                exc_info=True,
            )
            raise


async def log_request_summary(
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    extra: dict | None = None,
) -> None:
    """
    Log a request summary for analytics and monitoring.

    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
        extra: Additional fields to include in log
    """
    log_data = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    if extra:
        log_data.update(extra)

    logger.info("request_summary", extra=log_data)


def setup_observability_middleware(app: ASGIApp) -> ASGIApp:
    """
    Setup observability middleware on an ASGI app.

    This is a convenience function for adding the middleware
    during application initialization.
    """
    # The middleware wraps the app, so we need to return the wrapped version
    # In FastAPI, this is typically done via app.add_middleware()
    return app
