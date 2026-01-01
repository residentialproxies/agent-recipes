"""
Agent Navigator - Static Site Exporter (Legacy)
===============================================
This module is kept for backward compatibility.
New code should use the src.export package instead.

Usage:
  from src.export import export_site
  python3 -m src.export --output site --base-url https://example.com
"""

from __future__ import annotations

# Re-export everything from the new package for backward compatibility
from src.export.export import export_site, main
from src.export.templates import (
    _layout,
    _render_index,
    _render_agent,
    _render_category_landing,
    _render_comparison_page,
    _render_tutorial_page,
    _render_comparison_index,
    _render_tutorial_index,
    _render_404,
    _render_assets,
    _render_headers,
    _render_sitemap,
)
from src.export.seo import (
    _generate_meta_description,
    _generate_open_graph_tags,
)
from src.export.schema import (
    _generate_schema_org,
    _generate_faq_schema,
    _generate_breadcrumb_schema,
)
from src.export.data import (
    _find_related_agents,
    CATEGORY_PAGES,
    FRAMEWORK_PAGES,
    PROVIDER_PAGES,
    COMPLEXITY_PAGES,
    COMPARISON_CONFIGS,
    TUTORIAL_CONFIGS,
)

__all__ = [
    "export_site",
    "main",
    "_layout",
    "_render_index",
    "_render_agent",
    "_render_category_landing",
    "_render_comparison_page",
    "_render_tutorial_page",
    "_render_comparison_index",
    "_render_tutorial_index",
    "_render_404",
    "_render_assets",
    "_render_headers",
    "_render_sitemap",
    "_generate_meta_description",
    "_generate_open_graph_tags",
    "_generate_schema_org",
    "_generate_faq_schema",
    "_generate_breadcrumb_schema",
    "_find_related_agents",
    "CATEGORY_PAGES",
    "FRAMEWORK_PAGES",
    "PROVIDER_PAGES",
    "COMPLEXITY_PAGES",
    "COMPARISON_CONFIGS",
    "TUTORIAL_CONFIGS",
]

import argparse
import html
import json
import logging
import os
import re
from dataclasses import asdict, is_dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _slug(value: str) -> str:
    safe = "".join(c.lower() if c.isalnum() else "-" for c in value.strip())
    safe = "-".join([p for p in safe.split("-") if p])
    return safe[:80] or "agent"


def _iso_date(ts: Optional[int]) -> Optional[str]:
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
    # Inline category icons to avoid import issues when running as script
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


def _strip_html(text: str) -> str:
    """Strip HTML tags from text for use in plain text contexts like JSON."""
    return re.sub(r"<[^>]+>", "", text)


def _generate_schema_org(agent: dict, base_url: str) -> str:
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


def _generate_faq_schema(category: str, count: int, base_url: str) -> str:
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
                "name": f"What are RAG (Retrieval Augmented Generation) agents?",
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
                    "text": f"Each agent example includes complete setup instructions, code, and documentation. Popular frameworks include LangChain, raw API calls, and vector databases.",
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
                    "text": f"Popular frameworks include CrewAI, LangChain agents, and custom orchestrators. Each example shows complete implementation patterns.",
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
        item_list.append({
            "@type": "ListItem",
            "position": i,
            "name": name,
            "item": f"{base_url}{path}" if path else base_url,
        })

    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": item_list,
    }

    return json.dumps(schema, indent=2)


def _find_related_agents(agent: dict, all_agents: list[dict], limit: int = 4) -> list[dict]:
    """
    Find related agents based on category, frameworks, and providers.
    Uses Jaccard similarity for ranking.
    """
    agent_id = agent.get("id", "")
    agent_cat = agent.get("category", "")
    agent_frameworks = set(agent.get("frameworks", []))
    agent_providers = set(agent.get("llm_providers", []))

    scores = []
    for other in all_agents:
        if other.get("id") == agent_id:
            continue

        score = 0

        # Category match (highest weight)
        if other.get("category") == agent_cat:
            score += 3

        # Framework overlap (Jaccard)
        other_frameworks = set(other.get("frameworks", []))
        if agent_frameworks and other_frameworks:
            intersection = len(agent_frameworks & other_frameworks)
            union = len(agent_frameworks | other_frameworks)
            score += 2 * (intersection / union) if union > 0 else 0

        # Provider overlap (Jaccard)
        other_providers = set(other.get("llm_providers", []))
        if agent_providers and other_providers:
            intersection = len(agent_providers & other_providers)
            union = len(agent_providers | other_providers)
            score += 1 * (intersection / union) if union > 0 else 0

        if score > 0:
            scores.append((score, other))

    # Sort by score descending and return top matches
    scores.sort(key=lambda x: -x[0])
    return [agent for _, agent in scores[:limit]]


def _generate_open_graph_tags(
    title: str,
    description: str,
    url: str,
    image: str = "",
    og_type: str = "website",
) -> str:
    """
    Generate Open Graph and Twitter Card meta tags.
    """
    tags = []

    # Open Graph
    tags.append(f'<meta property="og:type" content="{html.escape(og_type)}" />')
    tags.append(f'<meta property="og:title" content="{html.escape(title)}" />')
    tags.append(f'<meta property="og:description" content="{html.escape(description)}" />')
    tags.append(f'<meta property="og:url" content="{html.escape(url)}" />')

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

    return "\n    ".join(tags)


def _normalize_record(agent: dict) -> dict:
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


def _layout(
    title: str,
    description: str,
    body: str,
    *,
    canonical: Optional[str] = None,
    asset_prefix: str = "/",
    schema_json: Optional[str] = None,
    og_tags: Optional[str] = None,
) -> str:
    title_e = html.escape(title)
    desc_e = html.escape(description)
    canonical_tag = f'<link rel="canonical" href="{html.escape(canonical)}" />' if canonical else ""
    prefix = html.escape(asset_prefix)

    # Schema.org structured data
    schema_tag = ""
    if schema_json:
        schema_tag = f'\n    <script type="application/ld+json">\n{schema_json}\n    </script>'

    # Open Graph tags
    og_section = ""
    if og_tags:
        og_section = f"\n    {og_tags}"

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title_e}</title>
    <meta name="description" content="{desc_e}" />
    {canonical_tag}{og_section}{schema_tag}
    <link rel="stylesheet" href="{prefix}assets/style.css" />
  </head>
  <body>
    <header class="topbar">
      <div class="wrap">
        <a class="brand" href="/">Agent Navigator</a>
        <nav class="nav">
          <a href="/#browse">Browse</a>
          <a href="/#about">About</a>
        </nav>
      </div>
    </header>
    <main class="wrap">
      {body}
    </main>
    <script src="{prefix}assets/app.js"></script>
  </body>
</html>
"""


def _render_index(agents: list[dict], base_url: Optional[str] = None) -> str:
    total = len(agents)
    cats = {}
    for a in agents:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    cat_html = "".join(
        f'<span class="chip">{html.escape(k.replace("_"," "))} <span class="muted">({v})</span></span>'
        for k, v in sorted(cats.items(), key=lambda kv: (-kv[1], kv[0]))
    )

    cards = []
    for a in agents:
        icon = _category_icon(a["category"])
        name = html.escape(a["name"])
        desc = html.escape(a.get("description") or "")
        href = f"/agents/{html.escape(a['id'])}/"
        badges = []
        if a.get("frameworks"):
            badges.append(html.escape(a["frameworks"][0]))
        if a.get("llm_providers"):
            badges.append(html.escape(a["llm_providers"][0]))
        if isinstance(a.get("stars"), int):
            badges.append(f"⭐ {a['stars']:,}")
        badge_html = "".join(f'<span class="badge">{b}</span>' for b in badges[:3])
        cards.append(
            f"""
<a class="card" href="{href}" data-name="{name.lower()}" data-desc="{desc.lower()}" data-cat="{html.escape(a['category'])}">
  <div class="card-title">{icon} {name}</div>
  <div class="card-desc">{desc}</div>
  <div class="card-badges">{badge_html}</div>
</a>
"""
        )

    # SEO elements
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    description = f"Search and browse {total} runnable LLM agent/app examples with tutorials, code, and setup instructions. RAG, chatbots, multi-agent systems, and more."

    og_tags = _generate_open_graph_tags(
        title="Agent Navigator - LLM Agent Examples & Tutorials",
        description=description,
        url=site_url,
        image=f"{site_url}/assets/og-image.png",
    )

    # Schema.org for homepage
    schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "Agent Navigator",
        "description": description,
        "url": site_url,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{site_url}/?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }

    body = f"""
<section class="hero">
  <h1>Agent Navigator</h1>
  <p class="lead">Search and browse runnable LLM agent/app examples indexed from a source repository.</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">agents</div></div>
    <div class="stat"><div class="stat-num">{len(cats)}</div><div class="stat-label">categories</div></div>
  </div>
</section>

<section id="browse">
  <h2>Browse</h2>
  <p class="muted">Use search or filter by category.</p>
  <input id="q" class="search" placeholder="Search agents (name/description)..." />
  <div class="chips">{cat_html}</div>
  <div id="cards" class="grid">
    {''.join(cards)}
  </div>
</section>

