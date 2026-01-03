"""
Agent Navigator - Circuit Breaker Pattern
==========================================
Implements circuit breaker for external API calls to prevent cascading failures.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit tripped, requests fail fast
- HALF_OPEN: Testing if service has recovered

Usage:
    breaker = CircuitBreaker(failure_threshold=5, timeout=60)

    try:
        result = breaker.call(api_function, arg1, arg2)
    except CircuitBreakerOpenError:
        # Handle fast-fail when circuit is open
        pass
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import Any, ParamSpec

from src.exceptions import CircuitBreakerOpenError as CircuitBreakerOpenErrorExt

P = ParamSpec("P")

logger = logging.getLogger(__name__)

# Re-export for backward compatibility
CircuitBreakerOpenError = CircuitBreakerOpenErrorExt


class CircuitBreaker:
    """
    Circuit breaker for protecting external API calls.

    Prevents cascading failures by fast-failing when an external service
    is experiencing issues. Automatically retries after a cooldown period.

    State transitions:
        CLOSED --(failures >= threshold)--> OPEN
        OPEN --(timeout elapsed)--> HALF_OPEN
        HALF_OPEN --(success)--> CLOSED
        HALF_OPEN --(failure)--> OPEN
    """

    _STATE_CLOSED = "closed"
    _STATE_OPEN = "open"
    _STATE_HALF_OPEN = "half_open"

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        *,
        name: str = "default",
        half_open_max_calls: int = 3,
        expected_exceptions: tuple[type[Exception], ...] = (Exception,),
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of consecutive failures before opening circuit.
            timeout: Seconds to wait before transitioning from OPEN to HALF_OPEN.
            name: Name for logging/debugging (e.g., "anthropic_api", "github_api").
            half_open_max_calls: Max calls allowed in HALF_OPEN state before decision.
            expected_exceptions: Exception types that count as failures.
        """
        self._failure_threshold = failure_threshold
        self._timeout = timeout
        self._name = name
        self._half_open_max_calls = half_open_max_calls
        self._expected_exceptions = expected_exceptions

        # State tracking
        self._state = self._STATE_CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._opened_at: float | None = None

        # Thread safety
        self._lock = threading.RLock()

    def call(self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to execute (typically an API call).
            *args: Positional arguments for func.
            **kwargs: Keyword arguments for func.

        Returns:
            Result from func.

        Raises:
            CircuitBreakerOpenError: If circuit is OPEN (fast fail).
            Exception: Propagates exception from func if in CLOSED/HALF_OPEN state.
        """
        with self._lock:
            # Check if we should attempt recovery
            if self._state == self._STATE_OPEN:
                if self._should_attempt_reset():
                    self._transition_to_half_open()
                    logger.info(
                        f"[CircuitBreaker:{self._name}] "
                        f"Transitioned to HALF_OPEN after {self._timeout}s timeout"
                    )
                else:
                    logger.warning(
                        f"[CircuitBreaker:{self._name}] "
                        f"OPEN - rejecting request (opened {self._seconds_since_opened():.1f}s ago)"
                    )
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self._name}' is open. "
                        f"Please wait {self._timeout - self._seconds_since_opened():.0f}s before retrying."
                    )

        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self._expected_exceptions as e:
            self._on_failure()
            raise

    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        with self._lock:
            was_state = self._state
            self._state = self._STATE_CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._opened_at = None
            logger.info(f"[CircuitBreaker:{self._name}] Manually reset from {was_state} to CLOSED")

    @property
    def state(self) -> str:
        """Current state: 'closed', 'open', or 'half_open'."""
        with self._lock:
            return self._state

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        with self._lock:
            return self._failure_count

    @property
    def is_open(self) -> bool:
        """Whether circuit is currently open."""
        return self.state == self._STATE_OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._opened_at is None:
            return True
        return time.time() - self._opened_at >= self._timeout

    def _seconds_since_opened(self) -> float:
        """Seconds since circuit opened."""
        if self._opened_at is None:
            return 0.0
        return time.time() - self._opened_at

    def _on_success(self) -> None:
        """Handle successful call."""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None

            if self._state == self._STATE_HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._half_open_max_calls:
                    self._transition_to_closed()
            else:
                # Already CLOSED, nothing to do
                pass

    def _on_failure(self) -> None:
        """Handle failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == self._STATE_HALF_OPEN:
                # Failure in HALF_OPEN -> back to OPEN
                self._transition_to_open()
            elif self._failure_count >= self._failure_threshold:
                # Too many failures in CLOSED -> OPEN
                self._transition_to_open()
            else:
                logger.warning(
                    f"[CircuitBreaker:{self._name}] "
                    f"Failure {self._failure_count}/{self._failure_threshold} (state: {self._state})"
                )

    def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        was_state = self._state
        self._state = self._STATE_OPEN
        self._opened_at = time.time()
        self._success_count = 0
        logger.error(
            f"[CircuitBreaker:{self._name}] "
            f"Transitioned from {was_state} to OPEN "
            f"(failures: {self._failure_count}, threshold: {self._failure_threshold})"
        )

    def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        was_state = self._state
        self._state = self._STATE_HALF_OPEN
        self._success_count = 0
        logger.info(f"[CircuitBreaker:{self._name}] Transitioned from {was_state} to HALF_OPEN")

    def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        was_state = self._state
        self._state = self._STATE_CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
        logger.info(
            f"[CircuitBreaker:{self._name}] "
            f"Transitioned from {was_state} to CLOSED (service recovered)"
        )

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name={self._name!r}, state={self.state}, "
            f"failures={self._failure_count}/{self._failure_threshold})"
        )


# Global circuit breaker instances for common services
_anthropic_breaker: CircuitBreaker | None = None
_github_breaker: CircuitBreaker | None = None


def get_anthropic_breaker() -> CircuitBreaker:
    """Get or create circuit breaker for Anthropic API calls."""
    global _anthropic_breaker
    if _anthropic_breaker is None:
        from src.config import settings

        _anthropic_breaker = CircuitBreaker(
            name="anthropic_api",
            failure_threshold=settings.circuit_breaker_anthropic_failure_threshold,
            timeout=settings.circuit_breaker_anthropic_timeout_seconds,
            expected_exceptions=(
                TimeoutError,
                ConnectionError,
                OSError,
            ),
        )
    return _anthropic_breaker


def get_github_breaker() -> CircuitBreaker:
    """Get or create circuit breaker for GitHub API calls."""
    global _github_breaker
    if _github_breaker is None:
        from src.config import settings

        _github_breaker = CircuitBreaker(
            name="github_api",
            failure_threshold=settings.circuit_breaker_github_failure_threshold,
            timeout=settings.circuit_breaker_github_timeout_seconds,
            expected_exceptions=(
                TimeoutError,
                ConnectionError,
                OSError,
            ),
        )
    return _github_breaker


def reset_all_breakers() -> None:
    """Reset all global circuit breakers."""
    if _anthropic_breaker:
        _anthropic_breaker.reset()
    if _github_breaker:
        _github_breaker.reset()
