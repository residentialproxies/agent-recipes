"""
Shared utility functions for static site export.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import datetime
from pathlib import Path


def _read_json(path: Path) -> list[dict]:
    """Read JSON file and return as list of dictionaries."""
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, content: str) -> None:
    """Write content to file, creating parent directories if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# Common prefixes that should be stripped from agent names for shorter slugs
_SLUG_PREFIXES_TO_REMOVE = (
    "ai_",
    "llm_",
    "agent_",
    "bot_",
    "chat_",
    "gpt_",
    "claude_",
    "auto",
    "smart",
    "intelligent",
)


def _slug(value: str, *, max_length: int = 50) -> str:
    """Generate SEO-friendly URL slug from a string.

    This improved slug function:
    - Removes common prefixes (ai_, llm_, agent_, etc.)
    - Limits length to 50 characters (configurable)
    - Transliterates non-ASCII characters
    - Uses meaningful keywords

    Args:
        value: Input string to convert to slug.
        max_length: Maximum length of the slug (default 50).

    Returns:
        SEO-friendly slug string.

    Examples:
        >>> _slug("AI_PDF_Chatbot_with_LangChain")
        'pdf-chatbot-langchain'
        >>> _slug("Multi-Agent Research Assistant")
        'multi-agent-research-assistant'
    """
    if not value:
        return "agent"

    # Convert to lowercase and strip whitespace
    value = value.lower().strip()

    # Remove common prefixes
    for prefix in _SLUG_PREFIXES_TO_REMOVE:
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break

    # Transliterate non-ASCII characters (e.g., -> cafe)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))

    # Replace separators with hyphens
    value = re.sub(r"[_\s]+", "-", value)

    # Convert non-alphanumeric runs into hyphens (better readability for punctuation-heavy IDs)
    value = re.sub(r"[^a-z0-9-]+", "-", value)

    # Remove consecutive hyphens
    value = re.sub(r"-{2,}", "-", value)

    # Strip leading/trailing hyphens
    value = value.strip("-")

    # Limit length but try to break at word boundary
    if len(value) > max_length:
        # Find the last hyphen before max_length
        last_hyphen = value.rfind("-", 0, max_length)
        value = value[:last_hyphen] if last_hyphen > max_length // 2 else value[:max_length].rstrip("-")

    return value or "agent"


def _iso_date(ts: int | None) -> str | None:
    """Convert Unix timestamp to ISO date string (YYYY-MM-DD)."""
    if not isinstance(ts, int) or ts <= 0:
        return None
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _category_icon(category: str) -> str:
    """Get the emoji icon for a category.

    Args:
        category: Category key (e.g., 'rag', 'chatbot').

    Returns:
        Emoji icon for the category, or default icon if not found.
    """
    icons = {
        "rag": "📚",
        "chatbot": "💬",
        "agent": "🤖",
        "multi_agent": "🧩",
        "automation": "⚙️",
        "search": "🔎",
        "vision": "🖼️",
        "voice": "🎙️",
        "coding": "🧑‍💻",
        "finance": "💹",
        "research": "🧪",
        "other": "✨",
    }
    # Also handle hyphenated categories by converting to underscore
    if isinstance(category, str) and "-" in category:
        category = category.replace("-", "_")
    category_key = category if isinstance(category, str) else "other"
    return icons.get(category_key or "other", "✨")


def _strip_html(text: str) -> str:
    """Strip HTML tags from text for use in plain text contexts like JSON."""
    import re

    return re.sub(r"<[^>]+>", "", text)


def _normalize_record(agent: dict) -> dict:
    """Normalize an agent record, filling in missing fields with defaults."""
    agent = dict(agent)
    agent.setdefault("id", _slug(agent.get("name") or "agent"))
    agent.setdefault("name", "Untitled")
    agent.setdefault("description", "")
    agent.setdefault("category", "other")
    agent.setdefault("frameworks", [])
    agent.setdefault("llm_providers", [])
    agent.setdefault("complexity", "intermediate")
    agent.setdefault("design_pattern", "other")
    agent.setdefault("stars", None)
    agent.setdefault("updated_at", None)
    agent.setdefault("github_url", "")
    agent.setdefault("codespaces_url", None)
    agent.setdefault("colab_url", None)
    agent.setdefault("api_keys", [])
    agent.setdefault("quick_start", "")
    agent.setdefault("clone_command", "")
    return agent


# SEO utility functions


def get_sitemap_priority(agent: dict, max_stars: int = 50000) -> float:
    """Calculate sitemap priority based on GitHub stars.

    Uses logarithmic scale to prevent top pages from dominating too much.

    Args:
        agent: Agent dictionary with 'stars' key.
        max_stars: Star count that equals priority 1.0.

    Returns:
        Priority value between 0.1 and 1.0.
    """
    stars = agent.get("stars") or agent.get("github_stars") or 0

    if not isinstance(stars, int) or stars <= 0:
        return 0.3  # Default for new/unknown agents

    # Logarithmic scale: base priority of 0.5, scaling up based on stars
    priority = 0.5 + 0.5 * (math.log(stars + 1) / math.log(max_stars + 1))
    return min(1.0, max(0.1, priority))


