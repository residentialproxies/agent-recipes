"""
SEO Utilities for Agent Navigator
==================================
Utility functions for SEO optimization including slug generation,
sitemap enhancements, and schema markup generation.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from datetime import datetime

# Common prefixes that should be stripped from agent names for shorter slugs
SLUG_PREFIXES_TO_REMOVE = (
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


def slugify(value: str, *, max_length: int = 50) -> str:
    """Generate SEO-friendly URL slug from a string.

    Args:
        value: Input string to convert to slug.
        max_length: Maximum length of the slug (default 50).

    Returns:
        SEO-friendly slug string.

    Examples:
        >>> slugify("AI_PDF_Chatbot_with_LangChain")
        'pdf-chatbot-langchain'
        >>> slugify("Multi-Agent Research Assistant")
        'multi-agent-research-assistant'
    """
    if not value:
        return "agent"

    # Convert to lowercase and strip whitespace
    value = value.lower().strip()

    # Remove common prefixes
    for prefix in SLUG_PREFIXES_TO_REMOVE:
        if value.startswith(prefix):
            value = value[len(prefix) :]
            break

    # Transliterate non-ASCII characters (e.g., -> cafe)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))

    # Replace separators with hyphens
    value = re.sub(r"[_\s]+", "-", value)

    # Remove non-alphanumeric characters (except hyphens)
    value = re.sub(r"[^a-z0-9-]", "", value)

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


def get_sitemap_priority(agent: dict, max_stars: int = 50000) -> float:
    """Calculate sitemap priority based on GitHub stars.

    Args:
        agent: Agent dictionary with 'stars' key.
        max_stars: Star count that equals priority 1.0.

    Returns:
        Priority value between 0.1 and 1.0.
    """
    stars = agent.get("stars") or agent.get("github_stars") or 0

    if not isinstance(stars, int) or stars <= 0:
        return 0.3  # Default for new/unknown agents

    # Logarithmic scale to prevent top pages from dominating too much
    # Base priority of 0.5, scaling up based on stars
    import math

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


def generate_article_published_time(agent: dict) -> str | None:
    """Generate article published_time meta tag value.

    Args:
        agent: Agent dictionary.

    Returns:
        ISO 8601 datetime string or None.
    """
    added_at = agent.get("added_at")
    if added_at and isinstance(added_at, int) and added_at > 0:
        try:
            return datetime.fromtimestamp(added_at).strftime("%Y-%m-%dT%H:%M:%S%z")
        except (OSError, ValueError):
            pass
    return None


def generate_organization_schema(
    name: str = "Agent Navigator",
    url: str = "https://agent-navigator.com",
    description: str = "Discover and explore LLM agent examples with tutorials, code, and setup instructions.",
) -> str:
    """Generate Organization Schema.org markup.

    Args:
        name: Organization name.
        url: Organization website URL.
        description: Organization description.

    Returns:
        JSON-LD string.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": name,
        "url": url,
        "description": description,
        "sameAs": [
            "https://github.com/Shubhamsaboo/awesome-llm-apps",
        ],
    }
    return json.dumps(schema, indent=2)


def generate_collection_page_schema(
    category_name: str,
    category_url: str,
    agents: list[dict],
    base_url: str,
) -> str:
    """Generate CollectionPage Schema.org markup for category pages.

    Args:
        category_name: Name of the category.
        category_url: URL of the category page.
        agents: List of agents in the collection.
        base_url: Base URL of the site.

    Returns:
        JSON-LD string.
    """
    items = []
    for agent in agents[:20]:  # Limit to first 20 for performance
        agent_url = f"{base_url}/agents/{agent.get('id', '')}/"
        items.append(
            {
                "@type": "ListItem",
                "position": len(items) + 1,
                "name": agent.get("name", ""),
                "url": agent_url,
            }
        )

    schema = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"{category_name} - Agent Navigator",
        "description": f"Browse {len(agents)} {category_name.lower()} agent examples with code and tutorials.",
        "url": category_url,
        "itemListElement": items,
    }
    return json.dumps(schema, indent=2)


def generate_webpage_schema(
    title: str,
    description: str,
    url: str,
    published_time: str | None = None,
    modified_time: str | None = None,
) -> str:
    """Generate WebPage Schema.org markup for a generic page.

    Args:
        title: Page title.
        description: Page description.
        url: Page URL.
        published_time: ISO 8601 published datetime.
        modified_time: ISO 8601 modified datetime.

    Returns:
        JSON-LD string.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": title,
        "description": description,
        "url": url,
    }

    if published_time:
        schema["datePublished"] = published_time
    if modified_time:
        schema["dateModified"] = modified_time

    return json.dumps(schema, indent=2)


def generate_keywords_meta_tag(keywords: list[str]) -> str:
    """Generate HTML keywords meta tag.

    Args:
        keywords: List of keyword strings.

    Returns:
        HTML meta tag string.
    """
    if not keywords:
        return ""

    keywords_str = ", ".join(k for k in keywords[:15] if k)  # Limit to 15
    return f'<meta name="keywords" content="{html.escape(keywords_str)}" />'


def get_breadcrumb_links(
    agent: dict,
    _base_url: str,
) -> list[tuple[str, str]]:
    """Generate breadcrumb navigation links for an agent page.

    Args:
        agent: Agent dictionary.
        base_url: Base URL of the site.

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


def get_related_category_links(agent: dict, _all_agents: list[dict]) -> list[tuple[str, str]]:
    """Generate internal links to related category pages.

    Args:
        agent: Current agent dictionary.
        all_agents: List of all agents for finding related content.

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


def render_sitemap_url(
    loc: str,
    lastmod: str | None = None,
    changefreq: str | None = None,
    priority: float | None = None,
) -> str:
    """Render a single URL entry for sitemap XML.

    Args:
        loc: URL location.
        lastmod: Last modification date (YYYY-MM-DD).
        changefreq: Change frequency.
        priority: Priority (0.0-1.0).

    Returns:
        XML string for the URL entry.
    """
    parts = [f"    <url>\n        <loc>{html.escape(loc)}</loc>"]

    if lastmod:
        parts.append(f"\n        <lastmod>{lastmod}</lastmod>")
    if changefreq:
        parts.append(f"\n        <changefreq>{changefreq}</changefreq>")
    if priority is not None:
        parts.append(f"\n        <priority>{priority:.1f}</priority>")

    parts.append("\n    </url>")
    return "".join(parts)
