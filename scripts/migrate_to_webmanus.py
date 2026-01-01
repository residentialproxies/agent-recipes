"""
Migrate developer-facing `data/agents.json` into WebManus SQLite (`data/webmanus.db`).

Usage:
  python3 scripts/migrate_to_webmanus.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict

# Allow "src/" and "config/" imports when executed as a script
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src.repository import AgentRepo  # noqa: E402
from config.capability_map import infer_capabilities  # noqa: E402


def slugify(text: str) -> str:
    """Generate a URL-safe slug (lowercase, hyphen separated, max 60 chars)."""
    slug = (text or "").strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug[:60] or "worker"


def estimate_labor_score(agent: dict) -> float:
    """
    Estimate automation capability score (0-10).

    Heuristic inputs:
    - complexity (beginner/intermediate/advanced)
    - design_pattern (rag/multi_agent)
    - supports_local_models
    """
    score = 5.0

    complexity = (agent.get("complexity") or "intermediate").lower()
    if complexity == "beginner":
        score += 2.0
    elif complexity == "advanced":
        score -= 1.0

    pattern = (agent.get("design_pattern") or "").lower()
    if "multi_agent" in pattern:
        score += 1.5
    elif "rag" in pattern:
        score += 1.0

    if agent.get("supports_local_models"):
        score += 0.5

    if agent.get("requires_gpu"):
        score -= 0.5

    return float(min(10.0, max(0.0, score)))


def _load_agents_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def migrate(*, agents_path: Path = Path("data/agents.json"), db_path: str = "data/webmanus.db") -> int:
    old_agents = _load_agents_json(agents_path)
    if not old_agents:
        raise SystemExit(f"❌ No agents found at {agents_path}")

    print("📦 Found %d agents to migrate" % len(old_agents))
    repo = AgentRepo(db_path)

    used: Dict[str, int] = {}
    migrated = 0

    for old in old_agents:
        name = (old.get("name") or "").strip()
        if not name:
            continue

        base = slugify(old.get("id") or name)
        n = used.get(base, 0)
        used[base] = n + 1
        slug = base if n == 0 else f"{base}-{n+1}"

        description = (old.get("description") or "").strip()
        tagline = (description[:120]).strip()
        if not tagline:
            tagline = f"AI-powered {name}"

        new_agent = {
            "slug": slug,
            "name": name,
            "tagline": tagline,
            "pricing": "freemium",
            "labor_score": estimate_labor_score(old),
            "browser_native": False,
            "website": old.get("website") or old.get("homepage") or None,
            "affiliate_url": None,
            "logo_url": None,
            "source_url": old.get("github_url"),
            "_legacy": {
                "id": old.get("id"),
                "category": old.get("category"),
                "frameworks": old.get("frameworks"),
                "llm_providers": old.get("llm_providers"),
                "complexity": old.get("complexity"),
                "design_pattern": old.get("design_pattern"),
            },
        }

        capabilities = infer_capabilities(old)
        repo.upsert(new_agent, capabilities)
        migrated += 1

    print("✅ Migrated %d workers to %s" % (migrated, db_path))
    print("📊 Total workers in DB: %d" % repo.count())
    caps = repo.get_all_capabilities()
    print("🏷️  Total capabilities: %d" % len(caps))
    if caps:
        print("   Sample: %s%s" % (", ".join(caps[:12]), " ..." if len(caps) > 12 else ""))
    return migrated


if __name__ == "__main__":
    migrate()

