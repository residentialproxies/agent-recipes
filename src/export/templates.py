"""
HTML template rendering functions.
"""

from __future__ import annotations

import html
import json
import re
from contextlib import suppress
from datetime import datetime

from src.export._utils import (
    _category_icon,
    _iso_date,
    get_agent_lastmod,
    get_related_category_links,
    get_sitemap_changefreq,
    get_sitemap_priority,
)
from src.export.data import _find_related_agents
from src.export.schema import (
    _generate_breadcrumb_schema,
    _generate_collection_page_schema,
    _generate_faq_schema,
    _generate_organization_schema,
    _generate_schema_org,
    _generate_webpage_schema,
)
from src.export.seo import (
    _generate_keywords_meta_tag,
    _generate_meta_description,
    _generate_open_graph_tags,
    _generate_page_title,
)


def _minify_css(css: str) -> str:
    """Minify CSS by removing comments, extra whitespace, and unnecessary semicolons.

    Args:
        css: Raw CSS content.

    Returns:
        Minified CSS string.
    """
    # Remove comments
    css = re.sub(r"/\*[^*]*\*+(?:[^/*][^*]*\*+)*/", "", css)
    # Remove whitespace around special characters
    css = re.sub(r"\s*([{}:;,>+~])\s*", r"\1", css)
    # Remove trailing semicolons
    css = re.sub(r";}", "}", css)
    # Collapse multiple spaces into one
    css = re.sub(r"\s+", " ", css)
    # Strip leading/trailing whitespace
    return css.strip()


def _layout(
    title: str,
    description: str,
    body: str,
    *,
    canonical: str | None = None,
    asset_prefix: str = "/",
    schema_json: str | None = None,
    og_tags: str | None = None,
    keywords_tag: str | None = None,
    preload_css: bool = False,
) -> str:
    """Generate the base HTML layout for all pages."""
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

    # Keywords meta tag
    keywords_section = ""
    if keywords_tag:
        keywords_section = f"\n    {keywords_tag}"

    # Resource preload hints for critical CSS/JS
    preload_hints = ""
    if preload_css:
        # Preload critical CSS for faster rendering
        preload_hints = f'\n    <link rel="preload" href="{prefix}assets/style.css" as="style" />'
    # Preload JavaScript for non-blocking execution
    preload_hints += f'\n    <link rel="modulepreload" href="{prefix}assets/app.js" />'

    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title_e}</title>
    <meta name="description" content="{desc_e}" />
    {canonical_tag}{keywords_section}{og_section}{preload_hints}{schema_tag}
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