<section id="about" class="about">
  <h2>About</h2>
  <p>This static site is generated from <code>data/agents.json</code> for SEO and fast browsing. For the full interactive experience, run the Streamlit app.</p>
  <pre><code>streamlit run src/app.py</code></pre>
</section>
"""

    return _layout(
        "Agent Navigator - LLM Agent Examples & Tutorials",
        description,
        body,
        canonical=site_url + "/" if base_url else None,
        asset_prefix="./",
        schema_json=json.dumps(schema, indent=2),
        og_tags=og_tags,
    )


def _render_agent(agent: dict, base_url: Optional[str] = None, all_agents: Optional[list[dict]] = None) -> str:
    icon = _category_icon(agent["category"])
    name = html.escape(agent["name"])
    desc = html.escape(agent.get("description") or "")
    category = html.escape(agent.get("category") or "other").replace("_", " ")
    category_raw = agent.get("category") or "other"
    complexity = html.escape(agent.get("complexity") or "intermediate")
    updated = _iso_date(agent.get("updated_at"))
    frameworks = ", ".join(html.escape(x) for x in (agent.get("frameworks") or [])[:6]) or "—"
    providers = ", ".join(html.escape(x) for x in (agent.get("llm_providers") or [])[:6]) or "—"
    api_keys = ", ".join(html.escape(x) for x in (agent.get("api_keys") or [])[:10]) or "—"

    links = []
    if agent.get("github_url"):
        links.append(f'<a class="btn" href="{html.escape(agent["github_url"])}" target="_blank" rel="noreferrer">GitHub</a>')
    if agent.get("codespaces_url"):
        links.append(f'<a class="btn" href="{html.escape(agent["codespaces_url"])}" target="_blank" rel="noreferrer">Codespaces</a>')
    if agent.get("colab_url"):
        links.append(f'<a class="btn" href="{html.escape(agent["colab_url"])}" target="_blank" rel="noreferrer">Colab</a>')
    link_html = " ".join(links) or ""

    stars = agent.get("stars")
    stars_html = f"<div><b>Repo stars:</b> {stars:,}</div>" if isinstance(stars, int) else ""
    updated_html = f"<div><b>Updated:</b> {html.escape(updated)}</div>" if updated else ""

    qs = html.escape((agent.get("quick_start") or "").strip())[:1200]
    clone = html.escape((agent.get("clone_command") or "").strip())[:400]

    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    agent_url = f"{site_url}/agents/{agent['id']}/"
    canonical = agent_url if base_url else None

    # Generate SEO elements
    meta_desc = _generate_meta_description(agent)
    schema = _generate_schema_org(agent, site_url)
    og_tags = _generate_open_graph_tags(
        title=f"{agent['name']} - Agent Navigator",
        description=meta_desc,
        url=agent_url,
        image=f"{site_url}/assets/og-agent-{agent['id']}.png",
        og_type="article",
    )

    # Generate breadcrumb schema
    breadcrumbs = [
        ("Home", "/"),
        ("Agents", "/#browse"),
        (agent["name"], f"/agents/{agent['id']}/"),
    ]
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if base_url else ""

    # Combine schemas
    combined_schema = schema
    if breadcrumb_schema:
        # Combine both schemas into an array
        schema_list = [json.loads(schema), json.loads(breadcrumb_schema)]
        combined_schema = json.dumps(schema_list, indent=2)

    # Generate related agents section
    related_html = ""
    if all_agents:
        related = _find_related_agents(agent, all_agents, limit=4)
        if related:
            related_cards = []
            for r in related:
                r_icon = _category_icon(r.get("category", "other"))
                r_name = html.escape(r.get("name", ""))
                r_desc = html.escape((r.get("description") or "")[:80])
                r_href = f"/agents/{html.escape(r.get('id', ''))}/"
                related_cards.append(f'''
<a class="card related-card" href="{r_href}">
  <div class="card-title">{r_icon} {r_name}</div>
  <div class="card-desc">{r_desc}</div>
</a>''')
            related_html = f'''
<section class="related-section">
  <h3>Related Agents</h3>
  <div class="related-grid">
    {''.join(related_cards)}
  </div>
</section>
'''

    # Breadcrumb HTML navigation
    breadcrumb_nav = f'''
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/#browse">Agents</a></li>
    <li aria-current="page">{name}</li>
  </ol>
</nav>
'''

    body = f"""
{breadcrumb_nav}
<h1>{icon} {name}</h1>
<p class="lead">{desc}</p>
<div class="row">{link_html}</div>

<div class="grid2">
  <div class="panel">
    <h3>Quick Start</h3>
    <div><b>API keys:</b> {api_keys}</div>
    <pre><code>{clone}</code></pre>
    <pre><code>{qs}</code></pre>
  </div>
  <div class="panel">
    <h3>Details</h3>
    <div><b>Category:</b> <a href="/#browse" class="category-link">{category}</a></div>
    <div><b>Complexity:</b> {complexity}</div>
    {updated_html}
    {stars_html}
    <div><b>Frameworks:</b> {frameworks}</div>
    <div><b>Providers:</b> {providers}</div>
  </div>
</div>
{related_html}
"""

    return _layout(
        f"{agent['name']} – Agent Navigator",
        meta_desc,
        body,
        canonical=canonical,
        asset_prefix="../../",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_category_landing(
    category_key: str,
    category_name: str,
    agents: list[dict],
    *,
    base_url: Optional[str],
    description: str,
    heading: str,
    intro_content: str = "",
    related_links: list[tuple[str, str]] = None,
    faq_data: list[dict] = None,
) -> str:
    """Render a pSEO category landing page."""
    icon = _category_icon(category_key.split("-")[0] if "-" in category_key else category_key)
    count = len(agents)

    # Build agent cards
    cards = []
    for a in agents[:50]:  # Limit for performance
        name = html.escape(a["name"])
        desc = html.escape(a.get("description") or "")[:150]
        href = f"/agents/{html.escape(a['id'])}/"
        badges = []

        if a.get("frameworks"):
            badges.append(html.escape(a["frameworks"][0]))
        if a.get("llm_providers"):
            badges.append(html.escape(a["llm_providers"][0]))

        badge_html = "".join(f'<span class="badge">{b}</span>' for b in badges[:2])
        cards.append(
            f"""
<a class="card" href="{href}">
  <div class="card-title">{name}</div>
  <div class="card-desc">{desc}</div>
  <div class="card-badges">{badge_html}</div>
</a>
"""
        )

    # Build framework/provider stats
    frameworks = {}
    providers = {}
    complexities = {}
    for a in agents:
        for fw in a.get("frameworks", []):
            frameworks[fw] = frameworks.get(fw, 0) + 1
        for p in a.get("llm_providers", []):
            providers[p] = providers.get(p, 0) + 1
        c = a.get("complexity", "intermediate")
        complexities[c] = complexities.get(c, 0) + 1

    fw_stats = " ".join(
        f'<span class="chip">{html.escape(k.title())} ({v})</span>'
        for k, v in sorted(frameworks.items(), key=lambda x: -x[1])[:5]
    )
    provider_stats = " ".join(
        f'<span class="chip">{html.escape(k.title())} ({v})</span>'
        for k, v in sorted(providers.items(), key=lambda x: -x[1])[:5]
    )
    complexity_stats = " ".join(
        f'<span class="chip">{html.escape(k.title())} ({v})</span>'
        for k, v in sorted(complexities.items(), key=lambda x: -x[1])
    )

    # SEO elements
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    category_url = f"{site_url}/{category_key}/"

    meta_desc = f"{description} Browse {count} examples with code, tutorials, and setup instructions."

    og_tags = _generate_open_graph_tags(
        title=f"{heading} - Agent Navigator",
        description=meta_desc,
        url=category_url,
        image=f"{site_url}/assets/og-{category_key}.png",
    )

    # FAQ Schema - map category key to schema type
    schema_category = {
        "rag-tutorials": "rag",
        "openai-agents": "openai",
        "multi-agent-systems": "multi_agent",
        "local-llm-agents": "local",
    }.get(category_key, category_key)

    # Use custom FAQ data if provided, otherwise generate based on category
    if faq_data:
        faqs = faq_data
    else:
        # Generate default FAQ schema
        faqs = json.loads(_generate_faq_schema(schema_category, count, site_url)).get("mainEntity", [])

    # Build breadcrumb schema
    breadcrumbs = [
        ("Home", "/"),
        (category_name, f"/{category_key}/"),
    ]
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if base_url else ""

    # Combine schemas
    faq_schema_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs,
    }
    combined_schema = json.dumps(faq_schema_obj, indent=2)
    if breadcrumb_schema:
        schema_list = [faq_schema_obj, json.loads(breadcrumb_schema)]
        combined_schema = json.dumps(schema_list, indent=2)

    # Build related links section
    related_html = ""
    if related_links:
        links_html = "".join(
            f'<a class="chip" href="{html.escape(href)}">{html.escape(text)}</a>'
            for text, href in related_links
        )
        related_html = f'<section><h2>Related Topics</h2><div class="chips">{links_html}</div></section>'

    # Build FAQ HTML
    faq_html = ""
    if faqs:
        faq_items = ""
        for faq in faqs:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f'''
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>'''
        faq_html = f'''
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>'''

    body = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li aria-current="page">{html.escape(category_name)}</li>
  </ol>
</nav>

<section class="hero">
  <h1>{icon} {heading}</h1>
  <p class="lead">{description}</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{count}</div><div class="stat-label">examples</div></div>
  </div>
</section>

{intro_content}

<section>
  <h2>Popular Frameworks</h2>
  <div class="chips">{fw_stats}</div>

  <h2>LLM Providers</h2>
  <div class="chips">{provider_stats}</div>

  <h2>Complexity Levels</h2>
  <div class="chips">{complexity_stats}</div>
</section>

{related_html}

<section>
  <h2>All {heading} Examples</h2>
  <div class="grid">
    {''.join(cards)}
  </div>
</section>

{faq_html}

<section class="about">
  <p><a class="muted" href="/">&larr; Back to all agents</a></p>
</section>
"""

    return _layout(
        f"{heading} - Agent Navigator",
        meta_desc,
        body,
        canonical=category_url if base_url else None,
        asset_prefix="../",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_comparison_page(
    comparison_key: str,
    title: str,
    description: str,
    left_option: str,
    right_option: str,
    left_agents: list[dict],
    right_agents: list[dict],
    *,
    base_url: Optional[str],
    comparison_content: str,
    faq_data: list[dict],
) -> str:
    """Render a pSEO comparison page between two frameworks/providers."""
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    comparison_url = f"{site_url}/compare/{comparison_key}/"

    left_count = len(left_agents)
    right_count = len(right_agents)

    meta_desc = f"{description} Compare examples, features, and use cases. {left_count} {left_option} examples vs {right_count} {right_option} examples."

    og_tags = _generate_open_graph_tags(
        title=f"{title} - Agent Navigator",
        description=meta_desc,
        url=comparison_url,
        image=f"{site_url}/assets/og-compare-{comparison_key}.png",
    )

    # Build breadcrumb schema
    breadcrumbs = [
        ("Home", "/"),
        ("Comparisons", "/compare/"),
        (title, f"/compare/{comparison_key}/"),
    ]
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if base_url else ""

    # FAQ Schema
    faq_schema_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_data,
    }
    combined_schema = json.dumps(faq_schema_obj, indent=2)
    if breadcrumb_schema:
        schema_list = [faq_schema_obj, json.loads(breadcrumb_schema)]
        combined_schema = json.dumps(schema_list, indent=2)

    # Build FAQ HTML
    faq_html = ""
    if faq_data:
        faq_items = ""
        for faq in faq_data:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f'''
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>'''
        faq_html = f'''
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>'''

    body = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/compare/">Comparisons</a></li>
    <li aria-current="page">{html.escape(title)}</li>
  </ol>
