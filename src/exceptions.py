"""
Centralized exception hierarchy for Agent Navigator.

Provides specific exception types for different error scenarios,
enabling better error handling and user-friendly error messages.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Base Exception
# =============================================================================


class AgentNavigatorError(RuntimeError):
    """
    Base exception for all Agent Navigator errors.

    Attributes:
        message: Human-readable error message.
        detail: Additional error details (optional).
        error_code: Machine-readable error code.
        request_id: Unique identifier for the request (optional).
    """

    def __init__(
        self,
        message: str,
        *,
        detail: str | None = None,
        error_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail
        self.error_code = error_code or self._default_error_code()
        self.request_id = request_id or self._generate_request_id()

    def _default_error_code(self) -> str:
        """Generate default error code from class name."""
        return f"agent_navigator_{self.__class__.__name__.lower()}"

    def _generate_request_id(self) -> str:
        """Generate request ID if not provided."""
        return str(uuid.uuid4())

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to API response format."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.detail:
            result["detail"] = self.detail
        if self.request_id:
            result["request_id"] = self.request_id
        return result

    def __str__(self) -> str:
        if self.detail:
            return f"{self.message}: {self.detail}"
        return self.message

    def log(self, level: int = logging.ERROR) -> None:
        """Log the exception with structured data."""
        logger.log(
            level,
            self.message,
            extra={
                "error_code": self.error_code,
                "detail": self.detail,
                "request_id": self.request_id,
                "exception_type": self.__class__.__name__,
            },
        )


# =============================================================================
# Input Validation Errors
# =============================================================================


class ValidationError(AgentNavigatorError):
    """
    Raised when input validation fails.

    HTTP Status: 400 Bad Request
    """

    def __init__(
        self,
        message: str,
        *,
        field: str | None = None,
        detail: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.field = field
        full_message = f"{field}: {message}" if field else message
        super().__init__(
            full_message,
            detail=detail,
            error_code="validation_error",
            request_id=request_id,
        )


class InvalidAgentIDError(ValidationError):
    """Raised when agent ID is invalid."""

    def __init__(
        self,
        agent_id: str,
        *,
        reason: str = "Invalid format",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message="Invalid agent ID",
            field="agent_id",
            detail=f"{reason}: {agent_id!r}",
            request_id=request_id,
        )
        self.agent_id = agent_id


class InvalidQueryError(ValidationError):
    """Raised when search query is invalid."""

    def __init__(
        self,
        query: str,
        *,
        reason: str = "Query must be a non-empty string",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message="Invalid search query",
            field="query",
            detail=f"{reason}: {query!r}",
            request_id=request_id,
        )
        self.query = query


class InvalidURLError(ValidationError):
    """Raised when URL validation fails."""

    def __init__(
        self,
        url: str,
        *,
        reason: str = "Invalid URL format",
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message="Invalid URL",
            field="url",
            detail=f"{reason}: {url!r}",
            request_id=request_id,
        )
        self.url = url


class MissingRequiredFieldError(ValidationError):
    """Raised when a required field is missing."""

    def __init__(
        self,
        field_name: str,
        *,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message="Missing required field",
            field=field_name,
            detail=f"Field '{field_name}' is required",
            request_id=request_id,
        )


# =============================================================================
# Not Found Errors
# =============================================================================


class NotFoundError(AgentNavigatorError):
    """
    Raised when a requested resource is not found.

    HTTP Status: 404 Not Found
    """

    def __init__(
        self,
        message: str,
        *,
        resource_type: str | None = None,
        resource_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        detail = None
        if resource_type and resource_id:
            detail = f"{resource_type} with ID {resource_id!r} not found"
        super().__init__(
            message,
            detail=detail,
            error_code="not_found",
            request_id=request_id,
        )


class AgentNotFoundError(NotFoundError):
    """Raised when an agent is not found."""

    def __init__(
        self,
        agent_id: str,
        *,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message="Agent not found",
            resource_type="Agent",
            resource_id=agent_id,
            request_id=request_id,
        )
        self.agent_id = agent_id


class SnapshotNotFoundError(NotFoundError):
    """Raised when a data snapshot is not found."""

    def __init__(
        self,
        snapshot_id: str | None = None,
        *,
        request_id: str | None = None,
    ) -> None:
        message = "Snapshot not found"
        if snapshot_id:
            message = f"Snapshot {snapshot_id!r} not found"
        super().__init__(
            message,
            resource_type="Snapshot",
            resource_id=snapshot_id,
            request_id=request_id,
        )
        self.snapshot_id = snapshot_id


# =============================================================================
# Rate Limiting Errors
# =============================================================================


class RateLimitError(AgentNavigatorError):
    """
    Raised when rate limit is exceeded.

    HTTP Status: 429 Too Many Requests
    """

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        *,
        retry_after: int | None = None,
        limit: int | None = None,
        window: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.retry_after = retry_after
        self.limit = limit
        self.window = window
        detail_parts = []
        if retry_after:
            detail_parts.append(f"Retry after {retry_after}s")
        if limit and window:
            detail_parts.append(f"Limit: {limit} requests per {window}s")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            error_code="rate_limited",
            request_id=request_id,
        )


class BudgetExceededError(RateLimitError):
    """Raised when daily budget is exceeded."""

    def __init__(
        self,
        *,
        budget_usd: float | None = None,
        spent_usd: float | None = None,
        request_id: str | None = None,
    ) -> None:
        message = "Daily AI budget exceeded"
        detail_parts = []
        if budget_usd is not None:
            detail_parts.append(f"Budget: ${budget_usd:.2f}")
        if spent_usd is not None:
            detail_parts.append(f"Spent: ${spent_usd:.2f}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            request_id=request_id,
        )
        self.budget_usd = budget_usd
        self.spent_usd = spent_usd


# =============================================================================
# External API Errors
# =============================================================================


class ExternalAPIError(AgentNavigatorError):
    """
    Base class for external API errors.

    HTTP Status: 502 Bad Gateway or 503 Service Unavailable
    """

    def __init__(
        self,
        message: str,
        *,
        service: str | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.service = service
        self.status_code = status_code
        detail_parts = []
        if service:
            detail_parts.append(f"Service: {service}")
        if status_code:
            detail_parts.append(f"Status: {status_code}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            error_code="external_api_error",
            request_id=request_id,
        )


class AnthropicAPIError(ExternalAPIError):
    """Raised when Anthropic API call fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_type: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.error_type = error_type
        detail_parts = []
        if error_type:
            detail_parts.append(f"Type: {error_type}")
        if status_code:
            detail_parts.append(f"Status: {status_code}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            service="anthropic",
            status_code=status_code,
            request_id=request_id,
        )
        if detail:
            self.detail = detail