def _render_index(agents: list[dict], base_url: str | None = None) -> str:
    """Render the homepage with agent listing."""
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
        # Generate description if empty
        agent_desc = a.get("description") or _generate_meta_description(a)
        desc = html.escape(agent_desc[:150])
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

    # Normalize base_url: treat empty string the same as None
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")

    # SEO elements
    description = f"Search and browse {total} runnable LLM agent/app examples with tutorials, code, and setup instructions. RAG, chatbots, multi-agent systems, and more."

    # Only generate OG tags and schema if base_url is provided
    og_tags = None
    combined_schema = ""

    if _base_url:
        og_tags = _generate_open_graph_tags(
            title="Agent Navigator - LLM Agent Examples & Tutorials",
            description=description,
            url=site_url,
            image=f"{site_url}/assets/og-image.png",
        )

        # Schema.org for homepage - combine WebSite and Organization schemas
        website_schema = {
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

        # Add Organization schema
        organization_schema = json.loads(
            _generate_organization_schema(
                name="Agent Navigator",
                url=site_url,
                description=description,
            )
        )

        # Combine schemas
        combined_schema = json.dumps([website_schema, organization_schema], indent=2)

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
        canonical=site_url + "/" if _base_url else None,
        asset_prefix="./",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_agent(agent: dict, base_url: str | None = None, all_agents: list[dict] | None = None) -> str:
    """Render an individual agent detail page."""
    icon = _category_icon(agent["category"])
    name = html.escape(agent["name"])
    # Use generated description if agent description is empty
    agent_desc = agent.get("description") or ""
    if not agent_desc:
        agent_desc = _generate_meta_description(agent)
    desc = html.escape(agent_desc)
    category = html.escape(agent.get("category") or "other").replace("_", " ")
    category_raw = agent.get("category") or "other"
    complexity = html.escape(agent.get("complexity") or "intermediate")
    updated = _iso_date(agent.get("updated_at"))
    frameworks = ", ".join(html.escape(x) for x in (agent.get("frameworks") or [])[:6]) or "—"
    providers = ", ".join(html.escape(x) for x in (agent.get("llm_providers") or [])[:6]) or "—"
    api_keys = ", ".join(html.escape(x) for x in (agent.get("api_keys") or [])[:10]) or "—"

    # Generate SEO-optimized title
    page_title = _generate_page_title(agent)

    links = []
    if agent.get("github_url"):
        links.append(
            f'<a class="btn" href="{html.escape(agent["github_url"])}" target="_blank" rel="noreferrer">GitHub</a>'
        )
    if agent.get("codespaces_url"):
        links.append(
            f'<a class="btn" href="{html.escape(agent["codespaces_url"])}" target="_blank" rel="noreferrer">Codespaces</a>'
        )
    if agent.get("colab_url"):
        links.append(
            f'<a class="btn" href="{html.escape(agent["colab_url"])}" target="_blank" rel="noreferrer">Colab</a>'
        )
    link_html = " ".join(links) or ""

    stars = agent.get("stars")
    stars_html = f"<div><b>Repo stars:</b> {stars:,}</div>" if isinstance(stars, int) else ""
    updated_html = f"<div><b>Updated:</b> {html.escape(updated)}</div>" if updated else ""

    qs = html.escape((agent.get("quick_start") or "").strip())[:1200]
    clone = html.escape((agent.get("clone_command") or "").strip())[:400]

    # Normalize base_url: treat empty string the same as None
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    agent_url = f"{site_url}/agents/{agent['id']}/"
    canonical = agent_url if _base_url else None

    # Generate SEO elements
    meta_desc = _generate_meta_description(agent)
    schema = _generate_schema_org(agent, site_url)

    # Generate keywords meta tag
    keywords_tag = _generate_keywords_meta_tag(agent)

    # Get published time for article-type OG tags
    published_time = None
    if agent.get("added_at") and isinstance(agent["added_at"], int) and agent["added_at"] > 0:
        with suppress(OSError, ValueError):
            published_time = datetime.fromtimestamp(agent["added_at"]).strftime("%Y-%m-%dT%H:%M:%S%z")

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
        og_tags = _generate_open_graph_tags(
            title=f"{agent['name']} - Agent Navigator",
            description=meta_desc,
            url=agent_url,
            image=f"{site_url}/assets/og-agent-{agent['id']}.png",
            og_type="article",
            published_time=published_time,
        )

    # Generate breadcrumb schema only if base_url is provided
    breadcrumbs = [
        ("Home", "/"),
        ("Agents", "/#browse"),
        (agent["name"], f"/agents/{agent['id']}/"),
    ]
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if _base_url else ""

    # Generate WebPage schema with published_time
    webpage_schema = _generate_webpage_schema(agent, site_url, published_time)

    # Combine schemas
    schema_list = [json.loads(schema)]
    if breadcrumb_schema:
        schema_list.append(json.loads(breadcrumb_schema))
    schema_list.append(json.loads(webpage_schema))
    combined_schema = json.dumps(schema_list, indent=2) if _base_url else ""

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
                related_cards.append(f"""
<a class="card related-card" href="{r_href}">
  <div class="card-title">{r_icon} {r_name}</div>
  <div class="card-desc">{r_desc}</div>
</a>""")
            related_html = f"""
<section class="related-section">
  <h3>Related Agents</h3>
  <div class="related-grid">
    {''.join(related_cards)}
  </div>
</section>
"""

    # Generate internal links for SEO (related categories)
    internal_links_html = ""
    if category_raw and category_raw != "other":
        internal_links = get_related_category_links(agent)
        if internal_links:
            link_items = []
            for link_text, link_url in internal_links[:5]:
                link_items.append(
                    f'<a href="{html.escape(link_url)}" class="category-link">{html.escape(link_text)}</a>'
                )
            internal_links_html = f"""
<div class="panel" style="margin-top: 1rem;">
  <h4>Explore More</h4>
  <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
    {''.join(f"<span>{item}</span>" for item in link_items)}
  </div>
</div>
"""

    # Breadcrumb HTML navigation with rich anchors
    category_breadcrumb = (
        f'<li><a href="/#{html.escape(category_raw)}">{html.escape(category_raw.replace("_", " ").title())}</a></li>'
        if category_raw != "other"
        else ""
    )
    breadcrumb_nav = f"""
<nav class="breadcrumb" aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    {category_breadcrumb}
    <li><a href="/#browse">Agents</a></li>
    <li aria-current="page">{name}</li>
  </ol>
</nav>
"""

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
    {internal_links_html}
  </div>
  <div class="panel">
    <h3>Details</h3>
    <div><b>Category:</b> <a href="/#{html.escape(category_raw)}" class="category-link">{category}</a></div>
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
        page_title,
        meta_desc,
        body,
        canonical=canonical,
        asset_prefix="../../",
        schema_json=combined_schema,
        og_tags=og_tags,
        keywords_tag=keywords_tag,
        preload_css=True,
    )


