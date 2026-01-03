"""
Main export orchestration for static site generation.
"""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path

from src.exceptions import DataStoreError, ExportError
from src.export._utils import _normalize_record, _read_json, _slug, _write
from src.export.data import (
    CATEGORY_PAGES,
    COMPARISON_CONFIGS,
    COMPLEXITY_PAGES,
    FRAMEWORK_PAGES,
    PROVIDER_PAGES,
    TUTORIAL_CONFIGS,
)
from src.export.pages import (
    generate_best_of_pages,
    generate_pattern_pages,
    generate_tech_combo_pages,
    generate_use_case_pages,
)
from src.export.pages.pseo_strategic import (
    generate_all_pseo_pages,
)
from src.export.templates import (
    _render_404,
    _render_agent,
    _render_assets,
    _render_category_landing,
    _render_comparison_index,
    _render_comparison_page,
    _render_headers,
    _render_index,
    _render_sitemap,
    _render_tutorial_index,
    _render_tutorial_page,
)

logger = logging.getLogger(__name__)


def export_site(data_path: Path, output_dir: Path, *, base_url: str | None) -> None:
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
    agents = [_normalize_record(a) for a in _read_json(data_path)]
    agents.sort(key=lambda a: ((a.get("name") or "").lower()))

    # Normalize export IDs to URL-safe slugs and ensure uniqueness.
    #
    # Static export URLs are path-based (`/agents/{id}/`), so IDs must be URL-safe.
    # Keep the original ID for debugging, but render using the slug.
    seen_ids: set[str] = set()
    for a in agents:
        raw_id = str(a.get("id") or "").strip()
        slug_id = _slug(raw_id, max_length=80)
        base = slug_id
        suffix = 2
        while slug_id in seen_ids:
            slug_id = f"{base}-{suffix}"
            suffix += 1
        seen_ids.add(slug_id)
        a["source_id"] = raw_id
        a["id"] = slug_id

    site_url = (base_url or "https://agent-navigator.com").rstrip("/")

    _render_assets(output_dir)
    _write(output_dir / "404.html", _render_404(base_url))
    _write(output_dir / "_headers", _render_headers())
    _write(output_dir / "index.html", _render_index(agents, base_url))

    # Generate individual agent pages
    for a in agents:
        agent_id = a.get("id") or ""
        if not isinstance(agent_id, str) or not agent_id.strip():
            continue
        agent_dir = output_dir / "agents" / agent_id
        _write(agent_dir / "index.html", _render_agent(a, base_url, all_agents=agents))

    # Track all additional URLs for sitemap
    additional_sitemap_urls: list[str] = []

    # Generate pSEO category landing pages (original 4)
    for cat_key, cat_name, filter_fn, heading, description in CATEGORY_PAGES:
        cat_agents = [a for a in agents if filter_fn(a)]
        cat_dir = output_dir / cat_key
        _write(
            cat_dir / "index.html",
            _render_category_landing(
                cat_key, cat_name, cat_agents, base_url=base_url, description=description, heading=heading
            ),
        )
        additional_sitemap_urls.append(f"{site_url}/{cat_key}/")

    # Framework-specific pages
    for fw_key, fw_name, filter_fn, heading, description, intro_content in FRAMEWORK_PAGES:
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
    for prov_key, prov_name, filter_fn, heading, description, intro_content in PROVIDER_PAGES:
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
    for comp_key, comp_name, filter_fn, heading, description, difficulty in COMPLEXITY_PAGES:
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

    for config in COMPARISON_CONFIGS:
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

    for config in TUTORIAL_CONFIGS:
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

    # Additional pSEO pages (patterns, best-of, use-cases, tech-combos)
    generate_pattern_pages(
        agents,
        output_dir,
        base_url=base_url,
        site_url=site_url,
        additional_urls=additional_sitemap_urls,
    )
    generate_best_of_pages(
        agents,
        output_dir,
        base_url=base_url,
        site_url=site_url,
        additional_urls=additional_sitemap_urls,
    )
    generate_use_case_pages(
        agents,
        output_dir,
        base_url=base_url,
        site_url=site_url,
        additional_urls=additional_sitemap_urls,
    )
    generate_tech_combo_pages(
        agents,
        output_dir,
        base_url=base_url,
        site_url=site_url,
        additional_urls=additional_sitemap_urls,
    )

    # Strategic pSEO pages (20+ pages for frameworks, categories, comparisons, difficulty)
    generate_all_pseo_pages(
        agents,
        output_dir,
        base_url=base_url,
        site_url=site_url,
        additional_urls=additional_sitemap_urls,
    )

    # Generate sitemap with all pages
    if base_url:
        _render_sitemap(
            output_dir,
            agents,
            [(c[0], c[1], [a for a in agents if c[2](a)]) for c in CATEGORY_PAGES],
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
    parser.add_argument(
        "--base-url", default=os.environ.get("SITE_BASE_URL", ""), help="Public base URL for sitemap/canonical links"
    )
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
