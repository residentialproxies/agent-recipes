"""
Observability utilities for API request tracking.

Provides request ID generation and middleware for distributed tracing,
logging correlation, and security monitoring with structured JSON logging.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from contextvars import ContextVar
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.api.middleware import get_client_ip as get_client_ip_safe
from src.logging_config import (
    LogContext,
    LogContextManager,
    PerformanceTracker,
    configure_logging,
    get_logger,
    log_error,
    log_event,
    log_performance,
)

# Context variables for request-scoped data (async-safe)
_request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
_client_ip_ctx: ContextVar[str | None] = ContextVar("client_ip", default=None)
_request_start_ctx: ContextVar[float | None] = ContextVar("request_start", default=None)
_user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)

# Module logger
logger = get_logger(__name__)


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


def get_user_id() -> str | None:
    """Get the current user ID from context."""
    return _user_id_ctx.get()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for request observability and tracing.

    Adds request ID tracking, timing metrics, and structured logging
    to all API requests. Enables distributed tracing correlation.

    Features:
    - Generates unique request ID (or uses X-Request-ID header)
    - Tracks request duration
    - Logs request/response metadata in JSON format
    - Adds request ID to response headers
    - Captures client IP for security monitoring
    - Performance metrics for slow requests

    Log format:
        {
            "timestamp": "2025-01-03T10:00:00Z",
            "level": "INFO",
            "request_id": "abc123",
            "message": "request_completed",
            "endpoint": "/v1/agents",
            "duration_ms": 45,
            "result_count": 20
        }
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        slow_request_threshold_ms: float = 1000.0,
        log_request_body: bool = False,
        log_response_body: bool = False,
    ) -> None:
        """
        Initialize the middleware.

        Args:
            app: ASGI application
            slow_request_threshold_ms: Threshold for logging slow requests (default: 1000ms)
            log_request_body: Include request body in logs (default: False)
            log_response_body: Include response body in logs (default: False)
        """
        super().__init__(app)
        self._logger = get_logger(__name__)
        self.slow_request_threshold_ms = slow_request_threshold_ms
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or retrieve request ID
        request_id = request.headers.get("x-request-id") or generate_request_id()

        # Extract client IP (proxy-safe, honors TRUST_PROXY_HEADERS/TRUSTED_PROXY_IPS)
        client_ip = get_client_ip_safe(request)

        # Set context variables (both contextvar and LogContext for compatibility)
        _request_id_ctx.set(request_id)
        _client_ip_ctx.set(client_ip)
        _user_id_ctx.set(None)
        _request_start_ctx.set(time.perf_counter())

        LogContext.set_request_id(request_id)
        LogContext.set_client_ip(client_ip)  # type: ignore[attr-defined]
        LogContext.set_user_id(None)
        LogContext.set_endpoint(str(request.url.path))

        # Prepare request metadata
        request_meta: dict[str, Any] = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
        }

        # Add query params if present (sanitize sensitive params)
        if request.url.query:
            request_meta["query_params"] = self._sanitize_query_params(str(request.url.query))

        # Log request start
        self._logger.info("request_started", extra=request_meta)

        # Process request with performance tracking
        endpoint_name = f"{request.method} {request.url.path}"
        with PerformanceTracker(
            "api_request",
            endpoint=endpoint_name,
            request_id=request_id,
        ):
            try:
                response = await call_next(request)

                # Calculate duration
                start_time = _request_start_ctx.get()
                duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0

                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id

                # Prepare response metadata
                response_meta: dict[str, Any] = {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }

                # Add cache hit info if available
                if hasattr(request.state, "cache_hit"):
                    response_meta["cache_hit"] = request.state.cache_hit

                # Add result count if available (set by route handlers)
                if hasattr(request.state, "result_count"):
                    response_meta["result_count"] = request.state.result_count

                # Log completion
                if duration_ms >= self.slow_request_threshold_ms:
                    response_meta["slow_request"] = True
                    self._logger.warning("request_completed_slow", extra=response_meta)
                else:
                    self._logger.info("request_completed", extra=response_meta)

                return response

            except Exception as exc:
                # Calculate duration even for errors
                start_time = _request_start_ctx.get()
                duration_ms = (time.perf_counter() - start_time) * 1000 if start_time else 0

                # Import for structured error handling
                from src.exceptions import AgentNavigatorError, handle_exception

                # Log error with full context
                error_meta: dict[str, Any] = {
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "duration_ms": round(duration_ms, 2),
                }

                # Use structured logging for custom exceptions
                if isinstance(exc, AgentNavigatorError):
                    exc.request_id = request_id
                    error_meta.update({
                        "error_code": exc.error_code,
                        "error_detail": exc.detail,
                    })
                    exc.log()
                else:
                    # Use handler for unknown exceptions
                    error_dict = handle_exception(exc, request_id=request_id)
                    error_meta["error_detail"] = error_dict.get("detail")
                    self._logger.error("request_failed", extra=error_meta, exc_info=True)

                raise

    def _sanitize_query_params(self, query: str) -> str:
        """
        Sanitize query parameters for logging (remove sensitive values).

        Args:
            query: Raw query string

        Returns:
            Sanitized query string with sensitive values redacted
        """
        sensitive_params = {"api_key", "token", "password", "secret", "auth"}
        parts = query.split("&")
        sanitized = []
        for part in parts:
            if "=" in part:
                key, _ = part.split("=", 1)
                if key.lower() in sensitive_params:
                    sanitized.append(f"{key}=***REDACTED***")
                    continue
            sanitized.append(part)
        return "&".join(sanitized)


class DatabaseMetrics:
    """
    Helper for tracking database query performance.

    Usage in route handlers:
        db_metrics = DatabaseMetrics()
        with db_metrics.track_query("get_agent"):
            agent = db.query(...)
    """

    def __init__(self, *, slow_threshold_ms: float = 100.0) -> None:
        """
        Initialize database metrics tracker.

        Args:
            slow_threshold_ms: Threshold for logging slow queries
        """
        self._logger = get_logger("database")
        self.slow_threshold_ms = slow_threshold_ms
        self._query_count = 0
        self._total_duration_ms = 0.0

    def track_query(self, operation: str, **extra_fields: Any) -> PerformanceTracker:
        """
        Create a performance tracker for a database query.

        Args:
            operation: Name of the query operation
            **extra_fields: Additional fields to log

        Returns:
            PerformanceTracker context manager
        """
        self._query_count += 1
        fields = {"operation": operation, **extra_fields}
        return PerformanceTracker("database_query", **fields)

    def log_summary(self, **extra_fields: Any) -> None:
        """
        Log a summary of all database queries in the request.

        Args:
            **extra_fields: Additional fields to include
        """
        if self._query_count == 0:
            return

        self._logger.info(
            "database_query_summary",
            extra={
                "query_count": self._query_count,
                "total_duration_ms": round(self._total_duration_ms, 2),
                **extra_fields,
            },
        )


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
    log_data: dict[str, Any] = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }
    if extra:
        log_data.update(extra)

    logger.info("request_summary", extra=log_data)


def setup_observability_middleware(
    app: ASGIApp,
    *,
    slow_request_threshold_ms: float = 1000.0,
    log_request_body: bool = False,
    log_response_body: bool = False,
) -> ASGIApp:
    """
    Setup observability middleware on an ASGI app.

    This is a convenience function for adding the middleware
    during application initialization.

    Args:
        app: ASGI application
        slow_request_threshold_ms: Threshold for logging slow requests
        log_request_body: Include request body in logs
        log_response_body: Include response body in logs

    Returns:
        The wrapped application (for FastAPI, use app.add_middleware instead)
    """
    # For FastAPI, use: app.add_middleware(ObservabilityMiddleware, ...)
    middleware = ObservabilityMiddleware(
        app,
        slow_request_threshold_ms=slow_request_threshold_ms,
        log_request_body=log_request_body,
        log_response_body=log_response_body,
    )
    return middleware


# Re-export logging helpers for convenience
__all__ = [
    "generate_request_id",
    "get_request_id",
    "get_client_ip",
    "get_user_id",
    "ObservabilityMiddleware",
    "DatabaseMetrics",
    "log_request_summary",
    "setup_observability_middleware",
    # Logging helpers
    "LogContextManager",
    "PerformanceTracker",
    "log_event",
    "log_error",
    "log_performance",
    "get_logger",
    "configure_logging",
]