def _render_category_landing(
    category_key: str,
    category_name: str,
    agents: list[dict],
    *,
    base_url: str | None,
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
        # Generate description if empty
        agent_desc = a.get("description") or _generate_meta_description(a)
        desc = html.escape(agent_desc[:150])
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
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    category_url = f"{site_url}/{category_key}/"

    meta_desc = f"{description} Browse {count} examples with code, tutorials, and setup instructions."

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
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
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if _base_url else ""

    # Generate CollectionPage schema for category pages
    collection_page_schema = _generate_collection_page_schema(
        category_name=heading,
        category_url=category_url,
        agents=agents,
        description=meta_desc,
    )

    # Combine schemas - FAQPage, CollectionPage, and BreadcrumbList
    faq_schema_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faqs,
    }
    schema_list = [faq_schema_obj]
    if _base_url:
        schema_list.append(json.loads(collection_page_schema))
    if breadcrumb_schema:
        schema_list.append(json.loads(breadcrumb_schema))
    combined_schema = json.dumps(schema_list, indent=2) if _base_url else ""

    # Build related links section
    related_html = ""
    if related_links:
        links_html = "".join(
            f'<a class="chip" href="{html.escape(href)}">{html.escape(text)}</a>' for text, href in related_links
        )
        related_html = f'<section><h2>Related Topics</h2><div class="chips">{links_html}</div></section>'

    # Build FAQ HTML
    faq_html = ""
    if faqs:
        faq_items = ""
        for faq in faqs:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f"""
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>"""
        faq_html = f"""
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>"""

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
        canonical=category_url if _base_url else None,
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
    base_url: str | None,
    comparison_content: str,
    faq_data: list[dict],
) -> str:
    """Render a pSEO comparison page between two frameworks/providers."""
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    comparison_url = f"{site_url}/compare/{comparison_key}/"

    left_count = len(left_agents)
    right_count = len(right_agents)

    meta_desc = f"{description} Compare examples, features, and use cases. {left_count} {left_option} examples vs {right_count} {right_option} examples."

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
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
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if _base_url else ""

    # FAQ Schema
    faq_schema_obj = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_data,
    }
    combined_schema = json.dumps(faq_schema_obj, indent=2) if _base_url else ""
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
            faq_items += f"""
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>"""
        faq_html = f"""
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>"""

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
        canonical=comparison_url if _base_url else None,
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
    base_url: str | None,
    tutorial_content: str,
    faq_data: list[dict],
    difficulty: str = "Intermediate",
) -> str:
    """Render a pSEO how-to/tutorial page."""
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    tutorial_url = f"{site_url}/how-to/{tutorial_key}/"

    count = len(agents)

    meta_desc = f"{description} Step-by-step guide with {count} working examples and code samples."

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
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
    breadcrumb_schema = _generate_breadcrumb_schema(breadcrumbs, site_url) if _base_url else ""

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
    combined_schema = json.dumps(schema_list, indent=2) if _base_url else ""

    # Build FAQ HTML
    faq_html = ""
    if faq_data:
        faq_items = ""
        for faq in faq_data:
            question = html.escape(faq.get("name", ""))
            answer = html.escape(faq.get("acceptedAnswer", {}).get("text", ""))
            faq_items += f"""
    <details><summary>{question}</summary>
      <p>{answer}</p>
    </details>"""
        faq_html = f"""
<section class="about">
  <h2>Frequently Asked Questions</h2>
  <div class="faq-container">{faq_items}
  </div>
</section>"""

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
        canonical=tutorial_url if _base_url else None,
        asset_prefix="../../",
        schema_json=combined_schema,
        og_tags=og_tags,
    )


