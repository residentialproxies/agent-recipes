from __future__ import annotations

import re
from typing import Optional, Tuple


# CATEGORY_ICONS is now imported from src.config to avoid duplication
# from src.config import CATEGORY_ICONS  # noqa: F401 (kept for reference)


def complexity_rank(value: str) -> int:
    """Return numeric rank for complexity level.

    Args:
        value: Complexity level string (e.g., 'beginner', 'intermediate').

    Returns:
        Numeric rank where lower = simpler (beginner=0, intermediate=1,
        advanced=2, unknown=99).
    """
    order = {"beginner": 0, "intermediate": 1, "advanced": 2}
    return order.get((value or "").lower(), 99)


def estimate_setup_time(complexity: str) -> str:
    """Return estimated setup time for a complexity level.

    Args:
        complexity: Complexity level string.

    Returns:
        Human-readable time estimate string.
    """
    return {"beginner": "10–20 min", "intermediate": "20–45 min", "advanced": "45–90+ min"}.get(
        (complexity or "").lower(),
        "Varies",
    )


def parse_github_tree_url(url: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse https://github.com/<owner>/<repo>/tree/<branch>/<path>
    Returns (owner, repo, branch).
    """
    m = re.match(r"^https://github\.com/([^/]+)/([^/]+)/tree/([^/]+)/", url or "")
    if not m:
        return None
    return m.group(1), m.group(2), m.group(3)


def raw_readme_url(
    agent: dict,
    *,
    default_owner: str = "Shubhamsaboo",
    default_repo: str = "awesome-llm-apps",
    default_branch: str = "main",
) -> Optional[str]:
    """Generate raw GitHub URL for an agent's README file.

    Args:
        agent: Agent dictionary containing github_url and readme paths.
        default_owner: Default repository owner if not parsed from URL.
        default_repo: Default repository name if not parsed from URL.
        default_branch: Default branch name.

    Returns:
        Raw GitHub content URL for the README, or None if insufficient
        information.
    """
    github_url = agent.get("github_url") or ""
    parsed = parse_github_tree_url(github_url)
    owner, repo, branch = (default_owner, default_repo, default_branch)
    if parsed:
        owner, repo, branch = parsed

    readme_relpath = agent.get("readme_relpath") or ""
    if not readme_relpath:
        folder_path = agent.get("folder_path") or ""
        if not folder_path:
            return None
        readme_relpath = f"{folder_path}/README.md"

    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{readme_relpath}"


def rewrite_relative_links(markdown: str, agent: dict, *, default_branch: str = "main") -> str:
    """Rewrite relative markdown links to absolute GitHub raw URLs.

    Args:
        markdown: Markdown content potentially containing relative links.
        agent: Agent dictionary with github_url and folder_path.
        default_branch: Default branch name for URL construction.

    Returns:
        Markdown with all relative links converted to absolute raw GitHub URLs.
    """
    folder_path = agent.get("folder_path") or ""
    parsed = parse_github_tree_url(agent.get("github_url") or "")
    owner, repo, branch = ("Shubhamsaboo", "awesome-llm-apps", default_branch)
    if parsed:
        owner, repo, branch = parsed
    # If we have a parsed URL, still allow override via default_branch
    if parsed and default_branch != "main":
        branch = default_branch

    repo_raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/"
    folder_raw_base = f"{repo_raw_base}{folder_path}/" if folder_path else repo_raw_base

    def replace_url(match):
        full = match.group(0)
        link = match.group(2).strip()
        if link.startswith(("http://", "https://", "#", "mailto:")):
            return full
        if link.startswith("/"):
            return f"{match.group(1)}({repo_raw_base}{link.lstrip('/')})"
        if link.startswith("./"):
            return f"{match.group(1)}({folder_raw_base}{link[2:]})"
        if link.startswith("../"):
            cleaned = re.sub(r"^\\.\\./", "", link)
            return f"{match.group(1)}({repo_raw_base}{cleaned})"
        return f"{match.group(1)}({folder_raw_base}{link})"

    return re.sub(r"(!?\[[^\]]*\])\(([^)]+)\)", replace_url, markdown)


def safe_mermaid_label(value: str) -> str:
    """Sanitize a string for use as a Mermaid diagram label.

    Args:
        value: Input string to sanitize.

    Returns:
        Sanitized string safe for Mermaid labels (max 40 chars).
    """
    # Remove HTML tags and special characters, but keep alphanumeric, spaces, hyphens, underscores
    value = re.sub(r"<[^>]+>", "", value or "")  # Remove HTML tags
    # Keep alphanumeric, spaces, hyphens, underscores, and periods (hyphen at end of char class)
    value = re.sub(r"[^a-zA-Z0-9 _\\.-]", "", value).strip()
    return value[:40] or "Other"


def build_agent_diagram(agent: dict) -> str:
    """Generate a Mermaid diagram showing an agent's architecture.

    Args:
        agent: Agent dictionary with frameworks, llm_providers, and design_pattern.

    Returns:
        Mermaid diagram specification as a string.
    """
    frameworks = agent.get("frameworks") or []
    providers = agent.get("llm_providers") or []
    fw = safe_mermaid_label((frameworks[0] if frameworks else "App").title())
    prov = safe_mermaid_label((providers[0] if providers else "LLM").upper())
    pattern = safe_mermaid_label((agent.get("design_pattern") or "other").replace("_", " ").title())

    return f"""
graph LR
  User([User]) --> UI[Streamlit]
  UI --> Core[{pattern}]
  Core --> FW[{fw}]
  FW --> LLM[{prov}]
  LLM --> Response([Response])
""".strip()


def recommend_similar(agent: dict, agents: list[dict], *, limit: int = 6) -> list[dict]:
    """Recommend similar agents based on shared attributes.

    Uses Jaccard similarity on category, design pattern, frameworks,
    and LLM providers.

    Args:
        agent: Reference agent to find similar agents for.
        agents: Full list of candidate agents.
        limit: Maximum number of similar agents to return.

    Returns:
        List of similar agent dictionaries, sorted by similarity score.
    """
    def tokens(a: dict) -> set[str]:
        values = set()
        values.add(a.get("category") or "other")
        values.add(a.get("design_pattern") or "other")
        values.update(a.get("frameworks") or [])
        values.update(a.get("llm_providers") or [])
        return {str(v).lower() for v in values if v}

    base = tokens(agent)
    scored = []
    for other in agents:
        if other.get("id") == agent.get("id"):
            continue
        t = tokens(other)
        if not t:
            continue
        score = len(base & t) / max(1, len(base | t))
        if score > 0:
            scored.append((score, other))
    scored.sort(key=lambda x: (-x[0], (x[1].get("name") or "").lower()))
    return [a for _, a in scored[:limit]]


def normalize_agent_record(agent: dict, *, source_repo_url: str) -> dict:
    """Normalize and populate default values for an agent record.

    Ensures all required fields exist with sensible defaults.

    Args:
        agent: Raw agent dictionary from source data.
        source_repo_url: Base URL for generating clone commands.

    Returns:
        Normalized agent dictionary with all fields populated.
    """
    folder_path = agent.get("folder_path") or agent.get("readme_path") or ""
    readme_relpath = agent.get("readme_relpath") or (f"{folder_path}/README.md" if folder_path else "")
    clone_command = agent.get("clone_command") or f"git clone {source_repo_url}.git\ncd awesome-llm-apps/{folder_path}"

    normalized = dict(agent)
    # Only set defaults if key doesn't exist or is empty string (but preserve None)
    if "frameworks" not in normalized or normalized["frameworks"] == []:
        normalized["frameworks"] = []
    if "llm_providers" not in normalized or normalized["llm_providers"] == []:
        normalized["llm_providers"] = []
    if "category" not in normalized or normalized["category"] in ("", None):
        normalized["category"] = "other"
    if "complexity" not in normalized or normalized["complexity"] in ("", None):
        normalized["complexity"] = "intermediate"
    if "design_pattern" not in normalized:
        normalized["design_pattern"] = "other"
    normalized.setdefault("requires_gpu", False)
    normalized.setdefault("supports_local_models", False)
    normalized.setdefault("api_keys", [])
    normalized.setdefault("languages", [])
    normalized.setdefault("tags", [])
    normalized.setdefault("stars", None)
    normalized["folder_path"] = folder_path
    normalized["readme_relpath"] = readme_relpath
    normalized["clone_command"] = clone_command
    normalized.setdefault("updated_at", None)
    return normalized
