"""
Agent Navigator - Structured Logging Configuration
==================================================
Provides JSON-formatted structured logging with request context.

Features:
- JSON output for log aggregation (ELK, Loki, Datadog)
- Request-scoped context (request_id, user_id, endpoint)
- Performance tracking (duration_ms, db_query_ms)
- Error tracking with stack traces
- Log level filtering via environment

Usage:
    from src.logging_config import get_logger, log_event

    logger = get_logger(__name__)
    logger.info("Search completed", extra={"result_count": 20})

    # Or use the helper
    log_event("search_completed", result_count=20, duration_ms=45)
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from src.config import settings


class LogLevel(str, Enum):
    """Standard log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# =============================================================================
# Context Variables (thread-safe for async)
# =============================================================================


class LogContext:
    """
    Thread-local storage for request-scoped log context.

    In async environments, use contextvars instead. This provides
    a fallback for synchronous code and compatibility with existing
    middleware.
    """

    _local = threading.local()
    _lock = threading.Lock()

    @classmethod
    def set_request_id(cls, request_id: str | None) -> None:
        """Set the current request ID."""
        if not hasattr(cls._local, "request_id"):
            cls._local.request_id = None
        cls._local.request_id = request_id

    @classmethod
    def get_request_id(cls) -> str | None:
        """Get the current request ID."""
        if not hasattr(cls._local, "request_id"):
            return None
        return cls._local.request_id

    @classmethod
    def set_user_id(cls, user_id: str | None) -> None:
        """Set the current user ID."""
        if not hasattr(cls._local, "user_id"):
            cls._local.user_id = None
        cls._local.user_id = user_id

    @classmethod
    def get_user_id(cls) -> str | None:
        """Get the current user ID."""
        if not hasattr(cls._local, "user_id"):
            return None
        return cls._local.user_id

    @classmethod
    def set_client_ip(cls, client_ip: str | None) -> None:
        """Set the current client IP."""
        if not hasattr(cls._local, "client_ip"):
            cls._local.client_ip = None
        cls._local.client_ip = client_ip

    @classmethod
    def get_client_ip(cls) -> str | None:
        """Get the current client IP."""
        if not hasattr(cls._local, "client_ip"):
            return None
        return cls._local.client_ip

    @classmethod
    def set_endpoint(cls, endpoint: str | None) -> None:
        """Set the current endpoint."""
        if not hasattr(cls._local, "endpoint"):
            cls._local.endpoint = None
        cls._local.endpoint = endpoint

    @classmethod
    def get_endpoint(cls) -> str | None:
        """Get the current endpoint."""
        if not hasattr(cls._local, "endpoint"):
            return None
        return cls._local.endpoint

    @classmethod
    def set_duration_ms(cls, duration_ms: float | None) -> None:
        """Set the current request duration."""
        if not hasattr(cls._local, "duration_ms"):
            cls._local.duration_ms = None
        cls._local.duration_ms = duration_ms

    @classmethod
    def get_duration_ms(cls) -> float | None:
        """Get the current request duration."""
        if not hasattr(cls._local, "duration_ms"):
            return None
        return cls._local.duration_ms

    @classmethod
    def clear(cls) -> None:
        """Clear all context."""
        cls._local.request_id = None
        cls._local.user_id = None
        cls._local.client_ip = None
        cls._local.endpoint = None
        cls._local.duration_ms = None

    @classmethod
    def get_all(cls) -> dict[str, Any]:
        """Get all context as a dict."""
        return {
            "request_id": cls.get_request_id(),
            "user_id": cls.get_user_id(),
            "client_ip": cls.get_client_ip(),
            "endpoint": cls.get_endpoint(),
            "duration_ms": cls.get_duration_ms(),
        }


# =============================================================================
# JSON Formatter
# =============================================================================