def _render_comparison_index(*, base_url: str | None) -> str:
    """Render the comparison index page."""
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    index_url = f"{site_url}/compare/"

    meta_desc = "Compare AI agent frameworks, LLM providers, and tools. Side-by-side comparisons of LangChain vs LlamaIndex, CrewAI vs AutoGen, OpenAI vs Anthropic, and more."

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
        og_tags = _generate_open_graph_tags(
            title="Framework & Provider Comparisons - Agent Navigator",
            description=meta_desc,
            url=index_url,
            image=f"{site_url}/assets/og-compare.png",
        )

    comparisons = [
        ("LangChain vs LlamaIndex", "/langchain-vs-llamaindex/", "Compare two leading RAG and agent frameworks"),
        ("CrewAI vs AutoGen", "/crewai-vs-autogen/", "Multi-agent framework comparison"),
        ("OpenAI vs Anthropic", "/openai-vs-anthropic/", "Leading LLM API providers"),
        ("LangChain vs Raw API", "/compare/langchain-vs-raw-api/", "Framework vs direct API calls"),
        ("Google vs OpenAI", "/compare/google-vs-openai/", "Gemini vs GPT comparison"),
        ("Local vs Cloud LLMs", "/local-vs-cloud-llm/", "Privacy and cost comparison"),
        ("RAG vs Vector Search", "/rag-vs-vector-search/", "Retrieval strategies comparison"),
        ("Sync vs Async Agents", "/sync-vs-async-agents/", "Execution patterns comparison"),
    ]

    cards = "".join(
        f"""
<a class="card" href="{path}">
  <div class="card-title">📊 {title}</div>
  <div class="card-desc">{desc}</div>
</a>"""
        for title, path, desc in comparisons
    )

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
        canonical=index_url if _base_url else None,
        asset_prefix="../",
        og_tags=og_tags,
    )


def _render_tutorial_index(*, base_url: str | None) -> str:
    """Render the tutorials index page."""
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")
    index_url = f"{site_url}/how-to/"

    meta_desc = "Step-by-step tutorials for building AI agents. Learn RAG chatbots, multi-agent systems, local LLM deployment, and more with working code examples."

    # Only generate OG tags if base_url is provided
    og_tags = None
    if _base_url:
        og_tags = _generate_open_graph_tags(
            title="AI Agent Tutorials - Agent Navigator",
            description=meta_desc,
            url=index_url,
            image=f"{site_url}/assets/og-howto.png",
        )

    tutorials = [
        (
            "Build RAG Chatbot",
            "/rag-tutorials/",
            "Beginner",
            "Create a retrieval augmented generation chatbot with vector database",
        ),
        (
            "Multi-Agent System",
            "/multi-agent-systems/",
            "Intermediate",
            "Build multi-agent systems with CrewAI and LangChain",
        ),
        (
            "Local LLM with Ollama",
            "/local-llm-agents/",
            "Beginner",
            "Run LLM agents locally with Ollama for privacy",
        ),
        (
            "OpenAI Function Calling",
            "how-to/openai-function-calling/",
            "Intermediate",
            "Implement function calling with OpenAI API",
        ),
        ("LangChain Agents", "/langchain-agents/", "Intermediate", "Build agents using LangChain framework"),
        (
            "Anthropic Claude Agents",
            "how-to/anthropic-claude-agents/",
            "Intermediate",
            "Create agents with Anthropic's Claude API",
        ),
        ("CrewAI Tutorials", "/crewai-tutorials/", "Intermediate", "Multi-agent systems with CrewAI"),
        ("LlamaIndex Examples", "/llamaindex-examples/", "Intermediate", "RAG applications with LlamaIndex"),
        ("Beginner AI Projects", "/beginner-ai-projects/", "Beginner", "Start your AI journey"),
        ("Advanced Agent Patterns", "/advanced-agent-patterns/", "Advanced", "Master complex architectures"),
    ]

    cards = "".join(
        f"""
<a class="card" href="{path}">
  <div class="card-title">📖 {title}</div>
  <div class="card-desc">{desc}</div>
  <div class="card-badges"><span class="badge">{difficulty}</span></div>
</a>"""
        for title, path, difficulty, desc in tutorials
    )

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
        canonical=index_url if _base_url else None,
        asset_prefix="../",
        og_tags=og_tags,
    )


