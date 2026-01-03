"""
“Best X Agents” pSEO pages.
"""

from __future__ import annotations

from pathlib import Path

from src.export._utils import _write
from src.export.data import BEST_OF_PAGES
from src.export.pages._shared import filter_agents, sort_agents
from src.export.templates import _render_category_landing


def generate_best_of_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    for slug, cfg in BEST_OF_PAGES.items():
        matched = filter_agents(agents, cfg["criteria"])
        matched = sort_agents(matched, sort_by=cfg.get("sort_by") or "stars")

        intro = """<section class="about">
<h2>How we pick “best”</h2>
<p>These pages are a curated, data-driven starting point. We generally prioritize runnable examples with clear READMEs and higher repo engagement (e.g., stars), then sort by name as a tie-breaker.</p>
<p>Always click through to confirm prerequisites (API keys, vector DBs, etc.).</p>
</section>"""

        _write(
            output_dir / slug / "index.html",
            _render_category_landing(
                slug,
                cfg["title"],
                matched,
                base_url=base_url,
                description=cfg["description"],
                heading=cfg["title"],
                intro_content=intro,
                related_links=[("All Agents", "/"), ("Tutorials", "/how-to/")],
            ),
        )
        additional_urls.append(f"{site_url}/{slug}/")