</nav>

<section class="hero">
  <h1>📊 {title}</h1>
  <p class="lead">{description}</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{left_count}</div><div class="stat-label">{html.escape(left_option)}</div></div>
    <div class="stat"><div class="stat-num">{right_count}</div><div class="stat-label">{html.escape(right_option)}</div></div>
  </div>
</section>

<section>
  <div class="comparison-content">
    {comparison_content}
  </div>
</section>

<section>
  <h2>{html.escape(left_option)} Examples</h2>
  <div class="grid">
    {"".join(f'''<a class="card" href="/agents/{html.escape(a["id"])}/">
  <div class="card-title">{html.escape(a["name"])}</div>
  <div class="card-desc">{html.escape((a.get("description") or "")[:120])}</div>
</a>''' for a in left_agents[:20])}
  </div>
</section>

<section>
  <h2>{html.escape(right_option)} Examples</h2>
  <div class="grid">
    {"".join(f'''<a class="card" href="/agents/{html.escape(a["id"])}/">
  <div class="card-title">{html.escape(a["name"])}</div>
  <div class="card-desc">{html.escape((a.get("description") or "")[:120])}</div>
</a>''' for a in right_agents[:20])}
  </div>
</section>

{faq_html}

<section class="about">
  <p><a class="muted" href="/compare/">&larr; Back to all comparisons</a> | <a class="muted" href="/">Back to home</a></p>