def _render_assets(out) -> None:
    """Render static assets (CSS and JS files) with CSS minification."""
    from src.export._utils import _write

    # Raw CSS content
    raw_css = """
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
.breadcrumb li:not(:last-child)::after { content: ">"; margin-left: 0.5rem; color: var(--muted); }
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

    # Apply CSS minification
    minified_css = _minify_css(raw_css)

    _write(out / "assets/style.css", minified_css + "\n")

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


def _render_404(base_url: str | None) -> str:
    """Render a simple 404 page for static hosting (e.g., Cloudflare Pages)."""
    _base_url = base_url if base_url and base_url.strip() else None
    site_url = (_base_url or "https://agent-navigator.com").rstrip("/")

    body = """
<section class="hero">
  <h1>Page not found</h1>
  <p class="lead">That URL doesn't exist. Try browsing or searching the directory.</p>
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
    canonical = f"{site_url}/404.html" if _base_url else None
    return _layout(
        title="404 — Agent Navigator",
        description="Page not found.",
        body=body,
        canonical=canonical,
    )


def _render_headers() -> str:
    """
    Generate a Cloudflare Pages-compatible `_headers` file with enhanced security headers.

    Includes:
    - Cache-Control for assets and HTML
    - X-Content-Type-Options to prevent MIME sniffing
    - X-Frame-Options to prevent clickjacking
    - Referrer-Policy for privacy
    - Permissions-Policy to disable unnecessary features
    - Strict-Transport-Security for HTTPS enforcement
    """
    return """
/assets/*
  Cache-Control: public, max-age=31536000, immutable

/*
  Cache-Control: public, max-age=600
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: interest-cohort=(), camera=(), microphone=(), geolocation=()
  Strict-Transport-Security: max-age=31536000; includeSubDomains
""".lstrip()


def _render_sitemap(
    out,
    agents: list[dict],
    categories: list[tuple[str, str, list]] = None,
    base_url: str = None,
    additional_urls: list[str] = None,
) -> None:
    """Generate sitemap.xml and robots.txt files with enhanced SEO (priority, changefreq, lastmod)."""
    import html
    from datetime import datetime

    from src.export._utils import _write

    if categories is None:
        categories = []
    if additional_urls is None:
        additional_urls = []
    base_url = base_url.rstrip("/")

    # Build sitemap items with priority, changefreq, and lastmod
    items = []

    # Homepage - highest priority
    items.append(f"""  <url>
    <loc>{html.escape(base_url)}/</loc>
    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>""")

    # Agent pages with priority based on stars and changefreq based on complexity/age
    for agent in agents:
        agent_url = f"{base_url}/agents/{agent['id']}/"
        lastmod = get_agent_lastmod(agent)
        priority = get_sitemap_priority(agent)
        changefreq = get_sitemap_changefreq(agent, page_type="agent")

        item = f"""  <url>
    <loc>{html.escape(agent_url)}</loc>"""
        if lastmod:
            item += f"\n    <lastmod>{lastmod}</lastmod>"
        item += f"""
    <changefreq>{changefreq}</changefreq>
    <priority>{priority:.1f}</priority>
  </url>"""
        items.append(item)

    # Category pages with priority based on agent count
    for key, _name, cat_agents in categories:
        cat_url = f"{base_url}/{key}/"
        count = len(cat_agents)
        # Priority based on number of agents (more agents = higher priority)
        cat_priority = min(0.9, 0.5 + (count / 100))
        items.append(f"""  <url>
    <loc>{html.escape(cat_url)}</loc>
    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{cat_priority:.1f}</priority>
  </url>""")

    # Additional URLs with default priority
    for url in additional_urls:
        items.append(f"""  <url>
    <loc>{html.escape(url)}</loc>
    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>""")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(items)}
</urlset>
"""
    _write(out / "sitemap.xml", sitemap_content)
    _write(out / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")