def get_sitemap_changefreq(agent: dict, page_type: str = "agent") -> str:
    """Determine appropriate changefreq based on page type and agent metadata.

    Args:
        agent: Agent dictionary.
        page_type: Type of page ('agent', 'category', 'homepage').

    Returns:
        Changefreq string: 'always', 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'never'.
    """
    if page_type == "homepage":
        return "daily"

    if page_type == "category":
        return "weekly"

    # For agent pages, base on complexity and age
    complexity = agent.get("complexity", "intermediate")
    updated_at = agent.get("updated_at")

    # Newer or more complex projects update more frequently
    if complexity == "advanced":
        return "monthly"
    elif complexity == "beginner":
        return "yearly"

    # Check if recently updated (within last 6 months)
    if updated_at:
        try:
            if isinstance(updated_at, int) and updated_at > 0:
                updated_date = datetime.fromtimestamp(updated_at)
                days_since_update = (datetime.now() - updated_date).days
                if days_since_update < 180:
                    return "monthly"
        except (OSError, ValueError):
            pass

    return "monthly"


def get_agent_lastmod(agent: dict) -> str | None:
    """Get the last modified date for an agent.

    Args:
        agent: Agent dictionary.

    Returns:
        ISO date string (YYYY-MM-DD) or None.
    """
    # Try updated_at first, then added_at, then fallback to None
    updated_at = agent.get("updated_at") or agent.get("added_at")
    if updated_at and isinstance(updated_at, int) and updated_at > 0:
        try:
            return datetime.fromtimestamp(updated_at).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass
    return None


def generate_keywords(agent: dict) -> list[str]:
    """Generate SEO keywords for an agent.

    Args:
        agent: Agent dictionary.

    Returns:
        List of keyword strings.
    """
    keywords = set()

    # Category
    category = agent.get("category", "")
    if category:
        keywords.add(category.replace("_", " "))
        keywords.add(f"{category.replace('_', ' ')} agent")

    # Frameworks
    for fw in agent.get("frameworks", []):
        if fw and fw != "raw_api":
            keywords.add(fw)
            keywords.add(f"{fw} agent")

    # LLM providers
    for provider in agent.get("llm_providers", []):
        if provider:
            keywords.add(f"{provider} agent")
            if provider == "openai":
                keywords.add("gpt")
            elif provider == "anthropic":
                keywords.add("claude")

    # Complexity
    complexity = agent.get("complexity", "")
    if complexity and complexity != "intermediate":
        keywords.add(f"{complexity} project")

    # Design pattern
    pattern = agent.get("design_pattern", "")
    if pattern and pattern != "other":
        keywords.add(pattern.replace("_", " "))

    # Languages
    for lang in agent.get("languages", []):
        if lang:
            keywords.add(f"{lang} agent")
            keywords.add(lang)

    # Tags
    for tag in agent.get("tags", [])[:10]:  # Limit tags
        if tag:
            keywords.add(tag.lower())

    return sorted(keywords)


def get_breadcrumb_links(agent: dict) -> list[tuple[str, str]]:
    """Generate breadcrumb navigation links for an agent page.

    Args:
        agent: Agent dictionary.

    Returns:
        List of (name, path) tuples for breadcrumbs.
    """
    breadcrumbs = [("Home", "/")]

    # Add category link
    category = agent.get("category", "")
    if category and category != "other":
        category_name = category.replace("_", " ").title()
        breadcrumbs.append((category_name, f"/#{category}"))

    # Add agents browse link
    breadcrumbs.append(("Agents", "/#browse"))

    # Current page
    breadcrumbs.append((agent.get("name", "Agent"), f"/agents/{agent.get('id', '')}/"))

    return breadcrumbs


def get_related_category_links(agent: dict) -> list[tuple[str, str]]:
    """Generate internal links to related category pages.

    Args:
        agent: Current agent dictionary.

    Returns:
        List of (text, url) tuples for related links.
    """
    links = []

    # Same category link
    category = agent.get("category", "")
    if category and category != "other":
        category_name = category.replace("_", " ").title()
        links.append((f"All {category_name} Agents", f"/#{category}"))

    # Framework links
    for fw in agent.get("frameworks", [])[:2]:
        if fw and fw != "raw_api":
            links.append((f"Popular in {fw.title()}", f"/#{fw}"))

    # Provider links
    for provider in agent.get("llm_providers", [])[:2]:
        if provider:
            links.append((f"{provider.title()} Agents", f"/#{provider}"))

    # Complexity link
    complexity = agent.get("complexity", "")
    if complexity and complexity != "intermediate":
        links.append((f"{complexity.title()} Projects", f"/#{complexity}"))

    return links
