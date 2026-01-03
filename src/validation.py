"""
Data validation and quality utilities for Agent Navigator.

Provides:
- validate_agent_data(): Check required fields in agent records
- generate_seo_description(): Create SEO-friendly descriptions for empty ones
- filter_low_value_tags(): Remove generic stop words from tags
"""

from __future__ import annotations

from typing import Any

# Generic stop words that add little value to tags/search
_LOW_VALUE_STOPWORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "was",
    "are",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "this",
    "that",
    "these",
    "those",
    "allows",
    "app",
    "application",
    "available",
    "based",
    "describing",
    "detailed",
    "download",
    "enter",
    "etc",
    "features",
    "format",
    "friendly",
    "generate",
    "generated",
    "generation",
    "input",
    "instruments",
    "interface",
    "listening",
    "mood",
    "mp3",
    "music",
    "output",
    "prompt",
    "simple",
    "they",
    "track",
    "type",
    "user",
    "users",
    "want",
    "using",
    "use",
    "used",
    "uses",
}


# Valid categories for validation
_VALID_CATEGORIES = {
    "rag",
    "chatbot",
    "agent",
    "multi_agent",
    "automation",
    "search",
    "vision",
    "voice",
    "coding",
    "finance",
    "research",
    "other",
}


# Valid complexity levels
_VALID_COMPLEXITY = {"beginner", "intermediate", "advanced"}


def validate_agent_data(agent: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate agent data and check required fields.

    Args:
        agent: Agent dictionary to validate.

    Returns:
        Tuple of (is_valid, list_of_issues). Empty issues list means valid.
    """
    issues: list[str] = []

    # Check required fields
    if not agent.get("id") or not str(agent.get("id", "")).strip():
        issues.append("Missing required field: id")

    if not agent.get("name") or not str(agent.get("name", "")).strip():
        issues.append("Missing required field: name")

    # Check description
    description = str(agent.get("description", "")).strip()
    if not description or len(description) < 10:
        issues.append("Missing or too short description (consider auto-generating)")

    # Check category validity
    category = agent.get("category")
    if category not in _VALID_CATEGORIES:
        issues.append(f"Invalid category: {category!r} (must be one of {sorted(_VALID_CATEGORIES)})")

    # Check complexity validity
    complexity = agent.get("complexity")
    if complexity and complexity not in _VALID_COMPLEXITY:
        issues.append(f"Invalid complexity: {complexity!r} (must be one of {sorted(_VALID_COMPLEXITY)})")

    # Check arrays are actually lists
    for field in ("frameworks", "llm_providers", "languages", "tags"):
        value = agent.get(field)
        if value is not None and not isinstance(value, list):
            issues.append(f"Field '{field}' must be a list, got {type(value).__name__}")

    # Check github_url format if present
    github_url = agent.get("github_url")
    if github_url and isinstance(github_url, str) and not github_url.startswith(("http://", "https://", "git@")):
        issues.append(f"Invalid github_url format: {github_url[:50]}")

    return len(issues) == 0, issues


def generate_seo_description(agent: dict[str, Any]) -> str:
    """
    Generate SEO-friendly description when empty or too short.

    Creates a descriptive summary based on the agent's category,
    frameworks, and LLM providers.

    Args:
        agent: Agent dictionary.

    Returns:
        SEO-friendly description string.
    """
    # If existing description is good, return it
    existing = str(agent.get("description", "")).strip()
    if len(existing) >= 50:
        return existing

    category = agent.get("category", "other")
    frameworks = agent.get("frameworks", []) or []
    providers = agent.get("llm_providers", []) or []

    # Get primary framework and provider
    primary_fw = frameworks[0] if frameworks else "Python"
    primary_provider = providers[0] if providers else "OpenAI"

    # Category-specific templates
    templates = {
        "rag": (
            f"Build RAG (Retrieval Augmented Generation) applications using {primary_fw} "
            f"with {primary_provider}. Complete example with vector database integration, "
            f"document loading, and LLM query engine."
        ),
        "chatbot": (
            f"Create an AI chatbot using {primary_fw} with {primary_provider}. "
            f"Includes conversation memory, user interface, and message handling."
        ),
        "multi_agent": (
            f"Multi-agent system using {primary_fw}. Multiple AI agents collaborate "
            f"on complex tasks with tool use, delegation, and coordination patterns."
        ),
        "agent": (
            f"LLM agent implementation using {primary_fw} with {primary_provider}. "
            f"Features tool use, state management, and task execution capabilities."
        ),
        "automation": (
            f"Workflow automation agent using {primary_fw} with {primary_provider}. "
            f"Automate repetitive tasks with AI-powered decision making."
        ),
        "search": (
            f"AI-powered search implementation using {primary_fw} with {primary_provider}. "
            f"Semantic search with vector embeddings and intelligent ranking."
        ),
        "vision": (
            f"Computer vision AI agent using {primary_fw} with {primary_provider}. "
            f"Process and analyze images with multimodal LLM capabilities."
        ),
        "voice": (
            f"Voice-enabled AI agent using {primary_fw} with {primary_provider}. "
            f"Speech-to-text, text-to-speech, and conversational AI capabilities."
        ),
        "coding": (
            f"AI coding assistant using {primary_fw} with {primary_provider}. "
            f"Code generation, refactoring, and developer workflow automation."
        ),
        "finance": (
            f"Financial analysis AI agent using {primary_fw} with {primary_provider}. "
            f"Portfolio tracking, market analysis, and financial insights."
        ),
        "research": (
            f"Research assistant AI agent using {primary_fw} with {primary_provider}. "
            f"Paper analysis, literature review, and knowledge synthesis."
        ),
    }

    # Get category-specific template or generate generic
    template = templates.get(category)
    if template:
        return template

    # Generic fallback
    return (
        f"{category.replace('_', ' ').title()} agent example using {primary_fw} "
        f"with {primary_provider}. Includes code and setup instructions."
    )


def filter_low_value_tags(tags: list[str] | tuple[str, ...]) -> list[str]:
    """
    Remove generic stop words from tags to improve search quality.

    Filters out common words that add little semantic value while
    preserving meaningful technical terms.

    Args:
        tags: List of tag strings to filter.

    Returns:
        Filtered list of tags with low-value words removed.
    """
    filtered = []
    for tag in tags:
        tag_str = str(tag).lower().strip()
        # Skip if it's a stop word or too short
        if tag_str in _LOW_VALUE_STOPWORDS or len(tag_str) <= 2:
            continue
        filtered.append(tag)
    return filtered