class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in a consistent JSON format with timestamps,
    log levels, and contextual fields.
    """

    def __init__(
        self,
        *,
        service_name: str = "agent-navigator",
        environment: str = "production",
        include_extra_fields: bool = True,
    ) -> None:
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra_fields = include_extra_fields
        self._iso_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON."""
        # Base log entry
        log_entry: dict[str, Any] = {
            "timestamp": self._format_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add source location
        if record.pathname:
            log_entry["file"] = Path(record.pathname).name
            log_entry["line"] = record.lineno
            log_entry["function"] = record.funcName

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self._format_traceback(record.exc_info),
            }

        # Add request context
        context = LogContext.get_all()
        for key, value in context.items():
            if value is not None:
                log_entry[key] = value

        # Add extra fields from the log call
        if self.include_extra_fields and hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)

        # Add any other extra attributes (not part of standard LogRecord)
        if self.include_extra_fields:
            standard_attrs = {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName",
                "process", "getMessage", "exc_info", "exc_text", "stack_info",
            }
            for key, value in record.__dict__.items():
                if key not in standard_attrs and not key.startswith("_"):
                    log_entry[key] = value

        return json.dumps(log_entry, default=self._json_serializer, ensure_ascii=False)

    def _format_timestamp(self, created: float) -> str:
        """Format Unix timestamp to ISO 8601 string."""
        dt = datetime.fromtimestamp(created, tz=timezone.utc)
        return dt.strftime(self._iso_format)

    def _format_traceback(self, exc_info: Any) -> str | None:
        """Format exception traceback."""
        if not exc_info:
            return None
        return "".join(traceback.format_exception(*exc_info))

    @staticmethod
    def _json_serializer(obj: Any) -> str:
        """Custom JSON serializer for non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        if hasattr(obj, "__dict__"):
            return str(obj)
        return str(obj)


# =============================================================================
# Console Formatter (human-readable fallback)
# =============================================================================


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable formatter for console output during development.
    """

    LEVEL_COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self) -> None:
        super().__init__()
        self._iso_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console."""
        level_color = self.LEVEL_COLORS.get(record.levelname, "")
        timestamp = self._format_timestamp(record.created)
        request_id = LogContext.get_request_id() or "-"

        base = (
            f"{level_color}{record.levelname:<8}{self.RESET} "
            f"{timestamp} "
            f"[{request_id}] "
            f"{record.name}: "
            f"{record.getMessage()}"
        )

        # Add exception info
        if record.exc_info:
            base += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return base

    def _format_timestamp(self, created: float) -> str:
        """Format Unix timestamp to ISO 8601 string."""
        dt = datetime.fromtimestamp(created, tz=timezone.utc)
        return dt.strftime(self._iso_format)


# =============================================================================
# Logger Factory
# =============================================================================


def _get_log_level() -> int:
    """Get log level from environment."""
    level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    return getattr(logging, level_str, logging.INFO)


def _should_use_json() -> bool:
    """Determine if JSON logging should be used."""
    # Explicit env var
    if os.environ.get("LOG_FORMAT", "").lower() == "console":
        return False
    if os.environ.get("LOG_FORMAT", "").lower() == "json":
        return True
    # Default to JSON in production, console in dev
    return not settings.debug_mode


_loggers: dict[str, logging.Logger] = {}
_configured = False


def configure_logging(
    *,
    level: str | int | None = None,
    service_name: str = "agent-navigator",
    environment: str = "production",
    log_format: str | None = None,
) -> None:
    """
    Configure the root logger with structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Service name for log identification
        environment: Environment label (production, staging, development)
        log_format: Format type ("json" or "console")
    """
    global _configured

    # Get the root logger
    root = logging.getLogger()
    root.setLevel(_get_log_level() if level is None else _convert_level(level))

    # Clear existing handlers
    root.handlers.clear()

    # Determine format
    use_json = _should_use_json() if log_format is None else log_format == "json"

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(_get_log_level() if level is None else _convert_level(level))

    if use_json:
        handler.setFormatter(
            StructuredFormatter(
                service_name=service_name,
                environment=environment,
            )
        )
    else:
        handler.setFormatter(ConsoleFormatter())

    root.addHandler(handler)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the configured structured format.

    Args:
        name: Logger name (usually __module__ or __name__)

    Returns:
        Configured logger instance
    """
    global _configured

    if not _configured:
        configure_logging()

    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(_get_log_level())
        _loggers[name] = logger

    return _loggers[name]


def _convert_level(level: str | int) -> int:
    """Convert log level string to int constant."""
    if isinstance(level, int):
        return level
    return getattr(logging, str(level).upper(), logging.INFO)


# =============================================================================
# Helper Functions
# =============================================================================


def log_event(
    event_name: str,
    level: str | LogLevel = LogLevel.INFO,
    **extra_fields: Any,
) -> None:
    """
    Log a structured event with additional fields.

    Convenience function for logging events with context.

    Args:
        event_name: Name of the event (used as message)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        **extra_fields: Additional structured fields to include

    Example:
        log_event("search_completed", result_count=20, duration_ms=45)
    """
    logger = get_logger("event")
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(event_name, extra=extra_fields)


