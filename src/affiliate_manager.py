"""
Affiliate link management for WebManus.

This is intentionally simple and offline:
- Prefer a hard-coded per-slug override for partners
- Otherwise, keep DB-stored `affiliate_url` if present
- Otherwise, derive a `?ref=webmanus` URL from `website` (best-effort)
"""

from __future__ import annotations

from typing import Any

AFFILIATE_LINKS: dict[str, str] = {
    # slug -> affiliate URL
    # "taskade-ai": "https://taskade.com?ref=webmanus",
    # "notion-ai": "https://affiliate.notion.so/...",
}


DEFAULT_REF_KEY = "ref"
DEFAULT_REF_VALUE = "webmanus"


def inject_affiliate(agent: dict[str, Any]) -> dict[str, Any]:
    """
    Return a copy of `agent` with `affiliate_url` injected.

    Priority:
      1) hard-coded override
      2) existing `affiliate_url` on the agent
      3) derived from `website` by adding `ref=webmanus`

    Args:
        agent: Agent dictionary potentially containing slug, website, and affiliate_url.

    Returns:
        Copy of agent dictionary with affiliate_url injected.
    """
    out = dict(agent or {})
    slug = (out.get("slug") or "").strip()

    if slug and slug in AFFILIATE_LINKS:
        out["affiliate_url"] = AFFILIATE_LINKS[slug]
        return out

    if out.get("affiliate_url"):
        return out

    website = out.get("website")
    if isinstance(website, str) and website.strip():
        sep = "&" if "?" in website else "?"
        out["affiliate_url"] = f"{website}{sep}{DEFAULT_REF_KEY}={DEFAULT_REF_VALUE}"
    return out


def batch_inject(agents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Inject affiliate URLs into a batch of agents.

    Args:
        agents: List of agent dictionaries.

    Returns:
        List of agent dictionaries with affiliate_url injected.
    """
    return [inject_affiliate(a) for a in (agents or [])]
