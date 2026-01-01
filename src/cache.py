"""
SQLite-based cache for thread-safe, scalable caching.
Replaces file-based JSON caches with O(log n) lookups.

Uses SQLite's built-in Python support with thread-local connections
for concurrent access. WAL mode enables readers to proceed without
blocking writers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional


@dataclass
class CacheEntry:
    """A cached AI response."""
    created_at: float
    model: str
    text: str
    usage: dict
    cost_usd: float


@dataclass
class RateLimitEntry:
    """Single rate limit entry for a client."""
    request_times: list[float]
    last_seen: float


class SQLiteCache:
    """
    Thread-safe SQLite cache with TTL support.

    Provides O(log n) indexed lookups instead of O(n) file scans.
    Uses thread-local connections with WAL mode for concurrency.

    Example:
        cache = SQLiteCache(Path("/cache/data.db"), ttl_seconds=3600)
        entry = CacheEntry(created_at=time.time(), model="gpt-4", ...)
        cache.set("key", entry)
        cached = cache.get("key")  # Returns None if expired
    """

    def __init__(self, path: Path, ttl_seconds: int = 21600):
        """
        Initialize the SQLite cache.

        Args:
            path: Path to SQLite database file (will be created if needed)
            ttl_seconds: Time-to-live for cache entries in seconds
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """
        Get thread-local SQLite connection.

        Each thread gets its own connection to avoid locking issues.
        WAL mode allows concurrent readers and writers.
        """
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.path),
                check_same_thread=False,
                timeout=10.0,
            )
            # WAL mode enables non-blocking concurrent reads
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=10000")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
        return self._local.conn

    def _init_db(self) -> None:
        """Initialize cache table with indexes."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                created_at REAL NOT NULL,
                data TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON cache_entries(created_at)")
        conn.commit()

    def get(self, key: str) -> Optional[CacheEntry]:
        """
        Get entry from cache, respecting TTL.

        Args:
            key: Cache key to look up

        Returns:
            CacheEntry if found and valid, None if expired or not found
        """
        conn = self._get_conn()
        now = time.time()
        row = conn.execute(
            "SELECT data, created_at FROM cache_entries WHERE key = ?",
            (key,)
        ).fetchone()

        if not row:
            return None

        data, created_at = row
        if now - created_at > self.ttl_seconds:
            # Expired - delete and return None
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            return None

        try:
            return CacheEntry(**json.loads(data))
        except (json.JSONDecodeError, TypeError):
            return None

    def set(self, key: str, entry: CacheEntry) -> None:
        """
        Set entry in cache.

        Args:
            key: Cache key to store under
            entry: CacheEntry to store
        """
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO cache_entries (key, created_at, data) VALUES (?, ?, ?)",
            (key, entry.created_at, json.dumps(asdict(entry)))
        )
        conn.commit()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        conn = self._get_conn()
        now = time.time()
        cursor = conn.execute(
            "DELETE FROM cache_entries WHERE created_at < ?",
            (now - self.ttl_seconds,)
        )
        conn.commit()
        return cursor.rowcount

    def clear(self) -> None:
        """Clear all cache entries."""
        conn = self._get_conn()
        conn.execute("DELETE FROM cache_entries")
        conn.commit()


class SQLiteBudget:
    """
    SQLite-based daily budget tracker.

    Thread-safe and atomic budget tracking across multiple processes.
    Replaces file-based JSON budget tracking.

    Example:
        budget = SQLiteBudget(Path("/budget.db"), daily_budget_usd=10.0)
        if budget.would_exceed(estimated_cost):
            raise Exception("Budget exceeded")
        budget.add_spend(actual_cost)
    """

    def __init__(self, path: Path, daily_budget_usd: float):
        """
        Initialize the budget tracker.

        Args:
            path: Path to SQLite database file
            daily_budget_usd: Maximum daily budget in USD
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.daily_budget_usd = float(daily_budget_usd)
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local SQLite connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.path),
                check_same_thread=False,
                timeout=10.0,
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=10000")
        return self._local.conn

    def _init_db(self) -> None:
        """Initialize budget table."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS daily_spends (
                date TEXT PRIMARY KEY,
                amount_usd REAL NOT NULL
            )
        """)
        conn.commit()

    def _today_key(self) -> str:
        """Get today's date as ISO string."""
        return date.today().isoformat()

    def spent_today_usd(self) -> float:
        """
        Get amount spent today.

        Returns:
            USD amount spent today
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT amount_usd FROM daily_spends WHERE date = ?",
            (self._today_key(),)
        ).fetchone()
        return float(row[0]) if row else 0.0

    def would_exceed(self, additional_usd: float) -> bool:
        """
        Check if additional spend would exceed daily budget.

        Args:
            additional_usd: Additional cost to check

        Returns:
            True if budget would be exceeded
        """
        return (self.spent_today_usd() + float(additional_usd)) > self.daily_budget_usd

    def add_spend(self, usd: float) -> None:
        """
        Record a spend against today's budget.

        Args:
            usd: Amount to add to today's spend
        """
        conn = self._get_conn()
        k = self._today_key()
        # Atomic upsert
        conn.execute(
            "INSERT INTO daily_spends (date, amount_usd) VALUES (?, ?) "
            "ON CONFLICT (date) DO UPDATE SET amount_usd = amount_usd + ?",
            (k, float(usd), float(usd))
        )
        conn.commit()

    def clear_today(self) -> None:
        """Clear today's spend (useful for testing)."""
        conn = self._get_conn()
        conn.execute("DELETE FROM daily_spends WHERE date = ?", (self._today_key(),))
        conn.commit()

    def get_all_spends(self) -> dict[str, float]:
        """
        Get all recorded spends by date.

        Returns:
            Dict mapping date strings to USD amounts
        """
        conn = self._get_conn()
        rows = conn.execute("SELECT date, amount_usd FROM daily_spends").fetchall()
        return {date: amount for date, amount in rows}


