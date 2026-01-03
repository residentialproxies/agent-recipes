"""
Server-side rate limiting using SQLite-based storage.

Prevents abuse by tracking request counts per client/session.
Uses SQLite storage to avoid Redis dependency for simple deployments.
Provides O(log n) lookups instead of O(n) file scans.
"""

from dataclasses import dataclass
from pathlib import Path

from src.cache import SQLiteRateLimiter as _SQLiteRateLimiter


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""

    requests_per_window: int = 10
    window_seconds: int = 60
    cleanup_interval: int = 300  # Clean up old entries every 5 minutes


class FileRateLimiter(_SQLiteRateLimiter):
    """
    Rate limiter with SQLite-based storage.

    This is a backward-compatible wrapper around SQLiteRateLimiter that
    maintains the old constructor signature (storage_path, config).

    The SQLite implementation provides O(log n) indexed lookups instead of
    O(n) file scans, and thread-safe concurrent access via WAL mode.

    Security benefits:
    - Server-side enforcement (client cannot bypass)
    - Prevents brute force attacks
    - Prevents API abuse
    - Protects against DoS attacks
    """

    def __init__(self, storage_path: str | Path, config: RateLimitConfig | None = None):
        """
        Initialize the rate limiter.

        Args:
            storage_path: Path to rate limit storage file (can be .json or .db)
            config: Rate limit configuration
        """
        cfg = config or RateLimitConfig()
        # Convert .json paths to .db for SQLite
        path = Path(storage_path)
        if path.suffix == ".json":
            path = path.with_suffix(".db")

        super().__init__(
            storage_path=path,
            requests_per_window=cfg.requests_per_window,
            window_seconds=cfg.window_seconds,
            cleanup_interval=cfg.cleanup_interval,
        )


# Global rate limiter instance
_rate_limiter: FileRateLimiter | None = None


def get_rate_limiter(storage_path: str | Path | None = None, config: RateLimitConfig | None = None) -> FileRateLimiter:
    """
    Get the global rate limiter instance.

    Args:
        storage_path: Path to rate limit storage file
        config: Rate limit configuration

    Returns:
        FileRateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        if storage_path is None:
            # Default to .streamlit/rate_limits.db
            storage_path = Path(".streamlit") / "rate_limits.db"

        _rate_limiter = FileRateLimiter(storage_path, config)

    return _rate_limiter
