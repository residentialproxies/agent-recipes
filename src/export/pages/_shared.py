"""
Shared helpers for pSEO page generation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

logger = logging.getLogger(__name__)


def sort_agents(agents: list[dict], sort_by: str = "stars") -> list[dict]:
    if sort_by == "stars":
        return sorted(
            agents,
            key=lambda a: (
                -(a.get("stars") if isinstance(a.get("stars"), int) else 0),
                (a.get("name") or "").lower(),
            ),
        )
    if sort_by == "updated_at":
        return sorted(
            agents,
            key=lambda a: (
                -(a.get("updated_at") if isinstance(a.get("updated_at"), int) else 0),
                (a.get("name") or "").lower(),
            ),
        )
    return sorted(agents, key=lambda a: (a.get("name") or "").lower())


def filter_agents(agents: list[dict], criteria: Callable[[dict], bool]) -> list[dict]:
    out: list[dict] = []
    for a in agents:
        try:
            if criteria(a):
                out.append(a)
        except Exception as exc:
            logger.debug("Ignoring agent during filter (criteria error): %s", exc)
            continue
    return out
