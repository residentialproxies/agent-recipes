"""
User repository for favorites and view history.

Connects to Supabase PostgreSQL for persistent user data.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import row_factory
from psycopg import OperationalError

from src.exceptions import DatabaseError

logger = logging.getLogger(__name__)

# Default database URL (override via env)
DEFAULT_DB_URL = "postgresql://postgres:${DB_PASSWORD}@supabase-db:5432/postgres?schema=agent_navigator"


def _get_db_url() -> str:
    """Get database URL from environment or use default."""
    db_url = os.environ.get("AGENT_NAV_DB_URL")
    if db_url:
        return db_url

    # Build from components
    password = os.environ.get("DB_PASSWORD", "postgres")
    host = os.environ.get("DB_HOST", "supabase-db")
    port = os.environ.get("DB_PORT", "5432")
    database = os.environ.get("DB_NAME", "postgres")
    return f"postgresql://postgres:{password}@{host}:{port}/{database}?schema=agent_navigator"


@dataclass
class Favorite:
    id: str
    user_id: str
    agent_id: str
    created_at: str


@dataclass
class ViewHistoryItem:
    id: str
    user_id: str
    agent_id: str
    viewed_at: str


class UserRepo:
    """
    Repository for user favorites and view history.

    Uses Supabase PostgreSQL connection. Falls back to in-memory
    storage if database is unavailable.
    """

    def __init__(self, db_url: str | None = None) -> None:
        self._db_url = db_url or _get_db_url()
        self._in_memory_favorites: dict[str, set[str]] = {}
        self._in_memory_history: dict[str, list[str]] = {}
        self._use_db = self._test_connection()

    def _test_connection(self) -> bool:
        """Test database connection, fall back to in-memory if failed."""
        try:
            with psycopg.connect(self._db_url, row_factory=row_factory) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    cur.fetchone()
            logger.info("UserRepo: Connected to PostgreSQL for user data")
            return True
        except OperationalError as e:
            logger.warning("UserRepo: DB connection failed, using in-memory storage: %s", e)
            return False
        except OSError as e:
            logger.warning("UserRepo: Network error, using in-memory storage: %s", e)
            return False

    def _execute(self, sql: str, params: tuple = (), fetch: bool = False) -> list[Any] | None:
        """Execute SQL with connection management."""
        if not self._use_db:
            return None

        try:
            with psycopg.connect(self._db_url, row_factory=row_factory) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    if fetch:
                        return cur.fetchall()
                    return None
        except OperationalError as e:
            logger.warning("UserRepo: DB connection lost, falling back to in-memory: %s", e)
            self._use_db = False
            return None
        except OSError as e:
            logger.warning("UserRepo: Network error, falling back to in-memory: %s", e)
            self._use_db = False
            return None

    def get_favorites(self, user_id: str) -> set[str]:
        """Get user's favorite agent IDs."""
        if not user_id:
            return set()

        if not self._use_db:
            return self._in_memory_favorites.get(user_id, set()).copy()

        rows = self._execute(
            "SELECT agent_id FROM agent_navigator.favorites WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,),
            fetch=True,
        )
        if rows is None:
            return self._in_memory_favorites.get(user_id, set()).copy()
        return {row["agent_id"] for row in rows}

    def toggle_favorite(self, user_id: str, agent_id: str) -> tuple[bool, bool]:
        """
        Toggle favorite status.
        Returns (is_favorite, was_added).
        """
        if not user_id or not agent_id:
            return False, False

        if not self._use_db:
            favorites = self._in_memory_favorites.setdefault(user_id, set())
            if agent_id in favorites:
                favorites.remove(agent_id)
                return False, False
            else:
                favorites.add(agent_id)
                return True, True

        rows = self._execute(
            "SELECT * FROM agent_navigator.favorites WHERE user_id = %s AND agent_id = %s",
            (user_id, agent_id),
            fetch=True,
        )
        if rows is None:
            return self._toggle_fallback(user_id, agent_id)

        if rows:
            self._execute(
                "DELETE FROM agent_navigator.favorites WHERE user_id = %s AND agent_id = %s",
                (user_id, agent_id),
            )
            return False, False
        else:
            self._execute(
                "INSERT INTO agent_navigator.favorites (user_id, agent_id) VALUES (%s, %s)",
                (user_id, agent_id),
            )
            return True, True

    def _toggle_fallback(self, user_id: str, agent_id: str) -> tuple[bool, bool]:
        """Fallback to in-memory on DB error."""
        favorites = self._in_memory_favorites.setdefault(user_id, set())
        if agent_id in favorites:
            favorites.remove(agent_id)
            return False, False
        favorites.add(agent_id)
        return True, True

    def is_favorite(self, user_id: str, agent_id: str) -> bool:
        """Check if agent is in user's favorites."""
        if not user_id or not agent_id:
            return False

        if not self._use_db:
            return agent_id in self._in_memory_favorites.get(user_id, set())

        rows = self._execute(
            "SELECT 1 FROM agent_navigator.favorites WHERE user_id = %s AND agent_id = %s",
            (user_id, agent_id),
            fetch=True,
        )
        if rows is None:
            return agent_id in self._in_memory_favorites.get(user_id, set())
        return len(rows) > 0

    def add_favorite(self, user_id: str, agent_id: str) -> bool:
        """Add agent to favorites. Returns True if added."""
        if not user_id or not agent_id:
            return False

        if not self._use_db:
            favorites = self._in_memory_favorites.setdefault(user_id, set())
            if agent_id not in favorites:
                favorites.add(agent_id)
                return True
            return False

        try:
            self._execute(
                "INSERT INTO agent_navigator.favorites (user_id, agent_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (user_id, agent_id),
            )
            return True
        except (OperationalError, OSError):
            return False

    def remove_favorite(self, user_id: str, agent_id: str) -> bool:
        """Remove agent from favorites. Returns True if removed."""
        if not user_id or not agent_id:
            return False

        if not self._use_db:
            favorites = self._in_memory_favorites.get(user_id, set())
            if agent_id in favorites:
                favorites.remove(agent_id)
                return True
            return False

        try:
            self._execute(
                "DELETE FROM agent_navigator.favorites WHERE user_id = %s AND agent_id = %s",
                (user_id, agent_id),
            )
            return True
        except (OperationalError, OSError):
            return False

    def get_view_history(self, user_id: str, limit: int = 20) -> list[str]:
        """Get user's view history as agent ID list."""
        if not user_id:
            return []

        if not self._use_db:
            return self._in_memory_history.get(user_id, [])[:limit]

        rows = self._execute(
            "SELECT agent_id FROM agent_navigator.view_history WHERE user_id = %s ORDER BY viewed_at DESC LIMIT %s",
            (user_id, limit),
            fetch=True,
        )
        if rows is None:
            return self._in_memory_history.get(user_id, [])[:limit]
        return [row["agent_id"] for row in rows]

    def record_view(self, user_id: str, agent_id: str) -> bool:
        """Record an agent view. Returns True on success."""
        if not user_id or not agent_id:
            return False

        if not self._use_db:
            history = self._in_memory_history.setdefault(user_id, [])
            if agent_id in history:
                history.remove(agent_id)
            history.insert(0, agent_id)
            self._in_memory_history[user_id] = history[:50]
            return True

        try:
            self._execute(
                "INSERT INTO agent_navigator.view_history (user_id, agent_id) VALUES (%s, %s) "
                "ON CONFLICT (user_id, agent_id) DO UPDATE SET viewed_at = NOW()",
                (user_id, agent_id),
            )
            return True
        except (OperationalError, OSError) as e:
            logger.warning("Failed to record view: %s", e)
            return False

    def sync_favorites_to_db(self, user_id: str, agent_ids: set[str]) -> bool:
        """Sync favorites from client to database (used on reconnection)."""
        if not user_id or not self._use_db:
            return False

        try:
            with psycopg.connect(self._db_url, row_factory=row_factory) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM agent_navigator.favorites WHERE user_id = %s", (user_id,))
                    for agent_id in agent_ids:
                        cur.execute(
                            "INSERT INTO agent_navigator.favorites (user_id, agent_id) VALUES (%s, %s)",
                            (user_id, agent_id),
                        )
            return True
        except (OperationalError, OSError) as e:
            logger.warning("Failed to sync favorites: %s", e)
            return False


# Singleton instance
_user_repo: UserRepo | None = None


def get_user_repo() -> UserRepo:
    """Get the global user repository instance."""
    global _user_repo
    if _user_repo is None:
        _user_repo = UserRepo()
    return _user_repo
