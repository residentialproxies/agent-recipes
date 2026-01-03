"""
Design pattern pSEO pages.
"""

from __future__ import annotations

from pathlib import Path

from src.export._utils import _write
from src.export.data import DESIGN_PATTERNS
from src.export.pages._shared import filter_agents, sort_agents
from src.export.templates import _render_category_landing


def generate_pattern_pages(
    agents: list[dict],
    output_dir: Path,
    *,
    base_url: str | None,
    site_url: str,
    additional_urls: list[str],
) -> None:
    for slug, cfg in DESIGN_PATTERNS.items():
        matched = filter_agents(agents, cfg["criteria"])
        matched = sort_agents(matched, sort_by="stars")
        intro = f"""<section class="about">
<h2>What is this pattern?</h2>
<p>{cfg["description"]}</p>
<p>Browse runnable examples below. Each entry links to the source repository with setup instructions.</p>
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
                related_links=[("All Agents", "/"), ("Tutorials", "/how-to/"), ("Comparisons", "/compare/")],
            ),
        )
        additional_urls.append(f"{site_url}/{slug}/")
