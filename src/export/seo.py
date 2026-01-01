"""
SEO-related functions: meta descriptions, Open Graph tags, keywords, etc.
"""

from __future__ import annotations

import html
from typing import Optional

from src.export._utils import generate_keywords as _generate_keywords_list


def _generate_meta_description(agent: dict) -> str:
    """
    Generate SEO-friendly meta description for an agent (120-158 characters).
    """
    category = agent.get("category", "other")
    frameworks = agent.get("frameworks", [])[:2]
    providers = agent.get("llm_providers", [])[:2]
    complexity = agent.get("complexity", "intermediate")

    # Build description - focus on action-oriented content
    parts = []

    # Start with category and what it does
    if category == "rag":
        parts.append("Build RAG applications")
    elif category == "multi_agent":
        parts.append("Multi-agent system")
    elif category == "chatbot":
        parts.append("AI chatbot")
    elif category == "agent":
        parts.append("LLM agent")
    else:
        parts.append(f"{category.replace('_', ' ').title()} agent")

    # Add key frameworks
    if frameworks:
        fw_list = ", ".join(f.title() for f in frameworks if f != "raw_api")
        if fw_list:
            parts.append(f"with {fw_list}")

    # Add providers
    if providers:
        provider_list = ", ".join(p.title() for p in providers)
        parts.append(f"using {provider_list}")

    # Build base description
    desc = " ".join(parts)

    # Add complexity info
    if complexity and complexity != "intermediate":
        desc += f". {complexity.title()} level project."

    # Ensure we hit target length (120-158 chars)
    min_target = 120
    max_target = 158

    # If too short, add more context
    if len(desc) < min_target:
        # Try longer suffixes first to reach target
        suffixes = [
            " Complete tutorial with code examples and setup guide.",
            " Includes code examples and step-by-step instructions.",
            " Production-ready example with documentation.",
            " Complete code example with setup instructions.",
        ]
        added = False
        for suffix in suffixes:
            test_desc = desc + suffix
            if min_target <= len(test_desc) <= max_target:
                desc = test_desc
                added = True
                break
            # If still too short but fits in max, use it and continue
            elif len(test_desc) <= max_target:
                desc = test_desc
                added = True

        # If still too short, extend with more context
        if not added or len(desc) < min_target:
            if desc.endswith("."):
                desc += " "
            else:
                desc += ". "
            desc += "Complete example with code and setup instructions."

    # If too long, truncate
    if len(desc) > max_target:
        desc = desc[: max_target - 3] + "..."

    return desc


def _generate_keywords_meta_tag(agent: dict) -> str:
    """Generate HTML keywords meta tag for an agent.

    Args:
        agent: Agent dictionary.

    Returns:
        HTML meta tag string or empty string if no keywords.
    """
    keywords = _generate_keywords_list(agent)
    if not keywords:
        return ""

    # Limit to 15 keywords for the meta tag
    keywords_str = ", ".join(k for k in keywords[:15] if k)
    return f'<meta name="keywords" content="{html.escape(keywords_str)}" />'


def _generate_open_graph_tags(
    title: str,
    description: str,
    url: str,
    image: str = "",
    og_type: str = "website",
    published_time: Optional[str] = None,
    author: Optional[str] = None,
) -> str:
    """
    Generate Open Graph and Twitter Card meta tags.

    Args:
        title: Page title.
        description: Page description.
        url: Page URL.
        image: OG image URL.
        og_type: Open Graph type (website, article, etc.).
        published_time: ISO 8601 published time (for article type).
        author: Article author name.
    """
    tags = []

    # Open Graph
    tags.append(f'<meta property="og:type" content="{html.escape(og_type)}" />')
    tags.append(f'<meta property="og:title" content="{html.escape(title)}" />')
    tags.append(f'<meta property="og:description" content="{html.escape(description)}" />')
    tags.append(f'<meta property="og:url" content="{html.escape(url)}" />')

    # Article-specific tags (include published_time by default for agent pages)
    if published_time:
        tags.append(f'<meta property="article:published_time" content="{html.escape(published_time)}" />')
    if og_type == "article":
        if author:
            tags.append(f'<meta property="article:author" content="{html.escape(author)}" />')

    if image:
        tags.append(f'<meta property="og:image" content="{html.escape(image)}" />')
        tags.append(f'<meta property="og:image:alt" content="{html.escape(title)}" />')
        tags.append('<meta property="og:image:width" content="1200" />')
        tags.append('<meta property="og:image:height" content="630" />')

    # Twitter Card
    tags.append('<meta name="twitter:card" content="summary_large_image" />')
    tags.append(f'<meta name="twitter:title" content="{html.escape(title)}" />')
    tags.append(f'<meta name="twitter:description" content="{html.escape(description)}" />')

    if image:
        tags.append(f'<meta name="twitter:image" content="{html.escape(image)}" />')

    # Twitter site/creator handles for brand attribution
    tags.append('<meta name="twitter:site" content="@agent_navigator" />')
    tags.append('<meta name="twitter:creator" content="@agent_navigator" />')

    return "\n    ".join(tags)


def _generate_page_title(agent: dict, base_name: str = "Agent Navigator") -> str:
    """Generate optimized title tag with keyword placement.

    Args:
        agent: Agent dictionary containing name, category, frameworks.
        base_name: Site name for suffix (default: "Agent Navigator").

    Returns:
        SEO-optimized title string (max 65 chars for Google display).
    """
    name = agent.get("name", "")
    category = agent.get("category", "").replace("_", " ")
    frameworks = agent.get("frameworks", [])
    framework = frameworks[0] if frameworks and frameworks[0] != "raw_api" else ""

    title_parts = [name]
    if framework:
        title_parts.append(f"with {framework.title()}")
    title_parts.append(base_name)

    title = " | ".join(title_parts)
    # Google displays up to ~65 chars for titles
    return title[:62] + "..." if len(title) > 65 else title