def log_error(
    event_name: str,
    exc: Exception | None = None,
    **extra_fields: Any,
) -> None:
    """
    Log an error event with optional exception info.

    Args:
        event_name: Name of the error event
        exc: Exception to log
        **extra_fields: Additional structured fields
    """
    logger = get_logger("error")
    logger.error(event_name, exc_info=exc is not None, extra=extra_fields)


def log_performance(
    operation: str,
    duration_ms: float,
    **extra_fields: Any,
) -> None:
    """
    Log a performance metric.

    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        **extra_fields: Additional structured fields
    """
    log_event(
        f"{operation}_completed",
        duration_ms=round(duration_ms, 2),
        **extra_fields,
    )


# =============================================================================
# Decorators
# =============================================================================


def log_execution(
    logger_name: str | None = None,
    *,
    log_args: bool = False,
    log_result: bool = False,
    log_exceptions: bool = True,
) -> callable:
    """
    Decorator to log function execution with timing.

    Args:
        logger_name: Logger name to use (defaults to function's module)
        log_args: Include function arguments in logs
        log_result: Include return value in logs
        log_exceptions: Log exceptions with traceback

    Example:
        @log_execution()
        def search_agents(query: str) -> list[Agent]:
            ...
    """
    import time
    import functools
    from inspect import signature

    def decorator(func: callable) -> callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(logger_name or func.__module__)
            start_time = time.perf_counter()

            # Build context
            extra: dict[str, Any] = {"function": func.__name__}
            if log_args:
                sig = signature(func)
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                extra["args"] = {
                    k: str(v) if k == "self" else v
                    for k, v in bound.arguments.items()
                }

            logger.debug(f"{func.__name__}_started", extra=extra)

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000

                extra["duration_ms"] = round(duration_ms, 2)
                if log_result:
                    extra["result"] = str(result)[:500]

                logger.info(f"{func.__name__}_completed", extra=extra)
                return result

            except Exception as exc:
                duration_ms = (time.perf_counter() - start_time) * 1000
                extra["duration_ms"] = round(duration_ms, 2)
                extra["error_type"] = type(exc).__name__
                extra["error_message"] = str(exc)

                if log_exceptions:
                    logger.error(f"{func.__name__}_failed", extra=extra, exc_info=True)
                else:
                    logger.warning(f"{func.__name__}_failed", extra=extra)
                raise

        return wrapper

    return decorator


# =============================================================================
# Context Manager
# =============================================================================


class LogContextManager:
    """
    Context manager for request-scoped log context.

    Automatically sets and clears log context for a request.

    Example:
        with LogContextManager(request_id="abc123", endpoint="/v1/agents"):
            logger.info("Processing request")
    """

    def __init__(
        self,
        *,
        request_id: str | None = None,
        user_id: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        self.request_id = request_id or str(uuid.uuid4())
        self.user_id = user_id
        self.endpoint = endpoint

    def __enter__(self) -> LogContextManager:
        LogContext.set_request_id(self.request_id)
        LogContext.set_user_id(self.user_id)
        LogContext.set_endpoint(self.endpoint)
        return self

    def __exit__(self, *args: Any) -> None:
        LogContext.clear()


# =============================================================================
# Performance Tracking
# =============================================================================


class PerformanceTracker:
    """
    Context manager for tracking operation performance.

    Logs the duration and any additional metrics when the context exits.

    Example:
        with PerformanceTracker("database_query", table="agents"):
            results = db.query(...)
    """

    def __init__(
        self,
        operation: str,
        **extra_fields: Any,
    ) -> None:
        self.operation = operation
        self.extra = extra_fields
        self._start_time: float | None = None

    def __enter__(self) -> PerformanceTracker:
        self._start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        if self._start_time is None:
            return

        duration_ms = (time.perf_counter() - self._start_time) * 1000
        self.extra["duration_ms"] = round(duration_ms, 2)

        # Check if exception occurred
        if args[0] is not None:
            self.extra["error"] = str(args[1])
            get_logger("performance").warning(
                f"{self.operation}_failed",
                extra=self.extra,
            )
        else:
            get_logger("performance").info(
                f"{self.operation}_completed",
                extra=self.extra,
            )


# =============================================================================
# Module Initialization
# =============================================================================

# Auto-configure on import if not already configured
if not _configured:
    configure_logging()