</section>
"""

    return _layout(
        title,
        meta_desc,
        body,
        canonical=comparison_url if base_url else None,
        asset_prefix="../../",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_tutorial_page(
    tutorial_key: str,
    title: str,
    description: str,
    agents: list[dict],
    *,
    base_url: Optional[str],
    tutorial_content: str,
    faq_data: list[dict],
    difficulty: str = "Intermediate",
) -> str:
    """Render a pSEO how-to/tutorial page."""
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    tutorial_url = f"{site_url}/how-to/{tutorial_key}/"

    count = len(agents)

    meta_desc = f"{description} Step-by-step guide with {count} working examples and code samples."

    og_tags = _generate_open_graph_tags(
        title=f"{title} - Agent Navigator",
        description=meta_desc,
        url=tutorial_url,
        image=f"{site_url}/assets/og-howto-{tutorial_key}.png",
    )

    # Build breadcrumb schema
    breadcrumbs = [
        ("Home", "/"),
        ("Tutorials", "/how-to/"),
        (title, f"/how-to/{tutorial_key}/"),
    ]
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if base_url else ""

    # FAQ Schema + HowTo Schema
    faq_schema_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_data,
    }

    # Add HowTo schema
    howto_schema = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": title,
        "description": description,
        "step": [
            {
                "@type": "HowToStep",
                "name": "Choose an example",
                "text": f"Browse {count} working examples below and select one matching your use case.",
            },
            {
                "@type": "HowToStep",
                "name": "Clone the repository",
                "text": "Use the clone command provided on each agent's page to get the code.",
            },
            {
                "@type": "HowToStep",
                "name": "Install dependencies",
                "text": "Run the pip install command to install required packages.",
            },
            {
                "@type": "HowToStep",
                "name": "Configure API keys",
                "text": "Set up your API keys (OpenAI, Anthropic, etc.) as environment variables.",
            },
            {
                "@type": "HowToStep",
                "name": "Run the agent",
                "text": "Execute the provided quick start command to run your agent.",
            },
        ],
    }

    schema_list = [faq_schema_obj, howto_schema]
    if breadcrumb_schema:
        schema_list.append(json.loads(breadcrumb_schema))
    combined_schema = json.dumps(schema_list, indent=2)

    # Build FAQ HTML
    faq_html = ""
    if faq_data:
        faq_items = ""
        for faq in faq_data:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f'''
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>'''
        faq_html = f'''
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>'''

    # Difficulty badge color
    difficulty_colors = {
        "Beginner": "#4ade80",
        "Intermediate": "#fbbf24",
        "Advanced": "#f87171",
    }
    diff_color = difficulty_colors.get(difficulty, "#fbbf24")

    body = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li><a href="/how-to/">Tutorials</a></li>
    <li aria-current="page">{html.escape(title)}</li>
  </ol>
</nav>

<section class="hero">
  <div style="margin-bottom: 1rem;">
    <span class="badge" style="background: {diff_color}; border-color: {diff_color}; font-size: 1rem; padding: 0.25rem 0.75rem;">{html.escape(difficulty)}</span>
  </div>
  <h1>📖 {title}</h1>
  <p class="lead">{description}</p>
  <div class="stats">
    <div class="stat"><div class="stat-num">{count}</div><div class="stat-label">examples</div></div>
  </div>
</section>

<div class="tutorial-content">
  {tutorial_content}
</div>

<section>
  <h2>Example Code</h2>
  <div class="grid">
    {"".join(f'''<a class="card" href="/agents/{html.escape(a["id"])}/">
  <div class="card-title">{html.escape(a["name"])}</div>
  <div class="card-desc">{html.escape((a.get("description") or "")[:120])}</div>
</a>''' for a in agents[:30])}
  </div>
</section>

{faq_html}

<section class="about">
  <p><a class="muted" href="/how-to/">&larr; Back to all tutorials</a> | <a class="muted" href="/">Back to home</a></p>
</section>
"""

    return _layout(
        title,
        meta_desc,
        body,
        canonical=tutorial_url if base_url else None,
        asset_prefix="../../",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_comparison_index(*, base_url: Optional[str]) -> str:
    """Render the comparison index page."""
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    index_url = f"{site_url}/compare/"

    meta_desc = "Compare AI agent frameworks, LLM providers, and tools. Side-by-side comparisons of LangChain vs LlamaIndex, CrewAI vs AutoGen, OpenAI vs Anthropic, and more."

    og_tags = _generate_open_graph_tags(
        title="Framework & Provider Comparisons - Agent Navigator",
        description=meta_desc,
        url=index_url,
        image=f"{site_url}/assets/og-compare.png",
    )

    comparisons = [
        ("LangChain vs LlamaIndex", "compare/langchain-vs-llamaindex/", "Compare two leading RAG and agent frameworks"),
        ("CrewAI vs AutoGen", "compare/crewai-vs-autogen/", "Multi-agent framework comparison"),
        ("OpenAI vs Anthropic", "compare/openai-vs-anthropic/", "Leading LLM API providers"),
        ("LangChain vs Raw API", "compare/langchain-vs-raw-api/", "Framework vs direct API calls"),
        ("Google vs OpenAI", "compare/google-vs-openai/", "Gemini vs GPT comparison"),
        ("Local vs Cloud LLMs", "compare/local-vs-cloud-llms/", "Privacy and cost comparison"),
    ]

    cards = "".join(f'''
<a class="card" href="{path}">
  <div class="card-title">📊 {title}</div>
  <div class="card-desc">{desc}</div>
</a>''' for title, path, desc in comparisons)

    body = f"""
<section class="hero">
  <h1>📊 Framework & Provider Comparisons</h1>
  <p class="lead">Compare AI agent frameworks, LLM providers, and tools to make the best choice for your project.</p>
</section>

<section>
  <h2>Available Comparisons</h2>
  <div class="grid">
    {cards}
  </div>
</section>

<section class="about">
  <h2>Why Compare?</h2>
  <p>Choosing the right framework or provider is crucial for your AI agent project. Our comparisons provide real-world examples, code samples, and insights from actual implementations to help you make informed decisions.</p>
</section>

<section class="about">
  <p><a class="muted" href="/">&larr; Back to all agents</a></p>
</section>
"""

    return _layout(
        "Framework & Provider Comparisons - Agent Navigator",
        meta_desc,
        body,
        canonical=index_url if base_url else None,
        asset_prefix="../",
        og_tags=og_tags,
    )


def _render_tutorial_index(*, base_url: Optional[str]) -> str:
    """Render the tutorials index page."""
    site_url = base_url.rstrip("/") if base_url else "https://agent-navigator.com"
    index_url = f"{site_url}/how-to/"

    meta_desc = "Step-by-step tutorials for building AI agents. Learn RAG chatbots, multi-agent systems, local LLM deployment, and more with working code examples."

    og_tags = _generate_open_graph_tags(
        title="AI Agent Tutorials - Agent Navigator",
        description=meta_desc,
        url=index_url,
        image=f"{site_url}/assets/og-howto.png",
    )

    tutorials = [
        ("Build RAG Chatbot", "how-to/build-rag-chatbot/", "Beginner", "Create a retrieval augmented generation chatbot with vector database"),
        ("Multi-Agent System", "how-to/multi-agent-system/", "Intermediate", "Build multi-agent systems with CrewAI and LangChain"),
        ("Local LLM with Ollama", "how-to/local-llm-ollama/", "Beginner", "Run LLM agents locally with Ollama for privacy"),
        ("OpenAI Function Calling", "how-to/openai-function-calling/", "Intermediate", "Implement function calling with OpenAI API"),
        ("LangChain Agents", "how-to/langchain-agents/", "Intermediate", "Build agents using LangChain framework"),
        ("Anthropic Claude Agents", "how-to/anthropic-claude-agents/", "Intermediate", "Create agents with Anthropic's Claude API"),
    ]

    cards = "".join(f'''
<a class="card" href="{path}">
  <div class="card-title">📖 {title}</div>
  <div class="card-desc">{desc}</div>
  <div class="card-badges"><span class="badge">{difficulty}</span></div>
</a>''' for title, path, difficulty, desc in tutorials)

    body = f"""
<section class="hero">
  <h1>📖 AI Agent Tutorials</h1>
  <p class="lead">Step-by-step guides for building AI agents with working code examples and best practices.</p>
</section>

<section>
  <h2>Available Tutorials</h2>
  <div class="grid">
    {cards}
  </div>
</section>

<section class="about">
  <h2>How These Tutorials Work</h2>
  <p>Each tutorial links to real, runnable agent examples. Browse the examples, clone the code, and follow the setup instructions. Every example includes complete documentation and quick start commands.</p>
</section>

<section class="about">
  <p><a class="muted" href="/">&larr; Back to all agents</a></p>
</section>
"""

    return _layout(
        "AI Agent Tutorials - Agent Navigator",
        meta_desc,
        body,
        canonical=index_url if base_url else None,
        asset_prefix="../",
        og_tags=og_tags,
    )


def _render_assets(out: Path) -> None:
    _write(
        out / "assets/style.css",
        """
:root { --bg: #0b1020; --card: #111a33; --text: #e7ebff; --muted: #aab1d6; --border: rgba(255,255,255,.08); --accent: #7c5cff; }
* { box-sizing: border-box; }
body { margin: 0; font: 16px/1.55 ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background: radial-gradient(1200px 800px at 20% 10%, rgba(124,92,255,.22), transparent 60%), var(--bg); color: var(--text); }
a { color: inherit; text-decoration: none; }
code { background: rgba(255,255,255,.06); padding: .1rem .25rem; border-radius: .3rem; }
pre { background: rgba(0,0,0,.25); padding: .75rem; border-radius: .75rem; border: 1px solid var(--border); overflow: auto; }
.wrap { max-width: 1100px; margin: 0 auto; padding: 1.25rem; }
.topbar { position: sticky; top: 0; backdrop-filter: blur(10px); background: rgba(11,16,32,.65); border-bottom: 1px solid var(--border); }
.topbar .wrap { display: flex; align-items: center; justify-content: space-between; }
.brand { font-weight: 750; letter-spacing: .2px; }
.nav a { margin-left: 1rem; color: var(--muted); }
.nav a:hover { color: var(--text); }
.hero { padding: 2rem 0 1rem; }
.lead { color: var(--muted); max-width: 70ch; }
.stats { display: flex; gap: 1rem; margin-top: 1rem; }
.stat { padding: .75rem 1rem; border: 1px solid var(--border); border-radius: 1rem; background: rgba(255,255,255,.03); }
.stat-num { font-size: 1.5rem; font-weight: 800; }
.stat-label { color: var(--muted); font-size: .9rem; }
.muted { color: var(--muted); }
.search { width: 100%; margin: .75rem 0 1rem; padding: .9rem 1rem; border-radius: 999px; border: 1px solid var(--border); background: rgba(255,255,255,.04); color: var(--text); outline: none; }
.chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
.chip { padding: .35rem .6rem; border-radius: 999px; border: 1px solid var(--border); color: var(--muted); background: rgba(255,255,255,.03); font-size: .9rem; }
.grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 1rem; }
.card { display: block; padding: 1rem; border-radius: 1rem; background: rgba(255,255,255,.03); border: 1px solid var(--border); }
.card:hover { border-color: rgba(124,92,255,.45); transform: translateY(-1px); transition: .12s ease; }
.card-title { font-weight: 750; margin-bottom: .35rem; }
.card-desc { color: var(--muted); font-size: .95rem; min-height: 2.8em; }
.card-badges { margin-top: .7rem; display: flex; flex-wrap: wrap; gap: .35rem; }
.badge { padding: .18rem .45rem; border-radius: 999px; background: rgba(124,92,255,.14); border: 1px solid rgba(124,92,255,.25); color: var(--text); font-size: .85rem; }
.row { margin: 1rem 0; display: flex; gap: .5rem; flex-wrap: wrap; }
.btn { display: inline-block; padding: .5rem .75rem; border-radius: .75rem; border: 1px solid var(--border); background: rgba(255,255,255,.04); }
.btn:hover { border-color: rgba(124,92,255,.45); }
.grid2 { display: grid; grid-template-columns: 1.35fr 1fr; gap: 1rem; margin-top: 1rem; }
.panel { padding: 1rem; border-radius: 1rem; border: 1px solid var(--border); background: rgba(255,255,255,.03); }
.about { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); }
.faq-container { margin-top: 1rem; }
.faq-container details { margin-bottom: 1rem; padding: 1rem; border: 1px solid var(--border); border-radius: 0.75rem; background: rgba(255,255,255,.02); }
.faq-container summary { font-weight: 600; cursor: pointer; }
.faq-container details p { margin: 0.75rem 0 0 0; }
.breadcrumb { margin-bottom: 1rem; }
.breadcrumb ol { display: flex; flex-wrap: wrap; list-style: none; margin: 0; padding: 0; gap: 0.5rem; }
.breadcrumb li { display: flex; align-items: center; color: var(--muted); font-size: 0.9rem; }
.breadcrumb li:not(:last-child)::after { content: "›"; margin-left: 0.5rem; color: var(--muted); }
.breadcrumb a { color: var(--muted); }
.breadcrumb a:hover { color: var(--text); }
.breadcrumb li[aria-current] { color: var(--text); font-weight: 600; }
.related-section { margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid var(--border); }
.related-section h3 { margin-bottom: 1rem; }
.related-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.related-card { padding: 0.75rem; }
.related-card .card-desc { font-size: 0.85rem; min-height: auto; }
.category-link { color: var(--accent); text-decoration: none; }
.category-link:hover { text-decoration: underline; }
@media (max-width: 900px) { .grid { grid-template-columns: 1fr; } .grid2 { grid-template-columns: 1fr; } .related-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px) { .related-grid { grid-template-columns: 1fr; } }
""".strip()
        + "\n",
    )
    _write(
        out / "assets/app.js",
        """
(function () {
  const q = document.getElementById("q");
  const cards = Array.from(document.querySelectorAll(".card"));
  if (!q || !cards.length) return;
  function apply() {
    const needle = (q.value || "").trim().toLowerCase();
    for (const c of cards) {
      const hay = (c.dataset.name || "") + " " + (c.dataset.desc || "") + " " + (c.dataset.cat || "");
      c.style.display = needle && !hay.includes(needle) ? "none" : "";
    }
  }
  q.addEventListener("input", apply);
})();
""".strip()
        + "\n",
    )


def _render_404(base_url: Optional[str]) -> str:
    """Render a simple 404 page for static hosting (e.g., Cloudflare Pages)."""
    body = """
<section class="hero">
  <h1>Page not found</h1>
  <p class="lead">That URL doesn’t exist. Try browsing or searching the directory.</p>
  <div style="margin-top: 1rem; display: flex; gap: 0.75rem; flex-wrap: wrap;">
    <a class="btn" href="/">Go home</a>
    <a class="btn secondary" href="/#browse">Browse agents</a>
  </div>
</section>
<section class="section">
  <h2>Search</h2>
  <p class="muted">Use the homepage search box to quickly find an agent by name, category, framework, or provider.</p>
</section>
""".strip()
    canonical = f"{base_url.rstrip('/')}/404.html" if base_url else None
    return _layout(
        title="404 — Agent Navigator",
        description="Page not found.",
        body=body,
        canonical=canonical,
    )


def _render_headers() -> str:
    """
    Generate a Cloudflare Pages-compatible `_headers` file.

    This keeps headers conservative to avoid breaking static rendering while still improving security and caching.
    """
    return """
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*
  Cache-Control: public, max-age=600
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: interest-cohort=()
""".lstrip()


def _render_sitemap(out: Path, agents: list[dict], categories: list[tuple[str, str, list[dict]]] = None, base_url: str = None, additional_urls: list[str] = None) -> None:
    if categories is None:
        categories = []
    if additional_urls is None:
        additional_urls = []
    base_url = base_url.rstrip("/")
    urls = [
        f"{base_url}/",
        *[f"{base_url}/agents/{a['id']}/" for a in agents],
        *[f"{base_url}/{key}/" for key, _, _ in categories],
        *additional_urls,
    ]
    now = datetime.now().strftime("%Y-%m-%d")
    items = "\n".join(
        f"<url><loc>{html.escape(u)}</loc><lastmod>{now}</lastmod></url>"
        for u in urls
    )
    _write(out / "sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n')
    _write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")


def export_site(data_path: Path, output_dir: Path, *, base_url: Optional[str]) -> None:
    """Export complete static site with all pSEO pages.

    Generates:
    - Homepage with agent listing
    - Individual agent pages
    - Category landing pages (RAG, OpenAI, Multi-Agent, Local)
    - Framework-specific pages (LangChain, CrewAI, etc.)
    - Provider-specific pages (OpenAI, Anthropic, etc.)
    - Complexity-based pages (Beginner, Intermediate, Advanced)
    - Comparison pages (LangChain vs X, etc.)
    - Tutorial/How-To pages
    - Index pages for comparisons and tutorials
    - Sitemap with all URLs
    """
    # Delegate to the maintained implementation in `src.export`.
    from src.export.export import export_site as export_site_new

    export_site_new(data_path, output_dir, base_url=base_url)
    return

    agents = [_normalize_record(a) for a in _read_json(data_path)]
    agents.sort(key=lambda a: ((a.get("name") or "").lower()))

    site_url = (base_url or "https://agent-navigator.com").rstrip("/")

    _render_assets(output_dir)
    _write(output_dir / "404.html", _render_404(base_url))
    _write(output_dir / "_headers", _render_headers())
    _write(output_dir / "index.html", _render_index(agents, base_url))

    # Generate individual agent pages
    for a in agents:
        agent_slug = _slug(a["id"])
        agent_dir = output_dir / "agents" / agent_slug
        _write(agent_dir / "index.html", _render_agent(a, base_url, all_agents=agents))

    # Track all additional URLs for sitemap
    additional_sitemap_urls = []

    # Generate pSEO category landing pages (original 4)
    categories = [
        (
            "rag-tutorials",
            "RAG Tutorials",
            lambda a: a.get("category") == "rag",
            "RAG Tutorials & Examples",
            "Build Retrieval Augmented Generation systems with vector databases, document loaders, and LLM query engines.",
        ),
        (
            "openai-agents",
            "OpenAI Agents",
            lambda a: "openai" in a.get("llm_providers", []),
            "OpenAI Agents & GPT Examples",
            "LLM agents powered by OpenAI GPT-4, GPT-3.5, Assistants API, function calling, and more.",
        ),
        (
            "multi-agent-systems",
            "Multi-Agent Systems",
            lambda a: a.get("category") == "multi_agent",
            "Multi-Agent Systems & Orchestration",
            "Multi-agent architectures with CrewAI, LangChain agents, and custom orchestrators for complex task automation.",
        ),
        (
            "local-llm-agents",
            "Local LLM Agents",
            lambda a: a.get("supports_local_models", False) or "ollama" in a.get("llm_providers", []) or "local" in a.get("llm_providers", []),
            "Local LLM Agents & Privacy-First Examples",
            "Run LLM agents locally with Ollama, Llama, Mistral, and other open-source models for privacy and cost savings.",
        ),
    ]

    for cat_key, cat_name, filter_fn, heading, description in categories:
        cat_agents = [a for a in agents if filter_fn(a)]
        cat_dir = output_dir / cat_key
        _write(
            cat_dir / "index.html",
            _render_category_landing(cat_key, cat_name, cat_agents, base_url=base_url, description=description, heading=heading),
        )
        additional_sitemap_urls.append(f"{site_url}/{cat_key}/")

    # Framework-specific pages
    framework_pages = [
        (
            "langchain-agents",
            "LangChain Agents",
            lambda a: "langchain" in a.get("frameworks", []),
            "LangChain Agents & Examples",
            "Build AI agents using LangChain framework. Includes agents, chains, tools, and RAG implementations with LangChain.",
            """<section class="about">
<h2>Why Use LangChain?</h2>
<p>LangChain is the most popular framework for building LLM applications. It provides abstractions for agents, chains, tools, memory, and RAG pipelines. With LangChain, you can quickly prototype and productionize AI agents.</p>
<h2>Getting Started with LangChain</h2>
<p>Install with <code>pip install langchain</code>. Browse examples below to see different agent patterns like ReAct agents, OpenAI functions, custom tools, and multi-agent collaboration.</p>
</section>""",
        ),
        (
            "crewai-agents",
            "CrewAI Agents",
            lambda a: "crewai" in a.get("frameworks", []),
            "CrewAI Multi-Agent Examples",
            "Build multi-agent systems using CrewAI framework. Role-based agents with delegation and collaboration patterns.",
            """<section class="about">
<h2>Why Use CrewAI?</h2>
<p>CrewAI specializes in multi-agent systems where each agent has a specific role. Agents can delegate tasks to each other, collaborate on complex problems, and use tools autonomously. Perfect for automation workflows.</p>
<h2>CrewAI Concepts</h2>
<p>Agents have roles, goals, and backstories. They can use tools and delegate to other agents. Browse examples to see practical implementations.</p>
</section>""",
        ),
        (
            "phidata-agents",
            "PhiData Agents",
            lambda a: "phidata" in a.get("frameworks", []),
            "PhiData Agent Examples",
            "Build production-ready agents with PhiData framework. Includes monitoring, evaluation, and deployment tools.",
            """<section class="about">
<h2>Why Use PhiData?</h2>
<p>PhiData focuses on production-ready agents with built-in monitoring, evaluation, and deployment capabilities. It's designed for teams building serious AI applications.</p>
</section>""",
        ),
        (
            "raw-api-agents",
            "Raw API Agents",
            lambda a: "raw_api" in a.get("frameworks", []),
            "Direct API Agent Examples",
            "Build AI agents using direct API calls to OpenAI, Anthropic, Google, and other providers without framework overhead.",
            """<section class="about">
<h2>Why Use Raw APIs?</h2>
<p>Direct API calls give you maximum control and zero dependencies. Great for learning how LLM APIs work, building lightweight agents, or when you don't need framework features.</p>
<h2>Getting Started</h2>
<p>All you need is an API key. Examples show chat completion, function calling, streaming, and more using official SDKs.</p>
</section>""",
        ),
    ]

    for fw_key, fw_name, filter_fn, heading, description, intro_content in framework_pages:
        fw_agents = [a for a in agents if filter_fn(a)]
        if fw_agents:  # Only generate if there are agents
            fw_dir = output_dir / fw_key
            _write(
                fw_dir / "index.html",
                _render_category_landing(
                    fw_key,
                    fw_name,
                    fw_agents,
                    base_url=base_url,
                    description=description,
                    heading=heading,
                    intro_content=intro_content,
                    related_links=[("Frameworks", "/compare/"), ("Tutorials", "/how-to/")],
                ),
            )
            additional_sitemap_urls.append(f"{site_url}/{fw_key}/")

    # Provider-specific pages
    provider_pages = [
        (
            "anthropic-agents",
            "Anthropic Claude Agents",
            lambda a: "anthropic" in a.get("llm_providers", []),
            "Anthropic Claude Agents & Examples",
            "Build AI agents using Anthropic's Claude API. Includes Claude 3.5 Haiku, Sonnet, and Opus examples with function calling.",
            """<section class="about">
<h2>Why Use Anthropic Claude?</h2>
<p>Claude is known for strong reasoning, long context windows (200K tokens), and careful outputs. Great for complex tasks requiring analysis or generation of long content.</p>
<h2>Getting Started</h2>
<p>Get an API key from console.anthropic.com. Install with <code>pip install anthropic</code>.</p>
</section>""",
        ),
        (
            "google-agents",
            "Google Gemini Agents",
            lambda a: "google" in a.get("llm_providers", []),
            "Google Gemini Agents & Examples",
            "Build AI agents using Google's Gemini API. Includes Gemini Pro, Flash, and specialized models.",
            """<section class="about">
<h2>Why Use Google Gemini?</h2>
<p>Gemini offers strong multimodal capabilities, competitive pricing, and Google's infrastructure. Excellent for vision tasks and Google Workspace integration.</p>
<h2>Getting Started</h2>
<p>Get an API key from AI Studio. Install with <code>pip install google-generativeai</code>.</p>
</section>""",
        ),
        (
            "cohere-agents",
            "Cohere Agents",
            lambda a: "cohere" in a.get("llm_providers", []),
            "Cohere Command & Embed Agents",
            "Build AI agents using Cohere's Command and Embed models. Strong for RAG and enterprise use cases.",
            """<section class="about">
<h2>Why Use Cohere?</h2>
<p>Cohere focuses on enterprise use cases with strong embedding models and RAG capabilities. Their API is designed for production applications.</p>
</section>""",
        ),
        (
            "huggingface-agents",
            "HuggingFace Agents",
            lambda a: "huggingface" in a.get("llm_providers", []),
            "HuggingFace Inference API Agents",
            "Build agents using HuggingFace's inference API and open-source models.",
            """<section class="about">
<h2>Why Use HuggingFace?</h2>
<p>Access thousands of open-source models through one API. Great for specialized models, cost optimization, and privacy requirements.</p>
</section>""",
        ),
    ]

    for prov_key, prov_name, filter_fn, heading, description, intro_content in provider_pages:
        prov_agents = [a for a in agents if filter_fn(a)]
        if prov_agents:
            prov_dir = output_dir / prov_key
            _write(
                prov_dir / "index.html",
                _render_category_landing(
                    prov_key,
                    prov_name,
                    prov_agents,
                    base_url=base_url,
                    description=description,
                    heading=heading,
                    intro_content=intro_content,
                    related_links=[("Compare Providers", "/compare/"), ("Tutorials", "/how-to/")],
                ),
            )
            additional_sitemap_urls.append(f"{site_url}/{prov_key}/")

    # Complexity-based pages
    complexity_pages = [
        (
            "beginner-projects",
            "Beginner Projects",
            lambda a: a.get("complexity") == "beginner",
            "Beginner AI Agent Projects",
            "Start your AI agent journey with beginner-friendly projects. Perfect for learning LLM agent fundamentals.",
            "Beginner",
        ),
        (
            "intermediate-projects",
            "Intermediate Projects",
            lambda a: a.get("complexity") == "intermediate",
            "Intermediate AI Agent Projects",
            "Expand your skills with intermediate agent projects. RAG, tool use, and multi-agent patterns.",
            "Intermediate",
        ),
        (
            "advanced-projects",
            "Advanced Projects",
            lambda a: a.get("complexity") == "advanced",
            "Advanced AI Agent Projects",
            "Master advanced agent architectures. Complex multi-agent systems, production deployments, and cutting-edge patterns.",
            "Advanced",
        ),
    ]

    for comp_key, comp_name, filter_fn, heading, description, difficulty in complexity_pages:
        comp_agents = [a for a in agents if filter_fn(a)]
        if comp_agents:
            comp_dir = output_dir / comp_key
            _write(
                comp_dir / "index.html",
                _render_category_landing(
                    comp_key,
                    comp_name,
                    comp_agents,
                    base_url=base_url,
                    description=description,
                    heading=heading,
                    intro_content=f"""<section class="about">
<h2>Learning Path</h2>
<p>These {difficulty.lower()} projects help you build practical skills. Each example includes complete code and setup instructions. Start with projects matching your interests and gradually increase complexity.</p>
<h2>Prerequisites</h2>
<p>Python knowledge, basic API understanding, and familiarity with command-line tools. Each project lists specific requirements.</p>
</section>""",
                    related_links=[("All Tutorials", "/how-to/")],
                ),
            )
            additional_sitemap_urls.append(f"{site_url}/{comp_key}/")

    # Comparison pages
    _write(output_dir / "compare" / "index.html", _render_comparison_index(base_url=base_url))
    additional_sitemap_urls.append(f"{site_url}/compare/")

    # Define comparison page configurations
    comparison_configs = [
        {
            "key": "langchain-vs-llamaindex",
            "title": "LangChain vs LlamaIndex",
            "description": "Compare LangChain and LlamaIndex for building AI agents. Learn about their strengths, use cases, and code examples.",
            "left": "LangChain",
            "right": "LlamaIndex",
            "left_filter": lambda a: "langchain" in a.get("frameworks", []),
            "right_filter": lambda a: "llamaindex" in a.get("frameworks", []),
            "content": """<section class="about">
<h2>LangChain Overview</h2>
<p>LangChain is a general-purpose framework for building LLM applications. It excels at agent orchestration, chain composition, and tool use. Ideal for complex multi-step reasoning and agent workflows.</p>
<h2>LlamaIndex Overview</h2>
<p>LlamaIndex (formerly GPT Index) specializes in RAG and data indexing. It provides excellent connectors to data sources and advanced retrieval strategies. Best for knowledge-intensive applications.</p>
<h2>When to Choose</h2>
<p>Choose LangChain for general agent development and complex workflows. Choose LlamaIndex when your primary need is RAG and connecting LLMs to your data. Many projects use both together.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Can I use LangChain and LlamaIndex together?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes! They work well together. Use LlamaIndex for data ingestion and retrieval, then pass results to LangChain agents for reasoning and action.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "Which has better performance?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Both are actively optimized. LangChain has more abstraction overhead while LlamaIndex is lighter for pure RAG. Choose based on your use case, not perceived performance.",
                    },
                },
            ],
        },
        {
            "key": "crewai-vs-autogen",
            "title": "CrewAI vs AutoGen",
            "description": "Compare CrewAI and AutoGen for multi-agent systems. Understand their approaches to agent collaboration and orchestration.",
            "left": "CrewAI",
            "right": "AutoGen",
            "left_filter": lambda a: "crewai" in a.get("frameworks", []),
            "right_filter": lambda a: "autogen" in a.get("frameworks", []),
            "content": """<section class="about">
<h2>CrewAI Overview</h2>
<p>CrewAI focuses on role-based multi-agent systems. Define agents with specific roles, goals, and backstories. Agents can delegate tasks and collaborate naturally. Great for business process automation.</p>
<h2>AutoGen Overview</h2>
<p>Microsoft's AutoGen enables multi-agent conversations through a simple interface. Agents communicate to solve tasks, with human-in-the-loop options. Excellent for research and complex problem-solving.</p>
<h2>Key Differences</h2>
<p>CrewAI emphasizes production-ready role definition. AutoGen focuses on conversational dynamics. Both support tool use and delegation, but with different mental models.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Which is easier for beginners?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "CrewAI's role-based approach is more intuitive for many. AutoGen's conversation model is powerful but may require more experimentation to master.",
                    },
                },
            ],
        },
        {
            "key": "openai-vs-anthropic",
            "title": "OpenAI vs Anthropic",
            "description": "Compare OpenAI GPT and Anthropic Claude for AI agents. Pricing, capabilities, and best use cases.",
            "left": "OpenAI",
            "right": "Anthropic",
            "left_filter": lambda a: "openai" in a.get("llm_providers", []),
            "right_filter": lambda a: "anthropic" in a.get("llm_providers", []),
            "content": """<section class="about">
<h2>OpenAI GPT Overview</h2>
<p>OpenAI offers GPT-4, GPT-4o, and GPT-3.5 with excellent function calling, vision capabilities, and the Assistants API. Largest ecosystem and tool support.</p>
<h2>Anthropic Claude Overview</h2>
<p>Claude 3.5 Haiku, Sonnet, and Opus offer strong reasoning, 200K context windows, and careful outputs. Known for reduced hallucination and excellent for analysis tasks.</p>
<h2>Pricing Comparison</h2>
<p>OpenAI GPT-3.5 is most cost-effective for simple tasks. Claude 3.5 Haiku offers great value. GPT-4o and Claude Opus are premium for complex reasoning.</p>
<h2>Decision Factors</h2>
<p>Choose OpenAI for ecosystem, vision, and Assistants API. Choose Claude for long context, careful outputs, and complex reasoning tasks.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Which has better function calling?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Both have excellent function calling. OpenAI's implementation is more mature with broader tool support. Claude 3.5 has competitive function calling with often better reliability.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "How do context windows compare?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Claude offers 200K tokens context. GPT-4 Turbo offers 128K tokens. Both support large document analysis. Claude's larger window can be advantageous for extensive document processing.",
                    },
                },
            ],
        },
        {
            "key": "langchain-vs-raw-api",
            "title": "LangChain vs Raw API",
            "description": "Compare using LangChain framework vs direct API calls for AI agents. When to use each approach.",
            "left": "LangChain",
            "right": "Raw API",
            "left_filter": lambda a: "langchain" in a.get("frameworks", []),
            "right_filter": lambda a: "raw_api" in a.get("frameworks", []),
            "content": """<section class="about">
<h2>LangChain Framework Approach</h2>
<p>LangChain provides abstractions for agents, chains, tools, memory, and RAG. Great for rapid development, standardizing patterns, and leveraging community components. Adds dependency overhead.</p>
<h2>Raw API Approach</h2>
<p>Direct API calls to OpenAI, Anthropic, or Google give maximum control with zero dependencies. Best for simple agents, learning, and when framework features aren't needed.</p>
<h2>When to Use Each</h2>
<p>Use raw APIs for simple chatbots, one-off tasks, and learning fundamentals. Use LangChain for complex workflows, RAG systems, multi-agent setups, and when you need built-in integrations.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Is LangChain too heavy for simple projects?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "For very simple projects, raw APIs may be sufficient. But LangChain's value becomes clear as complexity grows. Start with raw APIs to learn, then adopt LangChain as needs evolve.",
                    },
                },
            ],
        },
        {
            "key": "google-vs-openai",
            "title": "Google vs OpenAI",
            "description": "Compare Google Gemini and OpenAI GPT models. Features, pricing, and capabilities comparison.",
            "left": "Google Gemini",
            "right": "OpenAI",
            "left_filter": lambda a: "google" in a.get("llm_providers", []),
            "right_filter": lambda a: "openai" in a.get("llm_providers", []),
            "content": """<section class="about">
<h2>Google Gemini Overview</h2>
<p>Gemini Pro and Flash models offer strong multimodal capabilities, competitive pricing, and Google Cloud integration. Excellent for vision tasks and Google Workspace users.</p>
<h2>OpenAI GPT Overview</h2>
<p>GPT-4, GPT-4o, and GPT-3.5 lead in capabilities and ecosystem. Best-in-class function calling, Assistants API, and broadest tool support.</p>
<h2>Decision Factors</h2>
<p>Choose Google for cost-sensitive projects, vision-heavy applications, or Google Cloud integration. Choose OpenAI for cutting-edge capabilities, ecosystem, and when you need the best performance.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Which is more cost-effective?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Gemini Flash is very cost-effective for high-volume tasks. GPT-3.5 is also very affordable. Compare latest pricing as it changes frequently - both offer competitive tiers.",
                    },
                },
            ],
        },
        {
            "key": "local-vs-cloud-llms",
            "title": "Local vs Cloud LLMs",
            "description": "Compare running LLMs locally vs using cloud APIs. Privacy, cost, and performance considerations.",
            "left": "Local LLMs",
            "right": "Cloud LLMs",
            "left_filter": lambda a: a.get("supports_local_models", False) or "ollama" in a.get("llm_providers", []) or "local" in a.get("llm_providers", []),
            "right_filter": lambda a: any(p in ["openai", "anthropic", "google", "cohere"] for p in a.get("llm_providers", [])),
            "content": """<section class="about">
<h2>Local LLMs (Ollama, Llama, Mistral)</h2>
<p>Run models on your hardware for complete privacy, no API costs, and offline capability. Requires GPU for good performance. Models like Llama 3, Mistral, and Phi-3 are surprisingly capable.</p>
<h2>Cloud LLMs (OpenAI, Anthropic, Google)</h2>
<p>Best-in-class models, instant scaling, zero infrastructure. Pay per usage with predictable costs. GPT-4 and Claude Opus still outperform most open models.</p>
<h2>Decision Framework</h2>
<p>Use local for: sensitive data, cost control, offline needs, and privacy requirements. Use cloud for: best quality, speed of development, and when model quality matters more than cost.</p>
<h2>Hybrid Approach</h2>
<p>Many production systems use both: local models for simple tasks and sensitive data, cloud models for complex reasoning. This optimizes both cost and quality.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "What hardware do I need for local LLMs?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "For 7B models: 8GB GPU VRAM is comfortable. For 13B+: 16GB+ recommended. CPU-only is possible but slow. Quantized models (4-bit) reduce requirements significantly. Ollama makes setup easy.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "Are local models good enough for production?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "It depends on your use case. Llama 3 8B and Mistral 7B are excellent for many tasks. For complex reasoning, GPT-4/Claude Opus still lead. Hybrid architectures often work best.",
                    },
                },
            ],
        },
    ]

    for config in comparison_configs:
        left_agents = [a for a in agents if config["left_filter"](a)]
        right_agents = [a for a in agents if config["right_filter"](a)]
        if left_agents or right_agents:  # Generate even if one side is empty
            compare_dir = output_dir / "compare" / config["key"]
            _write(
                compare_dir / "index.html",
                _render_comparison_page(
                    config["key"],
                    config["title"],
                    config["description"],
                    config["left"],
                    config["right"],
                    left_agents[:20],
                    right_agents[:20],
                    base_url=base_url,
                    comparison_content=config["content"],
                    faq_data=config["faqs"],
                ),
            )
            additional_sitemap_urls.append(f"{site_url}/compare/{config['key']}/")

    # Tutorial/How-To pages
    _write(output_dir / "how-to" / "index.html", _render_tutorial_index(base_url=base_url))
    additional_sitemap_urls.append(f"{site_url}/how-to/")

    tutorial_configs = [
        {
            "key": "build-rag-chatbot",
            "title": "How to Build a RAG Chatbot",
            "description": "Learn how to build a Retrieval Augmented Generation (RAG) chatbot from scratch. Complete guide with vector databases, document processing, and LLM integration.",
            "filter": lambda a: a.get("category") == "rag" or ("rag" in a.get("tags", [])),
            "difficulty": "Beginner",
            "content": """<section class="about">
<h2>What is RAG?</h2>
<p>Retrieval Augmented Generation (RAG) combines LLMs with external knowledge retrieval. Instead of relying only on training data, RAG systems fetch relevant documents and include them in the prompt for accurate, up-to-date responses.</p>
<h2>RAG Components</h2>
<p><strong>Document Loading:</strong> Load from PDFs, web pages, databases<br>
<strong>Splitting:</strong> Break documents into chunks<br>
<strong>Embedding:</strong> Convert chunks to vectors<br>
<strong>Storage:</strong> Store in vector database (Pinecone, Chroma, Weaviate)<br>
<strong>Retrieval:</strong> Find relevant chunks for each query<br>
<strong>Generation:</strong> Pass chunks to LLM with the question</p>
<h2>Quick Start</h2>
<p>1. Choose a vector database (Chroma is easiest for local)<br>
2. Install LangChain or LlamaIndex<br>
3. Load and process your documents<br>
4. Create embeddings and store<br>
5. Build retrieval chain<br>
6. Add chat interface</p>
<h2>Best Practices</h2>
<p>Use semantic search, implement hybrid search with keywords, add citation sources, and monitor retrieval quality. Examples below demonstrate different approaches.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "What vector database should I use?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "For learning: Chroma (local, free). For production: Pinecone (managed), Weaviate (self-hosted), or pgvector (PostgreSQL extension). Choose based on your scaling needs and infrastructure preferences.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "How do I improve RAG accuracy?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Improve chunking strategy, use hybrid search (semantic + keyword), add reranking, implement query expansion, and fine-tune your prompts. Also ensure high-quality source documents.",
                    },
                },
            ],
        },
        {
            "key": "multi-agent-system",
            "title": "How to Build Multi-Agent Systems",
            "description": "Learn to build multi-agent systems where AI agents collaborate. Complete guide with CrewAI, LangChain agents, and custom orchestration patterns.",
            "filter": lambda a: a.get("category") == "multi_agent" or "multi_agent" in a.get("tags", []),
            "difficulty": "Intermediate",
            "content": """<section class="about">
<h2>What are Multi-Agent Systems?</h2>
<p>Multi-agent systems use multiple specialized AI agents working together. Each agent has specific capabilities and can delegate tasks to others. This mirrors how human teams collaborate.</p>
<h2>Common Patterns</h2>
<p><strong>Role-Based:</strong> Each agent has a role (researcher, writer, reviewer)<br>
<strong>Sequential:</strong> Agents pass work in a pipeline<br>
<strong>Hierarchical:</strong> Manager agent delegates to workers<br>
<strong>Debate:</strong> Agents discuss and reach consensus<br>
<strong>Competitive:</strong> Agents compete to find best solution</p>
<h2>Frameworks</h2>
<p>CrewAI: Easiest for role-based systems with clear delegation<br>
LangChain Agents: Flexible with extensive tool ecosystem<br>
AutoGen: Microsoft's conversation-based approach<br>
Custom: Build your own orchestration layer</p>
<h2>Getting Started</h2>
<p>Start with a simple two-agent system: one for research, one for synthesis. Gradually add more agents and complexity. Examples below demonstrate various patterns.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "When should I use multiple agents?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Use multi-agent systems for complex tasks requiring different skills, when you want clear separation of concerns, or for tasks that benefit from parallel processing. Single agents are better for simple, focused tasks.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "How do agents communicate?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Agents communicate through structured messages, shared context, or a central orchestrator. Frameworks provide different approaches - CrewAI uses hierarchical delegation, AutoGen uses conversations, LangChain uses agent chains.",
                    },
                },
            ],
        },
        {
            "key": "local-llm-ollama",
            "title": "How to Run Local LLMs with Ollama",
            "description": "Learn to run LLM agents locally using Ollama. Complete guide for privacy, cost savings, and offline capability.",
            "filter": lambda a: "ollama" in a.get("llm_providers", []) or a.get("supports_local_models", False),
            "difficulty": "Beginner",
            "content": """<section class="about">
<h2>Why Run LLMs Locally?</h2>
<p><strong>Privacy:</strong> Data never leaves your machine<br>
<strong>Cost:</strong> No API fees after initial hardware<br>
<strong>Offline:</strong> Works without internet<br>
<strong>Customization:</strong> Use any open-source model</p>
<h2>What is Ollama?</h2>
<p>Ollama is the easiest way to run LLMs locally. It manages models, provides an API compatible with OpenAI's format, and works on Mac, Linux, and Windows. Models like Llama 3, Mistral, and Phi-3 are available.</p>
<h2>Quick Start</h2>
<p>1. Download Ollama from ollama.ai<br>
2. Run <code>ollama pull llama3</code> (or any model)<br>
3. Run <code>ollama run llama3</code> to chat<br>
4. Use the API at localhost:11434</p>
<h2>Available Models</h2>
<p>Llama 3 (8B, 70B): Meta's excellent general models<br>
Mistral (7B): Strong performance, efficient<br>
Phi-3 (3.8B): Microsoft's small but capable model<br>
Gemma (2B, 7B): Google's lightweight models</p>
<h2>Hardware Requirements</h2>
<p>For 7B models: 8GB VRAM recommended (can work on CPU)<br>
For larger models: 16GB+ VRAM<br>
Quantized models (4-bit) reduce requirements by ~50%</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Can I use Ollama with LangChain?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes! Ollama provides an OpenAI-compatible API. You can use LangChain's ChatOpenAI class with base_url='http://localhost:11434'. Most frameworks that support OpenAI work with Ollama.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "How do local models compare to GPT-4?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "GPT-4 and Claude Opus still outperform local models on complex reasoning. However, Llama 3 8B and Mistral 7B are surprisingly capable for many tasks. Use local for cost/privacy, cloud for quality.",
                    },
                },
            ],
        },
        {
            "key": "openai-function-calling",
            "title": "How to Use OpenAI Function Calling",
            "description": "Learn to implement function calling with OpenAI's API. Build agents that can use tools and take actions.",
            "filter": lambda a: "openai" in a.get("llm_providers", []) and ("tool" in a.get("design_pattern", "") or "function" in str(a.get("tags", [])).lower()),
            "difficulty": "Intermediate",
            "content": """<section class="about">
<h2>What is Function Calling?</h2>
<p>Function calling lets LLMs request to run specific functions with structured arguments. The model doesn't execute code directly - it outputs what function to call and with what parameters. Your code executes the function and returns results.</p>
<h2>Use Cases</h2>
<p><strong>Query Databases:</strong> Convert natural language to SQL<br>
<strong>API Calls:</strong> Make external API requests<br>
<strong>Calculations:</strong> Perform accurate math<br>
<strong>Actions:</strong> Send emails, create calendar events<br>
<strong>Data Retrieval:</strong> Fetch specific information</p>
<h2>Basic Pattern</h2>
<p>1. Define functions with schemas (name, description, parameters)<br>
2. Pass functions to ChatCompletion API<br>
3. Check if model wants to call a function<br>
4. Execute the function with provided arguments<br>
5. Return results to model for final response</p>
<h2>Best Practices</h2>
<p>Provide clear function descriptions, use TypeScript-style schema for parameters, handle errors gracefully, and validate arguments before execution.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "Is function calling different from tool use?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Function calling is OpenAI's term for tool use. Other providers call it tool use (Anthropic), function calling (Google), or tools (Claude). They all follow similar patterns: define tools, let LLM choose, execute, return results.",
                    },
                },
            ],
        },
        {
            "key": "langchain-agents",
            "title": "How to Build Agents with LangChain",
            "description": "Learn to build AI agents using LangChain framework. Complete guide with ReAct agents, tools, and chains.",
            "filter": lambda a: "langchain" in a.get("frameworks", []),
            "difficulty": "Intermediate",
            "content": """<section class="about">
<h2>LangChain Agents</h2>
<p>LangChain agents use LLMs to determine actions, observe results, and iterate until completion. Unlike predefined chains, agents dynamically decide what to do based on the current state.</p>
<h2>Agent Types</h2>
<p><strong>ReAct:</strong> Reasoning + Acting, most common pattern<br>
<strong>OpenAI Functions:</strong> Uses GPT's function calling<br>
<strong>Structured Chat:</strong> For multi-input tools<br>
<strong>Self-Ask with Search:</strong> For complex queries needing research</p>
<h2>Key Components</h2>
<p><strong>Tools:</strong> Functions agents can call (search, calculator, database)<br>
<strong>Toolkits:</strong> Collections of related tools<br>
<strong>Agent Executor:</strong> Runtime that manages agent loops<br>
<strong>Memory:</strong> Maintains conversation context<br>
<strong>Prompt Templates:</strong> Guide agent behavior</p>
<h2>Getting Started</h2>
<p>Install with <code>pip install langchain langchain-openai</code>. Define tools, initialize agent with prompt, and run with executor. Examples below show various patterns.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "What's the difference between chains and agents?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Chains have predefined steps in a fixed sequence. Agents dynamically decide actions based on each step's outcome. Chains are predictable and faster. Agents are flexible and can handle complex, multi-step problems.",
                    },
                },
            ],
        },
        {
            "key": "anthropic-claude-agents",
            "title": "How to Build Agents with Anthropic Claude",
            "description": "Learn to build AI agents using Anthropic's Claude API. Tool use, long context, and reliable outputs.",
            "filter": lambda a: "anthropic" in a.get("llm_providers", []),
            "difficulty": "Intermediate",
            "content": """<section class="about">
<h2>Why Build Agents with Claude?</h2>
<p>Claude 3.5 models offer excellent reasoning, 200K token context windows, and strong tool use capabilities. Claude is known for careful, reliable outputs which is crucial for agent systems.</p>
<h2>Claude Tool Use</h2>
<p>Anthropic's tool use (function calling) is highly reliable. Claude excels at understanding when to use tools, extracting proper parameters, and handling tool outputs gracefully.</p>
<h2>Key Features</h2>
<p><strong>Long Context:</strong> 200K tokens for extensive document processing<br>
<strong>Artifacts:</strong> Claude can generate and edit code/artifacts<br>
<strong>Strong Reasoning:</strong> Excellent for complex decision-making<br>
<strong>Reduced Hallucination:</strong> More factual than many alternatives</p>
<h2>Getting Started</h2>
<p>Get API key from console.anthropic.com. Install with <code>pip install anthropic</code>. Define tools in Anthropic's format, pass to messages API, and handle tool_use blocks.</p>
</section>""",
            "faqs": [
                {
                    "@type": "Question",
                    "name": "How does Claude tool use differ from OpenAI?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Claude's tool use is very similar but uses a different API structure. Instead of a separate functions parameter, tools are defined separately and the model returns tool_use content blocks. Both are highly capable - choose based on which model you prefer.",
                    },
                },
            ],
        },
    ]

    for config in tutorial_configs:
        tutorial_agents = [a for a in agents if config["filter"](a)]
        if tutorial_agents:
            tutorial_dir = output_dir / "how-to" / config["key"]
            _write(
                tutorial_dir / "index.html",
                _render_tutorial_page(
                    config["key"],
                    config["title"],
                    config["description"],
                    tutorial_agents[:30],
                    base_url=base_url,
                    tutorial_content=config["content"],
                    faq_data=config["faqs"],
                    difficulty=config["difficulty"],
                ),
            )
            additional_sitemap_urls.append(f"{site_url}/how-to/{config['key']}/")

    # Generate sitemap with all pages
    if base_url:
        _render_sitemap(
            output_dir,
            agents,
            [(c[0], c[1], [a for a in agents if c[2](a)]) for c in categories],
            base_url,
            additional_urls=additional_sitemap_urls,
        )


def main() -> int:
    """CLI entry point for static site export.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = argparse.ArgumentParser(description="Export a static site from data/agents.json")
    parser.add_argument("--data", type=Path, default=Path("data/agents.json"), help="Path to agents.json")
    parser.add_argument("--output", type=Path, default=Path("site"), help="Output directory")
    parser.add_argument("--base-url", default=os.environ.get("SITE_BASE_URL", ""), help="Public base URL for sitemap/canonical links")
    args = parser.parse_args()

    if not args.data.exists():
        logger.error(f"Missing data file: {args.data}")
        return 1

    base_url = args.base_url.strip() or None
    export_site(args.data, args.output, base_url=base_url)
    logger.info(f"Static site exported to: {args.output}")
    if base_url:
        logger.info(f"Sitemap: {args.output / 'sitemap.xml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