class SQLiteRateLimiter:
    """
    SQLite-based rate limiter.

    Thread-safe and atomic rate limiting with O(log n) lookups by client.
    Stores request timestamps efficiently and provides automatic cleanup.

    Example:
        limiter = SQLiteRateLimiter(Path("/rate_limit.db"))
        allowed, retry_after = limiter.check_rate_limit("client_id")
        if not allowed:
            return Response("Rate limited", status=429)
    """

    def __init__(
        self,
        storage_path: Path,
        requests_per_window: int = 10,
        window_seconds: int = 60,
        cleanup_interval: int = 300,
    ):
        """
        Initialize the rate limiter.

        Args:
            storage_path: Path to SQLite database file
            requests_per_window: Max requests allowed per window
            window_seconds: Time window in seconds
            cleanup_interval: Seconds between cleanup runs
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.cleanup_interval = cleanup_interval
        self._local = threading.local()
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get thread-local SQLite connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.storage_path),
                check_same_thread=False,
                timeout=10.0,
            )
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA busy_timeout=10000")
        return self._local.conn

    def _init_db(self) -> None:
        """Initialize rate limit tables."""
        conn = self._get_conn()
        # Table for individual request timestamps
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_client_timestamp ON rate_limit_requests(client_id, timestamp)")
        # Table for client last-seen tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit_clients (
                client_id TEXT PRIMARY KEY,
                last_seen REAL NOT NULL
            )
        """)
        conn.commit()

    def _get_client_id(self, identifier: str) -> str:
        """
        Generate a client ID from an identifier.

        Uses hashing to avoid storing potentially sensitive identifiers.

        Args:
            identifier: Client identifier (e.g., session ID, IP address)

        Returns:
            Hashed client ID
        """
        import hashlib
        return hashlib.sha256(identifier.encode()).hexdigest()

    def _cleanup_old_entries(self) -> None:
        """
        Remove old entries to prevent unbounded growth.

        Cleans up requests older than 2x the window size.
        """
        conn = self._get_conn()
        now = time.time()
        cutoff = now - (self.window_seconds * 2)

        # Delete old requests
        conn.execute("DELETE FROM rate_limit_requests WHERE timestamp < ?", (cutoff,))

        # Delete clients with no recent requests
        conn.execute("""
            DELETE FROM rate_limit_clients
            WHERE client_id NOT IN (
                SELECT DISTINCT client_id FROM rate_limit_requests
            )
        """)

        conn.commit()

    def check_rate_limit(
        self,
        client_identifier: str,
        *,
        cost: int = 1
    ) -> tuple[bool, int]:
        """
        Check if a request should be rate limited.

        This is server-side enforcement - the client cannot bypass it.

        Args:
            client_identifier: Unique identifier for the client (session ID, IP, etc.)
            cost: Cost of this request (default: 1, can be higher for expensive operations)

        Returns:
            Tuple of (allowed: bool, retry_after: int)
            - allowed: True if request is allowed, False if rate limited
            - retry_after: Seconds to wait before retry (only meaningful if not allowed)
        """
        client_id = self._get_client_id(client_identifier)
        now = time.time()

        # Periodically clean up old entries
        if int(now) % self.cleanup_interval == 0:
            with self._lock:
                self._cleanup_old_entries()

        conn = self._get_conn()
        window_start = now - self.window_seconds

        # Count existing requests in window
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limit_requests "
            "WHERE client_id = ? AND timestamp > ?",
            (client_id, window_start)
        )
        current_count = cursor.fetchone()[0]

        # Check if limit exceeded
        if current_count + cost > self.requests_per_window:
            # Calculate retry time
            cursor = conn.execute(
                "SELECT MIN(timestamp) FROM rate_limit_requests "
                "WHERE client_id = ? AND timestamp > ?",
                (client_id, window_start)
            )
            result = cursor.fetchone()
            if result and result[0]:
                oldest_request = result[0]
                retry_after = int(oldest_request + self.window_seconds - now) + 1
                retry_after = max(1, retry_after)
            else:
                retry_after = self.window_seconds
            return False, retry_after

        # Add this request (one entry per cost unit)
        for _ in range(cost):
            conn.execute(
                "INSERT INTO rate_limit_requests (client_id, timestamp) VALUES (?, ?)",
                (client_id, now)
            )

        # Update last seen
        conn.execute(
            "INSERT OR REPLACE INTO rate_limit_clients (client_id, last_seen) VALUES (?, ?)",
            (client_id, now)
        )

        conn.commit()
        return True, 0

    def reset_rate_limit(self, client_identifier: str) -> None:
        """
        Reset rate limit for a specific client.

        Useful for testing or admin actions.

        Args:
            client_identifier: Client identifier to reset
        """
        client_id = self._get_client_id(client_identifier)
        conn = self._get_conn()
        conn.execute("DELETE FROM rate_limit_requests WHERE client_id = ?", (client_id,))
        conn.execute("DELETE FROM rate_limit_clients WHERE client_id = ?", (client_id,))
        conn.commit()

    def get_stats(self, client_identifier: str) -> dict:
        """
        Get rate limit statistics for a client.

        Args:
            client_identifier: Client identifier

        Returns:
            Dictionary with stats including requests_remaining, requests_used, window_reset
        """
        client_id = self._get_client_id(client_identifier)
        conn = self._get_conn()
        now = time.time()
        window_start = now - self.window_seconds

        # Count requests in current window
        cursor = conn.execute(
            "SELECT COUNT(*) FROM rate_limit_requests "
            "WHERE client_id = ? AND timestamp > ?",
            (client_id, window_start)
        )
        requests_in_window = cursor.fetchone()[0]

        # Get oldest request time for window reset calculation
        cursor = conn.execute(
            "SELECT MAX(timestamp) FROM rate_limit_requests "
            "WHERE client_id = ? AND timestamp > ?",
            (client_id, window_start)
        )
        result = cursor.fetchone()
        window_reset = result[0] + self.window_seconds if result and result[0] else now + self.window_seconds

        return {
            'requests_remaining': max(0, self.requests_per_window - requests_in_window),
            'requests_used': requests_in_window,
            'window_reset': window_reset
        }

    def reset_all(self) -> None:
        """Reset all rate limits. Useful for testing."""
        conn = self._get_conn()
        conn.execute("DELETE FROM rate_limit_requests")
        conn.execute("DELETE FROM rate_limit_clients")
        conn.commit()
