"""
Schema.org structured data generation functions.
"""

from __future__ import annotations

import json
from datetime import datetime

from src.export._utils import _strip_html


def _generate_schema_org(agent: dict, _base_url: str) -> str:
    """
    Generate SoftwareSourceCode Schema.org structured data.
    """
    name = _strip_html(agent.get("name", "Agent"))
    description = _strip_html(agent.get("description", ""))
    category = agent.get("category", "other")
    frameworks = agent.get("frameworks", [])
    providers = agent.get("llm_providers", [])
    stars = agent.get("stars")
    github_url = agent.get("github_url", "")
    languages = agent.get("languages", [])

    # Build keywords list
    keywords = [category.replace("_", " ")]
    keywords.extend(frameworks)
    keywords.extend(providers)
    keywords.extend(languages)

    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": name,
        "description": description or f"{name} - {category.replace('_', ' ')} LLM agent example",
        "codeRepository": github_url,
        "programmingLanguage": languages[0] if languages else "Python",
        "keywords": ", ".join(k for k in keywords if k),
    }

    # Add frameworks
    if frameworks:
        schema["frameworks"] = frameworks

    # Add aggregate rating if stars available
    if isinstance(stars, int) and stars > 0:
        # Normalize stars to 5-point scale (rough approximation)
        rating_value = min(5.0, 3.0 + (stars / 10000))  # Base 3.0, scale with popularity
        schema["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": round(rating_value, 1),
            "bestRating": "5",
            "ratingCount": stars,
        }

    return json.dumps(schema, indent=2)


def _generate_webpage_schema(
    agent: dict,
    base_url: str,
    published_time: str | None = None,
) -> str:
    """Generate WebPage Schema.org markup with published_time for article-like content.

    Args:
        agent: Agent dictionary.
        base_url: Base URL of the site.
        published_time: ISO 8601 published datetime (optional, auto-derived from agent).

    Returns:
        JSON-LD string.
    """
    agent_url = f"{base_url}/agents/{agent.get('id', '')}/"
    name = _strip_html(agent.get("name", "Agent"))
    description = _strip_html(agent.get("description", ""))

    schema = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": name,
        "description": description or f"{name} - LLM agent example",
        "url": agent_url,
    }

    # Add published time if available (from added_at)
    if published_time:
        schema["datePublished"] = published_time
    elif agent.get("added_at"):
        try:
            if isinstance(agent["added_at"], int) and agent["added_at"] > 0:
                schema["datePublished"] = datetime.fromtimestamp(agent["added_at"]).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass

    # Add modified time if available
    if agent.get("updated_at"):
        try:
            if isinstance(agent["updated_at"], int) and agent["updated_at"] > 0:
                schema["dateModified"] = datetime.fromtimestamp(agent["updated_at"]).strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass

    return json.dumps(schema, indent=2)


def _generate_organization_schema(
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


def _generate_collection_page_schema(
    category_name: str,
    category_url: str,
    agents: list[dict],
    description: str = "",
) -> str:
    """Generate CollectionPage Schema.org markup for category pages.

    Args:
        category_name: Name of the category.
        category_url: URL of the category page.
        agents: List of agents in the collection.
        description: Optional description of the collection.

    Returns:
        JSON-LD string.
    """
    items = []
    for agent in agents[:20]:  # Limit to first 20 for performance
        agent_id = agent.get("id", "")
        agent_url = f"{category_url.rsplit('/', 1)[0]}/agents/{agent_id}/" if category_url else ""
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
        "name": category_name,
        "description": description
        or f"Browse {len(agents)} {category_name.lower()} agent examples with code and tutorials.",
        "url": category_url,
    }

    if items:
        schema["itemListElement"] = items

    return json.dumps(schema, indent=2)