class GitHubAPIError(ExternalAPIError):
    """Raised when GitHub API call fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message,
            service="github",
            status_code=status_code,
            request_id=request_id,
        )


class AuthenticationError(ExternalAPIError):
    """Raised when API authentication fails."""

    def __init__(
        self,
        service: str,
        *,
        request_id: str | None = None,
    ) -> None:
        super().__init__(
            message=f"Authentication failed for {service}",
            service=service,
            request_id=request_id,
        )
        self.error_code = "authentication_error"


class APITimeoutError(ExternalAPIError):
    """Raised when API request times out."""

    def __init__(
        self,
        service: str,
        *,
        timeout_seconds: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        detail = f"Timeout after {timeout_seconds}s" if timeout_seconds else None
        # Call parent with service, then override error_code
        super().__init__(
            message=f"Request to {service} timed out",
            service=service,
            request_id=request_id,
        )
        self.error_code = "api_timeout"
        if detail:
            self.detail = detail


class APIConnectionError(ExternalAPIError):
    """Raised when API connection fails."""

    def __init__(
        self,
        service: str,
        *,
        reason: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.reason = reason
        detail = reason if reason else "Could not establish connection"
        super().__init__(
            message=f"Connection to {service} failed",
            service=service,
            request_id=request_id,
        )
        self.error_code = "api_connection_error"
        self.detail = detail


# =============================================================================
# Circuit Breaker Errors
# =============================================================================


class CircuitBreakerOpenError(AgentNavigatorError):
    """
    Raised when circuit breaker is open.

    HTTP Status: 503 Service Unavailable
    """

    def __init__(
        self,
        service: str,
        *,
        retry_after_seconds: int | None = None,
        failure_count: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.service = service
        self.retry_after_seconds = retry_after_seconds
        self.failure_count = failure_count
        detail_parts = [f"Service: {service}"]
        if retry_after_seconds:
            detail_parts.append(f"Retry after: {retry_after_seconds}s")
        if failure_count:
            detail_parts.append(f"Failures: {failure_count}")
        detail = "; ".join(detail_parts)
        super().__init__(
            message=f"Circuit breaker open for {service}",
            detail=detail,
            error_code="circuit_breaker_open",
            request_id=request_id,
        )


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(AgentNavigatorError):
    """
    Raised when configuration is invalid or missing.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(
        self,
        message: str,
        *,
        setting_name: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.setting_name = setting_name
        detail = f"Missing or invalid setting: {setting_name}" if setting_name else None
        super().__init__(
            message,
            detail=detail,
            error_code="configuration_error",
            request_id=request_id,
        )


class MissingAPIKeyError(ConfigurationError):
    """Raised when required API key is missing."""

    def __init__(
        self,
        service: str,
        *,
        env_var: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.service = service
        self.env_var = env_var
        detail = f"API key for {service} is required"
        if env_var:
            detail += f" (set {env_var} environment variable)"
        super().__init__(
            message=f"Missing API key for {service}",
            setting_name=env_var or f"{service}_api_key",
            request_id=request_id,
        )
        self.detail = detail


# =============================================================================
# Data Store Errors
# =============================================================================


class DataStoreError(AgentNavigatorError):
    """
    Raised when data store operation fails.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(
        self,
        message: str,
        *,
        operation: str | None = None,
        path: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.operation = operation
        self.path = path
        detail_parts = []
        if operation:
            detail_parts.append(f"Operation: {operation}")
        if path:
            detail_parts.append(f"Path: {path}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            error_code="data_store_error",
            request_id=request_id,
        )


class CacheError(DataStoreError):
    """Raised when cache operation fails."""

    def __init__(
        self,
        message: str = "Cache operation failed",
        *,
        operation: str | None = None,
        cache_key: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.cache_key = cache_key
        detail_parts = []
        if operation:
            detail_parts.append(f"Operation: {operation}")
        if cache_key:
            detail_parts.append(f"Key: {cache_key}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            operation=operation,
            request_id=request_id,
        )


class DatabaseError(DataStoreError):
    """Raised when database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        *,
        operation: str | None = None,
        table: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.table = table
        detail_parts = []
        if operation:
            detail_parts.append(f"Operation: {operation}")
        if table:
            detail_parts.append(f"Table: {table}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            operation=operation,
            request_id=request_id,
        )


# =============================================================================
# Indexing Errors
# =============================================================================


class IndexingError(AgentNavigatorError):
    """
    Raised when indexing operation fails.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(
        self,
        message: str,
        *,
        repo_path: str | None = None,
        agent_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.agent_id = agent_id
        detail_parts = []
        if repo_path:
            detail_parts.append(f"Repository: {repo_path}")
        if agent_id:
            detail_parts.append(f"Agent: {agent_id}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            error_code="indexing_error",
            request_id=request_id,
        )


class LLMIndexingError(IndexingError):
    """Raised when LLM-based indexing fails."""

    def __init__(
        self,
        message: str = "LLM indexing failed",
        *,
        reason: str | None = None,
        agent_id: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.reason = reason
        detail = reason if reason else None
        super().__init__(
            message,
            agent_id=agent_id,
            request_id=request_id,
        )
        if detail:
            self.detail = detail


# =============================================================================
# Export Errors
# =============================================================================


class ExportError(AgentNavigatorError):
    """
    Raised when static site export fails.

    HTTP Status: 500 Internal Server Error
    """

    def __init__(
        self,
        message: str,
        *,
        output_path: str | None = None,
        page_type: str | None = None,
        request_id: str | None = None,
    ) -> None:
        self.output_path = output_path
        self.page_type = page_type
        detail_parts = []
        if page_type:
            detail_parts.append(f"Page type: {page_type}")
        if output_path:
            detail_parts.append(f"Output: {output_path}")
        detail = "; ".join(detail_parts) if detail_parts else None
        super().__init__(
            message,
            detail=detail,
            error_code="export_error",
            request_id=request_id,
        )


# =============================================================================
# HTTP Exception Helpers
# =============================================================================


def exception_to_http_status(exc: AgentNavigatorError) -> int:
    """
    Map exception to appropriate HTTP status code.

    Args:
        exc: The exception to map.

    Returns:
        HTTP status code.
    """
    status_map = {
        ValidationError: 400,
        InvalidAgentIDError: 400,
        InvalidQueryError: 400,
        InvalidURLError: 400,
        MissingRequiredFieldError: 400,
        NotFoundError: 404,
        AgentNotFoundError: 404,
        SnapshotNotFoundError: 404,
        RateLimitError: 429,
        BudgetExceededError: 429,
        ExternalAPIError: 502,
        AnthropicAPIError: 502,
        GitHubAPIError: 502,
        AuthenticationError: 503,
        APITimeoutError: 504,
        APIConnectionError: 503,
        CircuitBreakerOpenError: 503,
        ConfigurationError: 500,
        MissingAPIKeyError: 500,
        DataStoreError: 500,
        CacheError: 500,
        DatabaseError: 500,
        IndexingError: 500,
        LLMIndexingError: 500,
        ExportError: 500,
    }

    for exc_class, status in status_map.items():
        if isinstance(exc, exc_class):
            return status
    return 500


# =============================================================================
# Exception Handler for FastAPI
# =============================================================================


def handle_exception(exc: Exception, request_id: str | None = None) -> dict[str, Any]:
    """
    Convert any exception to standardized error response.

    Args:
        exc: The exception to handle.
        request_id: Request ID for tracing.

    Returns:
        Dictionary with error details.
    """
    if isinstance(exc, AgentNavigatorError):
        exc.request_id = request_id or exc.request_id
        return exc.to_dict()

    # Handle standard library exceptions
    if isinstance(exc, ValueError):
        return ValidationError(str(exc), request_id=request_id).to_dict()
    if isinstance(exc, KeyError):
        return MissingRequiredFieldError(str(exc), request_id=request_id).to_dict()
    if isinstance(exc, FileNotFoundError):
        return NotFoundError("Resource not found", request_id=request_id).to_dict()
    if isinstance(exc, PermissionError):
        return AgentNavigatorError(
            "Permission denied",
            detail=str(exc),
            error_code="permission_error",
            request_id=request_id,
        ).to_dict()
    if isinstance(exc, TimeoutError):
        return APITimeoutError("unknown", request_id=request_id).to_dict()
    if isinstance(exc, ConnectionError):
        return APIConnectionError("unknown", reason=str(exc), request_id=request_id).to_dict()

    # Generic error
    logger.error(
        "Unhandled exception",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "request_id": request_id,
        },
        exc_info=True,
    )
    return AgentNavigatorError(
        "An unexpected error occurred",
        detail=str(exc) if __debug__ else None,
        request_id=request_id,
    ).to_dict()
