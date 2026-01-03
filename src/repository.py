from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.security.sql import escape_like_pattern, validate_search_input

_ALLOWED_PRICING = {"free", "freemium", "paid", "enterprise"}


@dataclass
class Agent:
    """Data model for an AI agent worker."""

    slug: str
    name: str
    tagline: str
    pricing: str  # free | freemium | paid | enterprise
    labor_score: float  # 0-10
    browser_native: bool
    website: str | None
    affiliate_url: str | None
    logo_url: str | None
    source_url: str | None
    capabilities: list[str]
    data_json: str  # full JSON backup (including capabilities)


class AgentRepo:
    """
    Lightweight SQLite repository for WebManus "workers".

    Design goals:
    - Single-file DB (easy deploy + backup)
    - Fast filtered listing via indexes + join table
    - Store full JSON blob for forward compatibility
    """

    def __init__(self, db_path: str = "data/webmanus.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS agents (
                    slug TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    tagline TEXT,
                    pricing TEXT DEFAULT 'freemium',
                    labor_score REAL DEFAULT 5.0,
                    browser_native INTEGER DEFAULT 0,
                    website TEXT,
                    affiliate_url TEXT,
                    logo_url TEXT,
                    source_url TEXT,
                    data_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS agent_capabilities (
                    agent_slug TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    PRIMARY KEY (agent_slug, capability),
                    FOREIGN KEY (agent_slug) REFERENCES agents(slug) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_agents_pricing ON agents(pricing);
                CREATE INDEX IF NOT EXISTS idx_agents_labor_score ON agents(labor_score);
                CREATE INDEX IF NOT EXISTS idx_agent_capabilities_capability ON agent_capabilities(capability);
                """
            )

    def upsert(self, agent: dict[str, Any], capabilities: list[str]) -> None:
        slug = (agent.get("slug") or "").strip()
        if not slug:
            raise ValueError("agent.slug is required")

        full_agent = dict(agent)
        full_agent["capabilities"] = [c for c in (capabilities or []) if c]

        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO agents (
                    slug, name, tagline, pricing, labor_score, browser_native,
                    website, affiliate_url, logo_url, source_url, data_json, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(slug) DO UPDATE SET
                    name=excluded.name,
                    tagline=excluded.tagline,
                    pricing=excluded.pricing,
                    labor_score=excluded.labor_score,
                    browser_native=excluded.browser_native,
                    website=excluded.website,
                    affiliate_url=excluded.affiliate_url,
                    logo_url=excluded.logo_url,
                    source_url=excluded.source_url,
                    data_json=excluded.data_json,
                    updated_at=CURRENT_TIMESTAMP
                """,
                (
                    slug,
                    full_agent.get("name"),
                    full_agent.get("tagline"),
                    full_agent.get("pricing", "freemium"),
                    float(full_agent.get("labor_score", 5.0)),
                    int(bool(full_agent.get("browser_native", False))),
                    full_agent.get("website"),
                    full_agent.get("affiliate_url"),
                    full_agent.get("logo_url"),
                    full_agent.get("source_url"),
                    json.dumps(full_agent, ensure_ascii=False),
                ),
            )

            conn.execute("DELETE FROM agent_capabilities WHERE agent_slug = ?", (slug,))
            for cap in capabilities or []:
                cap_clean = str(cap).strip().lower()
                if not cap_clean:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO agent_capabilities (agent_slug, capability) VALUES (?, ?)",
                    (slug, cap_clean),
                )

    def search(
        self,
        *,
        q: str = "",
        capability: str | None = None,
        pricing: str | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        q = (q or "").strip()
        capability = (capability or "").strip() or None
        pricing = (pricing or "").strip() or None
        if pricing and pricing not in _ALLOWED_PRICING:
            return []
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        min_score = max(0.0, min(float(min_score), 10.0))

        # Security: Validate search input to prevent injection
        if q:
            try:
                q = validate_search_input(q, max_length=200)
            except (TypeError, ValueError):
                q = ""

        with self._conn() as conn:
            sql, params = self._build_search_sql(
                q=q,
                capability=capability,
                pricing=pricing,
                min_score=min_score,
            )
            rows = conn.execute(
                f"SELECT DISTINCT a.data_json {sql} ORDER BY a.labor_score DESC, a.name ASC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            return [json.loads(row["data_json"]) for row in rows if row["data_json"]]

    def search_page(
        self,
        *,
        q: str = "",
        capability: str | None = None,
        pricing: str | None = None,
        min_score: float = 0.0,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[dict[str, Any]]]:
        """
        Search workers and return (total_count, page_items).

        This keeps the existing `search()` API stable while enabling correct pagination in the HTTP layer.
        """
        q = (q or "").strip()
        capability = (capability or "").strip() or None
        pricing = (pricing or "").strip() or None
        if pricing and pricing not in _ALLOWED_PRICING:
            return 0, []
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        min_score = max(0.0, min(float(min_score), 10.0))

        # Security: Validate search input to prevent injection
        if q:
            try:
                q = validate_search_input(q, max_length=200)
            except (TypeError, ValueError):
                q = ""

        with self._conn() as conn:
            sql, params = self._build_search_sql(
                q=q,
                capability=capability,
                pricing=pricing,
                min_score=min_score,
            )
            row = conn.execute(f"SELECT COUNT(DISTINCT a.slug) AS c {sql}", params).fetchone()
            total = int(row["c"] if row else 0)
            rows = conn.execute(
                f"SELECT DISTINCT a.data_json {sql} ORDER BY a.labor_score DESC, a.name ASC LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
            items = [json.loads(r["data_json"]) for r in rows if r["data_json"]]
            return total, items

    def _build_search_sql(
        self,
        *,
        q: str,
        capability: str | None,
        pricing: str | None,
        min_score: float,
    ) -> tuple[str, list[Any]]:
        sql = "FROM agents a"
        params: list[Any] = []

        if capability:
            sql += " JOIN agent_capabilities ac ON a.slug = ac.agent_slug"

        where: list[str] = ["a.labor_score >= ?"]
        params.append(float(min_score))

        if capability:
            where.append("ac.capability = ?")
            params.append(capability.lower())

        if pricing:
            where.append("a.pricing = ?")
            params.append(pricing)

        if q:
            # Security: Escape LIKE wildcards to prevent SQL injection
            # Without escaping, user input like "admin' OR '1'='1" could manipulate the query
            # The % and _ characters are wildcards in SQL LIKE and must be escaped
            escaped_q = escape_like_pattern(q)
            like = f"%{escaped_q}%"
            # Use ESCAPE clause to properly handle escaped wildcards
            where.append("(a.name LIKE ? ESCAPE '\\' OR a.tagline LIKE ? ESCAPE '\\')")
            params.extend([like, like])

        sql += " WHERE " + " AND ".join(where)
        return sql, params

    def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        slug = (slug or "").strip()
        if not slug:
            return None
        with self._conn() as conn:
            row = conn.execute("SELECT data_json FROM agents WHERE slug = ?", (slug,)).fetchone()
            if not row:
                return None
            return json.loads(row["data_json"]) if row["data_json"] else None

    def get_all_capabilities(self) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute("SELECT DISTINCT capability FROM agent_capabilities ORDER BY capability").fetchall()
            return [row["capability"] for row in rows]

    def count(self) -> int:
        with self._conn() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM agents").fetchone()
            return int(row["c"] if row else 0)