def _generate_faq_schema(category: str, count: int, _base_url: str) -> str:
    """
    Generate FAQPage Schema.org for category landing pages.
    """
    category_name = category.replace("_", " ").replace("-", " ").title()

    faqs = []

    # Generic FAQ items
    if category == "rag":
        faqs = [
            {
                "@type": "Question",
                "name": "What are RAG (Retrieval Augmented Generation) agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"RAG agents combine large language models with external knowledge retrieval to provide accurate, up-to-date responses. Browse {count} RAG agent examples with tutorials and code.",
                },
            },
            {
                "@type": "Question",
                "name": f"How do I build a RAG agent with {category_name}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Each agent example includes complete setup instructions, code, and documentation. Popular frameworks include LangChain, raw API calls, and vector databases.",
                },
            },
        ]
    elif category == "multi_agent":
        faqs = [
            {
                "@type": "Question",
                "name": "What are multi-agent systems?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Multi-agent systems use multiple AI agents working together, each specializing in different tasks. Browse {count} multi-agent architecture examples with CrewAI and custom frameworks.",
                },
            },
            {
                "@type": "Question",
                "name": "What frameworks support multi-agent systems?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Popular frameworks include CrewAI, LangChain agents, and custom orchestrators. Each example shows complete implementation patterns.",
                },
            },
        ]
    elif category == "openai":
        faqs = [
            {
                "@type": "Question",
                "name": "How do I use OpenAI's API for agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Browse {count} OpenAI agent examples showing GPT-4, GPT-3.5, function calling, Assistants API, and more. Each includes API key setup and best practices.",
                },
            },
            {
                "@type": "Question",
                "name": "What can I build with OpenAI agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Examples include chatbots, RAG systems, coding assistants, research tools, automation workflows, and vision applications.",
                },
            },
        ]
    elif category == "local":
        faqs = [
            {
                "@type": "Question",
                "name": "What are local LLM agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Local LLM agents run on your own hardware using models like Llama, Mistral, and others via Ollama. Browse {count} local agent examples for privacy and cost savings.",
                },
            },
            {
                "@type": "Question",
                "name": "What hardware do I need for local LLM agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Requirements vary by model size. Many examples work on CPU-only systems, while larger models benefit from GPUs with 8GB+ VRAM.",
                },
            },
        ]
    else:
        faqs = [
            {
                "@type": "Question",
                "name": f"What are {category_name.lower()} agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Browse {count} {category_name.lower()} agent examples with complete code, setup instructions, and documentation.",
                },
            },
            {
                "@type": "Question",
                "name": "How do I get started with these agents?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": "Each agent example includes quick start commands, requirements, and step-by-step setup instructions.",
                },
            },
        ]

    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs,
    }

    return json.dumps(schema, indent=2)


def _generate_breadcrumb_schema(items: list[tuple[str, str]], base_url: str) -> str:
    """
    Generate BreadcrumbList Schema.org structured data.

    Args:
        items: List of (name, url_path) tuples
        base_url: Base URL for the site
    """
    base_url = base_url.rstrip("/")
    item_list = []

    for i, (name, path) in enumerate(items, 1):
        item_list.append(
            {
                "@type": "ListItem",
                "position": i,
                "name": name,
                "item": f"{base_url}{path}" if path else base_url,
            }
        )

    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list,
    }

    return json.dumps(schema, indent=2)


def _generate_video_schema(
    name: str,
    description: str,
    thumbnail_url: str,
    embed_url: str,
    upload_date: str | None = None,
    duration: str | None = None,
) -> str:
    """Generate VideoObject Schema.org markup for demo videos.

    Args:
        name: Video title.
        description: Video description.
        thumbnail_url: URL to video thumbnail image.
        embed_url: URL to embedded video content.
        upload_date: ISO 8601 upload date (optional).
        duration: ISO 8601 duration format (e.g., "PT10M45S" for 10min 45sec).

    Returns:
        JSON-LD string.
    """
    schema = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": name,
        "description": description,
        "thumbnailUrl": thumbnail_url,
        "embedUrl": embed_url,
        "uploadDate": upload_date or datetime.now().strftime("%Y-%m-%d"),
    }

    if duration:
        schema["duration"] = duration

    return json.dumps(schema, indent=2)


def _generate_review_schema(
    agent_name: str,
    github_stars: int,
    base_url: str,
    agent_id: str | None = None,
) -> str:
    """Generate AggregateRating Schema.org markup using GitHub stars as rating proxy.

    Args:
        agent_name: Name of the agent/project.
        github_stars: Number of GitHub stars.
        base_url: Base URL of the site.
        agent_id: Optional agent ID for the review URL.

    Returns:
        JSON-LD string with AggregateRating markup.
    """
    # Normalize stars to a 5-point rating scale
    # Using a logarithmic scale: more stars = higher rating
    # Base rating of 3.0, increases with star count
    import math

    if github_stars <= 0:
        rating_value = 3.0
    else:
        # Logarithmic scaling: 3.0 base + up to 2.0 based on log10 of stars
        # This means 100 stars = ~4.0 rating, 1000 stars = ~4.6 rating
        log_stars = math.log10(max(1, github_stars))
        rating_value = min(5.0, 3.0 + (log_stars / 2.5))
        rating_value = round(rating_value, 1)

    # Use star count as rating count (community engagement)
    rating_count = min(github_stars, 10000)  # Cap for realistic display

    item_url = f"{base_url}/agents/{agent_id}/" if agent_id else base_url

    schema = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": agent_name,
        "url": item_url,
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": rating_value,
            "bestRating": "5",
            "worstRating": "1",
            "ratingCount": rating_count,
        },
        "author": {
            "@type": "Organization",
            "name": agent_name.split()[0] if agent_name else "Agent Navigator",
        },
    }

    return json.dumps(schema, indent=2)
